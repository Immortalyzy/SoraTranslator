"""This file defines the API used to interact with GalTransl"""

import importlib.util
import sys
import os
import shutil
import subprocess
import signal
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import yaml
from datetime import datetime
from project import Project
from textfile import TextFile
from block import Block
from config import Config, default_config
from constants import SuccessStatus as success
from constants import LogLevel
from logger import log_message
from .translator import Translator


def sync_config_to_yaml(config: Config, yaml_file: str):
    """sync the config to the yaml file"""
    # open the yaml file
    with open(yaml_file, "r", encoding="utf-8") as file:
        yaml_object = yaml.load(file, Loader=yaml.FullLoader)

    try:
        # proxy settings
        if config.proxy is not "":
            yaml_object["proxy"]["enableProxy"] = True
            yaml_object["proxy"]["proxies"][0]["address"] = config.proxy
        else:
            yaml_object["proxy"]["enableProxy"] = False

        # token settings
        yaml_object["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["token"] = config.token
        yaml_object["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["endpoint"] = config.endpoint
        yaml_object["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["modelName"] = config.modelName

        # common settings
        yaml_object["common"]["gpt.enhance_jailbreak"] = True
        yaml_object["common"]["gpt.prompt_content"] = ""

    except Exception as e:
        log_message(f"Error: {e}", LogLevel.ERROR)
        print(f"Error: {e}")

    # save the yaml file
    with open(yaml_file, "w", encoding="utf-8") as file:
        yaml.dump(yaml_object, file, default_flow_style=False, sort_keys=False, allow_unicode=True)


class GalTransl_Translator(Translator):
    """API to interact with GalTransl"""

    def __init__(self, config: Config = default_config):
        super().__init__(config)

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
            log_message("Error: Worker function not found!", LogLevel.ERROR)

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
            log_message(f"Failed to import {module_name}.{attribute_name}: {e}", LogLevel.ERROR)
            return None

    def translate_file_whole(self, text_file: TextFile) -> success:
        """This function will create an environment for GalTransl to translate the text file"""

        # create a project (for this file) config .yaml file
        ## copy the default config to the project directory
        ### generate tempate config path
        template_yaml_config_path = os.path.join(self.this_path, "GalTransl/sampleProject/config.inc.yaml")
        text_file_path = Path(text_file.text_file_path)
        text_file_name = text_file_path.name

        ## store each translate single file in a separate folder, the folder name is the same as the file name
        target_folder_path = text_file_path.parent.parent / "GalTransl" / text_file_name
        ## mkdir the folder
        os.makedirs(target_folder_path, exist_ok=True)
        ## the yaml config is stored in the this folder
        target_yaml_config_path = os.path.join(target_folder_path, self.CONFIG_FILENAME)
        ## copy the template config to the folder, if the file exists, overwrite it
        shutil.copyfile(template_yaml_config_path, target_yaml_config_path)

        ## sync the config file from config to the yaml file, the API key, etc.
        sync_config_to_yaml(self.config, target_yaml_config_path)

        # create the GalTransl folders
        gt_input_folder = os.path.join(target_folder_path, "gt_input")
        gt_output_folder = os.path.join(target_folder_path, "gt_output")
        output_file_name = os.path.join(gt_output_folder, text_file_name + ".json")
        # mkdir the folders
        os.makedirs(gt_input_folder, exist_ok=True)
        os.makedirs(gt_output_folder, exist_ok=True)

        # create the json file in the gt_input folder under the project directory
        target_json_file_path = os.path.join(gt_input_folder, text_file_name + ".json")
        text_file.generate_galtransl_json(dest=target_json_file_path, replace=True)

        # prepare the dictionary of characters' names
        starting_line = "JP_Name,CN_Name,Count\n"
        # if the name list is empty, this will just write the header, prompt the user to fill the file
        exsiting_empty = False
        for i, name in enumerate(text_file.name_list_original):
            if text_file.name_list_translated[i] == "":
                exsiting_empty = True
            starting_line += f"{name},{text_file.name_list_translated[i]},{text_file.name_list_count[i]}\n"

        namelist_file_path = os.path.join(target_folder_path, "人名替换表.csv")
        with open(namelist_file_path, "w", encoding="utf-8") as file:
            file.write(starting_line)

        # prompt the user to fill the name list
        if exsiting_empty:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.after(100, lambda: root.lift())
            messagebox.showinfo(
                "人名替换表为空",
                f"请按照GalTransl要求填写 人名替换表.csv 以达到更好的翻译效果，文件在 {target_folder_path}",
            )
            root.destroy()

        # read the 人名替换表.csv file
        with open(namelist_file_path, "r", encoding="utf-8") as file:
            namelist = file.readlines()
        # remove the header
        namelist = namelist[1:]
        # sync the name list to the textfile instance
        for line in namelist:
            jp_name, cn_name, count = line.strip().split(",")
            if jp_name in text_file.name_list_original:
                index = text_file.name_list_original.index(jp_name)
                text_file.name_list_translated[index] = cn_name
            else:
                log_message(f"Warning: {jp_name} not found in the original name list", LogLevel.WARNING)

        # call GalTransl
        self.run_worker(target_folder_path)

        # read the translation results (sync to textfile instance)
        if os.path.exists(output_file_name):
            text_file.update_from_galtransl_json(output_file_name)
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
        # create a project (for this file) config .yaml file
        ## copy the default config to the project directory
        ### generate tempate config path
        template_yaml_config_path = os.path.join(self.this_path, "GalTransl/sampleProject/config.inc.yaml")
        project_path = Path(project.project_path)

        ## store each translate single file in a separate folder, the folder name is the same as the file name
        target_folder_path = project_path / "GalTransl"
        ## mkdir the folder
        os.makedirs(target_folder_path, exist_ok=True)
        ## the yaml config is stored in the this folder
        target_yaml_config_path = os.path.join(target_folder_path, self.CONFIG_FILENAME)
        ## copy the template config to the folder, if the file exists, overwrite it
        shutil.copyfile(template_yaml_config_path, target_yaml_config_path)

        ## sync the config file from config to the yaml file, the API key, etc.
        sync_config_to_yaml(self.config, target_yaml_config_path)

        # create the GalTransl folders
        gt_input_folder = os.path.join(target_folder_path, "gt_input")
        gt_output_folder = os.path.join(target_folder_path, "gt_output")
        # mkdir the folders
        os.makedirs(gt_input_folder, exist_ok=True)
        os.makedirs(gt_output_folder, exist_ok=True)

        # create the json files in the gt_input folder under the project directory
        def textfile_2_json_name(tf):
            """return the json file name for the textfile"""
            return os.path.join(gt_input_folder, Path(tf.text_file_path).name + ".json")

        def json_name_2_textfile(json_name):
            """return the textfile for the json file name"""
            for i, script_file in enumerate(project.game.script_file_list):
                for j, text_file in enumerate(script_file.textfiles):
                    if os.path.join(gt_output_folder, Path(text_file.text_file_path).name + ".json") == json_name:
                        return text_file
            log_message(f"Error: {json_name} not found in the project", LogLevel.ERROR)
            return None

        for i, script_file in enumerate(project.game.script_file_list):
            for j, text_file in enumerate(script_file.textfiles):
                if text_file.is_empty:
                    continue
                text_file.generate_galtransl_json(dest=textfile_2_json_name(text_file), replace=True)

        # prepare the dictionary of characters' names
        namelist_file_path = os.path.join(target_folder_path, "人名替换表.csv")
        # if the file exists, read the result first
        # read the 人名替换表.csv file
        if os.path.exists(namelist_file_path):
            with open(namelist_file_path, "r", encoding="utf-8") as file:
                namelist = file.readlines()
            # remove the header
            namelist = namelist[1:]
            # sync the name list to the textfile instance
            for line in namelist:
                jp_name, cn_name, _ = line.strip().split(",")
                if jp_name in project.game.name_list_original:
                    index = project.game.name_list_original.index(jp_name)
                    project.game.name_list_translated[index] = cn_name
                else:
                    log_message(f"Warning: {jp_name} not found in the original name list", LogLevel.WARNING)
        else:
            # create the name file and write current name list
            starting_line = "JP_Name,CN_Name,Count\n"
            # if the name list is empty, this will just write the header, prompt the user to fill the file
            exsiting_empty = False
            for i, name in enumerate(project.game.name_list_original):
                if project.game.name_list_translated[i] == "":
                    exsiting_empty = True
                starting_line += f"{name},{project.game.name_list_translated[i]},{project.game.name_list_count[i]}\n"

            with open(namelist_file_path, "w", encoding="utf-8") as file:
                file.write(starting_line)

            # prompt the user to fill the name list if any name is empty
            if exsiting_empty:
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                root.after(100, lambda: root.lift())
                messagebox.showinfo(
                    "人名替换表为空",
                    f"请按照GalTransl要求填写 人名替换表.csv 以达到更好的翻译效果，文件在 {target_folder_path}",
                )
                root.destroy()

            # read the 人名替换表.csv file
            with open(namelist_file_path, "r", encoding="utf-8") as file:
                namelist = file.readlines()
            # remove the header
            namelist = namelist[1:]
            # sync the name list to the textfile instance
            for line in namelist:
                jp_name, cn_name, _ = line.strip().split(",")
                if jp_name in project.game.name_list_original:
                    index = project.game.name_list_original.index(jp_name)
                    project.game.name_list_translated[index] = cn_name
                else:
                    log_message(f"Warning: {jp_name} not found in the original name list", LogLevel.WARNING)

        # call GalTransl
        self.run_worker(target_folder_path)

        # read the translation results (sync to textfiles instance)
        ## list the files inside the gt_output folder
        output_files = os.listdir(gt_output_folder)
        log_message("Reading the translation results of GalTransl", LogLevel.INFO)
        log_message(f"{len(output_files)} files found", LogLevel.INFO)
        for output_file in output_files:
            output_file_path = os.path.join(gt_output_folder, output_file)
            text_file = json_name_2_textfile(output_file_path)
            if text_file is None:
                continue
            text_file.update_from_galtransl_json(output_file_path)
            # mark the file as translated, this will make the file appear as green in the GUI
            text_file.is_translated = True
            text_file.generate_textfile(text_file.text_file_path, replace=True)

    def run_worker(self, project_path: str):
        """run the worker function in a separate thread, wait for the worker to finish"""

        batch_file = os.path.join(self.galtransl_path, "run_GalTransl_zh.bat")
        arg1 = project_path
        arg2 = self.config.galtransl_translation_method

        log_message("Running GalTransl worker in a separate thread", LogLevel.INFO)
        try:
            process = subprocess.Popen(f'start /wait cmd /c "{batch_file}" {arg1} {arg2}', shell=True)
            process.wait()  # Wait for the process to complete

            log_message("GalTransl worker finished", LogLevel.INFO)

        except Exception as e:
            log_message(f"Error running worker: {str(e)}", LogLevel.ERROR)
