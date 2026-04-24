"""This file defines the API used to interact with GalTransl"""

import importlib.util
import sys
import os
import shutil
import subprocess
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from logging import getLogger
import yaml
from project import Project
from textfile import TextFile
from block import Block
from config import Config, CONFIG
from constants import SuccessStatus as success
from .translator import Translator

logger = getLogger(__name__)


def build_galtransl_settings_bridge(config: Config):
    """Build the shared runtime->GalTransl settings mapping."""
    proxy_address = getattr(config, "proxy", None) or ""
    return {
        "project_config": {
            "proxy": {
                "enableProxy": bool(proxy_address),
                "address": proxy_address,
            },
            "openai_compatible": {
                "token": getattr(config, "token", ""),
                "endpoint": getattr(config, "endpoint", ""),
                "model_name": getattr(config, "model_name", ""),
            },
            "common": {
                "gpt.enhance_jailbreak": True,
                "gpt.prompt_content": "",
                "gpt.numPerRequestTranslate": getattr(config, "galtransl_num_per_request", 10),
            },
        },
        "worker": {
            "translation_method": getattr(config, "galtransl_translation_method", "ForGal-json"),
        },
    }


def write_galtransl_project_config(template_yaml_file: str, target_yaml_file: str, settings_bridge: dict):
    """Materialize the shared settings bridge into a GalTransl project config file."""
    shutil.copyfile(template_yaml_file, target_yaml_file)

    with open(target_yaml_file, "r", encoding="utf-8") as file:
        yaml_object = yaml.load(file, Loader=yaml.FullLoader)

    try:
        project_settings = settings_bridge["project_config"]
        proxy_settings = project_settings["proxy"]
        yaml_object["proxy"]["enableProxy"] = proxy_settings["enableProxy"]
        if proxy_settings["enableProxy"]:
            yaml_object["proxy"]["proxies"][0]["address"] = proxy_settings["address"]

        token_settings = project_settings["openai_compatible"]
        yaml_object["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["token"] = token_settings["token"]
        yaml_object["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["endpoint"] = token_settings["endpoint"]
        yaml_object["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["modelName"] = token_settings["model_name"]

        for key, value in project_settings["common"].items():
            yaml_object["common"][key] = value
    except Exception as e:
        logger.error(f"Error applying GalTransl settings: {e}")
        raise

    with open(target_yaml_file, "w", encoding="utf-8") as file:
        yaml.dump(yaml_object, file, default_flow_style=False, sort_keys=False, allow_unicode=True)


class GalTranslTranslator(Translator):
    """API to interact with GalTransl"""

    def __init__(self, config: Config = CONFIG):
        super().__init__(config)
        self._progress_callback = None

        # generate the roor path of GalTransl
        self.this_path = os.path.dirname(os.path.abspath(__file__))
        self.galtransl_path = os.path.join(self.this_path, "GalTransl")
        self.galtransl_code_path = os.path.join(self.galtransl_path, "GalTransl")
        # add the GalTransl path to the system path for importing GalTransl's variables
        sys.path.insert(0, self.galtransl_path)

        # Dynamically import modules from GalTransl
        self.GalTransl = self._import_galtransl_module("__init__")
        self.CONFIG_FILENAME = self._import_galtransl_module("__init__", "CONFIG_FILENAME")
        self.AUTHOR = self._import_galtransl_module("__init__", "AUTHOR")
        self.CONTRIBUTORS = self._import_galtransl_module("__init__", "CONTRIBUTORS")
        self.GALTRANSL_VERSION = self._import_galtransl_module("__init__", "GALTRANSL_VERSION")
        self.PROGRAM_SPLASH = self._import_galtransl_module("__init__", "PROGRAM_SPLASH")

        from GalTransl.__main__ import worker

        self.worker = worker

        if not self.worker:
            logger.error("Error: Worker function not found!")

    def set_progress_callback(self, callback):
        """Set callback used to emit translation progress updates."""
        self._progress_callback = callback

    def _report_progress(self, **payload):
        """Emit progress payload to app-level progress tracker."""
        if not callable(self._progress_callback):
            return
        try:
            self._progress_callback(payload)
        except Exception as e:
            logger.warning(f"Failed to report GalTransl progress: {e}")

    @staticmethod
    def _iter_json_files(folder_path):
        """Yield all json files under a folder recursively."""
        folder = Path(folder_path)
        if not folder.is_dir():
            return []
        return [path for path in folder.rglob("*.json") if path.is_file()]

    @staticmethod
    def _clear_json_files(folder_path):
        """Delete stale json files so progress reflects current run only."""
        for file_path in GalTranslTranslator._iter_json_files(folder_path):
            os.remove(file_path)

    @staticmethod
    def _collect_output_progress(output_folder, total_count):
        """Return completed file count and latest file name in gt_output."""
        output_root = Path(output_folder)
        if not output_root.is_dir():
            return 0, ""

        output_files = []
        for file_path in GalTranslTranslator._iter_json_files(output_root):
            output_files.append((os.path.getmtime(file_path), file_path))

        output_files.sort(key=lambda item: item[0])
        completed = len(output_files)
        if total_count > 0:
            completed = min(completed, total_count)
        latest_file = str(output_files[-1][1].relative_to(output_root)) if output_files else ""
        return completed, latest_file

    def _import_galtransl_module(self, module_name, attribute_name=None):
        """Dynamically import a module or an attribute from GalTransl"""
        try:
            module_path = os.path.join(self.galtransl_code_path, module_name + ".py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            if attribute_name:
                return getattr(module, attribute_name)
            return module
        except Exception as e:
            logger.error(f"Failed to import {module_name}.{attribute_name}: {e}")
            return None

    @staticmethod
    def _resolve_text_context(text_file_path):
        """Return project root, text root, and relative path for a text file under Text/."""
        text_path = Path(text_file_path)
        for parent in text_path.parents:
            if parent.name.lower() != "text":
                continue
            return parent.parent, parent, text_path.relative_to(parent)
        raise ValueError(f"Unable to locate project Text directory for {text_file_path}")

    @classmethod
    def _resolve_individual_workspace(cls, text_file_path):
        """Return the single-file GalTransl workspace path."""
        project_root, _, relative_path = cls._resolve_text_context(text_file_path)
        return project_root / "GalTransl" / "individual" / relative_path

    @classmethod
    def _resolve_project_json_path(cls, text_file_path, json_root):
        """Return the project translation json path preserving the Text-relative path."""
        _, _, relative_path = cls._resolve_text_context(text_file_path)
        return Path(json_root) / Path(str(relative_path) + ".json")

    def _template_config_path(self):
        """Return the bundled GalTransl sample config template path."""
        return os.path.join(self.this_path, "GalTransl/sampleProject/config.inc.yaml")

    def _prepare_workspace(self, workspace_path, clear_json=False):
        """Create a GalTransl workspace and return key paths plus worker settings."""
        workspace_path = Path(workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)

        settings_bridge = build_galtransl_settings_bridge(self.config)
        config_path = workspace_path / self.CONFIG_FILENAME
        write_galtransl_project_config(self._template_config_path(), config_path, settings_bridge)

        gt_input_folder = workspace_path / "gt_input"
        gt_output_folder = workspace_path / "gt_output"
        gt_input_folder.mkdir(exist_ok=True)
        gt_output_folder.mkdir(exist_ok=True)
        if clear_json:
            self._clear_json_files(gt_input_folder)
            self._clear_json_files(gt_output_folder)

        return {
            "workspace_path": workspace_path,
            "config_path": config_path,
            "gt_input_folder": gt_input_folder,
            "gt_output_folder": gt_output_folder,
            "worker_settings": settings_bridge["worker"],
        }

    @staticmethod
    def _read_name_table(namelist_file_path):
        """Read a GalTransl name table, skipping the header row."""
        with open(namelist_file_path, "r", encoding="utf-8") as file:
            return file.readlines()[1:]

    @staticmethod
    def _apply_name_table(namelist_file_path, original_names, translated_names):
        """Sync translated names from the GalTransl name table back into memory."""
        for line in GalTranslTranslator._read_name_table(namelist_file_path):
            row = line.strip()
            if not row:
                continue
            parts = row.split(",")
            if len(parts) != 3:
                logger.warning("Warning: malformed row in %s: %s", namelist_file_path, row)
                continue
            jp_name, cn_name, _ = parts
            if jp_name in original_names:
                index = original_names.index(jp_name)
                translated_names[index] = cn_name
            else:
                logger.warning(f"Warning: {jp_name} not found in the original name list")

    @staticmethod
    def _write_name_table(namelist_file_path, original_names, translated_names, name_counts):
        """Write the in-memory name table to disk and report whether any names are empty."""
        lines = ["JP_Name,CN_Name,Count\n"]
        has_empty_translation = False
        for index, name in enumerate(original_names):
            translated_name = translated_names[index]
            if translated_name == "":
                has_empty_translation = True
            lines.append(f"{name},{translated_name},{name_counts[index]}\n")

        with open(namelist_file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)
        return has_empty_translation

    @staticmethod
    def _prompt_fill_name_table(workspace_path):
        """Ask the user to fill the GalTransl name table when values are missing."""
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.after(100, lambda: root.lift())
        messagebox.showinfo(
            "人名替换表为空",
            f"请按照GalTransl要求填写 人名替换表.csv 以达到更好的翻译效果，文件在 {workspace_path}",
        )
        root.destroy()

    def _sync_name_table(self, workspace_path, original_names, translated_names, name_counts, reuse_existing=True):
        """Load or initialize the GalTransl name table and sync the chosen values back."""
        namelist_file_path = Path(workspace_path) / "人名替换表.csv"
        should_create = not (reuse_existing and namelist_file_path.exists())
        if should_create:
            has_empty_translation = self._write_name_table(
                namelist_file_path,
                original_names,
                translated_names,
                name_counts,
            )
            if has_empty_translation:
                self._prompt_fill_name_table(workspace_path)

        self._apply_name_table(namelist_file_path, original_names, translated_names)
        return namelist_file_path

    def translate_file_whole(self, text_file: TextFile) -> success:
        """This function will create an environment for GalTransl to translate the text file"""
        text_file_path = Path(text_file.text_file_path)
        text_file_name = text_file_path.name
        workspace = self._prepare_workspace(self._resolve_individual_workspace(text_file.text_file_path))
        target_folder_path = workspace["workspace_path"]
        gt_input_folder = workspace["gt_input_folder"]
        gt_output_folder = workspace["gt_output_folder"]
        output_file_name = gt_output_folder / f"{text_file_name}.json"

        # create the json file in the gt_input folder under the project directory
        target_json_file_path = gt_input_folder / f"{text_file_name}.json"
        text_file.generate_galtransl_json(dest=str(target_json_file_path), replace=True)

        self._sync_name_table(
            target_folder_path,
            text_file.name_list_original,
            text_file.name_list_translated,
            text_file.name_list_count,
        )

        # call GalTransl
        self.run_worker(target_folder_path, workspace["worker_settings"], total_count=1)

        # read the translation results (sync to textfile instance)
        if os.path.exists(output_file_name):
            text_file.update_from_galtransl_json(str(output_file_name))
            # write the translated text to the text file
            text_file.generate_textfile(text_file.text_file_path, replace=True)
            return success.SUCCESS
        else:
            return success.ERROR

    def translate_block(self, block: Block, context: str = None):
        """Not implemented as GalTransl is intended for translating the whole project"""
        raise RuntimeError("Not implemented")

    def translate_project(self, project: Project):
        """translate the project using GalTransl"""
        project_path = Path(project.project_path)
        workspace = self._prepare_workspace(project_path / "GalTransl", clear_json=True)
        target_folder_path = workspace["workspace_path"]
        gt_input_folder = workspace["gt_input_folder"]
        gt_output_folder = workspace["gt_output_folder"]

        # create the json files in the gt_input folder under the project directory
        output_file_map = {}

        generated_json_count = 0
        for _, script_file in enumerate(project.game.script_file_list):
            for _, text_file in enumerate(script_file.textfiles):
                if text_file.is_empty:
                    continue
                input_json_path = self._resolve_project_json_path(text_file.text_file_path, gt_input_folder)
                output_json_path = self._resolve_project_json_path(text_file.text_file_path, gt_output_folder)
                input_json_path.parent.mkdir(parents=True, exist_ok=True)
                output_json_path.parent.mkdir(parents=True, exist_ok=True)
                text_file.generate_galtransl_json(dest=str(input_json_path), replace=True)
                output_file_map[output_json_path] = text_file
                generated_json_count += 1

        self._report_progress(
            phase="running",
            totalCount=generated_json_count,
            completedCount=0,
            currentFile="",
        )

        self._sync_name_table(
            target_folder_path,
            project.game.name_list_original,
            project.game.name_list_translated,
            project.game.name_list_count,
        )

        # call GalTransl
        self.run_worker(target_folder_path, workspace["worker_settings"], total_count=generated_json_count)

        self._report_progress(
            phase="applying_results",
            totalCount=generated_json_count,
            completedCount=generated_json_count,
            currentFile="",
        )

        # read the translation results (sync to textfiles instance)
        output_files = self._iter_json_files(gt_output_folder)
        logger.info("Reading the translation results of GalTransl")
        logger.info(f"{len(output_files)} files found")
        for output_file in output_files:
            output_file_path = Path(output_file)
            text_file = output_file_map.get(output_file_path)
            if text_file is None:
                logger.error(f"Error: {output_file_path} not found in the project")
                continue
            text_file.update_from_galtransl_json(str(output_file_path))
            # mark the file as translated, this will make the file appear as green in the GUI
            text_file.is_translated = True
            text_file.generate_textfile(text_file.text_file_path, replace=True)
            self._report_progress(
                phase="applying_results",
                totalCount=generated_json_count,
                completedCount=generated_json_count,
                currentFile=str(output_file_path.relative_to(gt_output_folder)),
            )

    def run_worker(self, project_path: str, worker_settings: dict, total_count=0):
        """run the worker function in a separate thread, wait for the worker to finish"""
        project_path = str(project_path)
        batch_file = os.path.join(self.galtransl_path, "run_GalTransl_zh.bat")
        arg1 = project_path
        arg2 = worker_settings["translation_method"]
        gt_output_folder = os.path.join(project_path, "gt_output")

        logger.info("Running GalTransl worker in a separate thread")
        try:
            # activate current environment and run the batch file
            activate_command = f"call {os.path.join(self.galtransl_path, '../../.venv', 'Scripts', 'activate.bat')}"
            process = subprocess.Popen(
                f'start /wait cmd /c "{activate_command} && {batch_file} {arg1} {arg2}"', shell=True
            )
            while process.poll() is None:
                completed_count, latest_file = self._collect_output_progress(gt_output_folder, total_count)
                self._report_progress(
                    phase="running",
                    totalCount=total_count,
                    completedCount=completed_count,
                    currentFile=latest_file,
                )
                time.sleep(1)
            process.wait()  # Wait for the process to complete

            completed_count, latest_file = self._collect_output_progress(gt_output_folder, total_count)
            self._report_progress(
                phase="running",
                totalCount=total_count,
                completedCount=completed_count,
                currentFile=latest_file,
            )
            if process.returncode not in (0, None):
                raise RuntimeError(f"GalTransl worker exited with code {process.returncode}")

            logger.info("GalTransl worker finished")

        except Exception as e:
            logger.error(f"Error running worker: {str(e)}")
            raise
