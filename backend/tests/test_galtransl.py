from pathlib import Path

import yaml

from config import Config
from constants import SuccessStatus as success

from ..Translators.GalTransl_API import (
    GalTranslTranslator,
    build_galtransl_settings_bridge,
    write_galtransl_project_config,
)


def build_template_config(template_path: Path):
    template_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "backendSpecific": {
            "OpenAI-Compatible": {
                "tokens": [
                    {
                        "token": "template-token",
                        "endpoint": "https://template.invalid/v1",
                        "modelName": "template-model",
                    }
                ]
            }
        },
        "common": {
            "gpt.enhance_jailbreak": False,
            "gpt.prompt_content": "template prompt",
            "gpt.numPerRequestTranslate": 3,
        },
        "proxy": {
            "enableProxy": False,
            "proxies": [
                {
                    "address": "http://127.0.0.1:7890",
                }
            ],
        },
    }
    template_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def build_test_translator(tmp_path: Path, config=None):
    translator = object.__new__(GalTranslTranslator)
    translator.config = config or Config()
    translator._progress_callback = None
    translator.this_path = str(tmp_path / "translator_root")
    translator.CONFIG_FILENAME = "config.yaml"
    build_template_config(Path(translator.this_path) / "GalTransl" / "sampleProject" / "config.inc.yaml")
    return translator


class DummyTextFile:
    def __init__(self, file_path: Path):
        self.text_file_path = str(file_path)
        self.is_empty = False
        self.is_translated = False
        self.name_list_original = ["Alice"]
        self.name_list_translated = ["Alice"]
        self.name_list_count = [1]
        self.generated_json_path = None
        self.updated_json_path = None
        self.generated_text_path = None

    def generate_galtransl_json(self, dest="", replace=False):
        self.generated_json_path = Path(dest)
        self.generated_json_path.parent.mkdir(parents=True, exist_ok=True)
        self.generated_json_path.write_text("[]", encoding="utf-8")
        return 0

    def update_from_galtransl_json(self, json_file=""):
        self.updated_json_path = Path(json_file)
        return True

    def generate_textfile(self, file_path, replace=True):
        self.generated_text_path = Path(file_path)


class DummyScriptFile:
    def __init__(self, textfiles):
        self.textfiles = textfiles


class DummyGame:
    def __init__(self, script_file_list):
        self.script_file_list = script_file_list
        self.name_list_original = ["Alice"]
        self.name_list_translated = ["Alice"]
        self.name_list_count = [1]


class DummyProject:
    def __init__(self, project_path: Path, script_file_list):
        self.project_path = str(project_path)
        self.game = DummyGame(script_file_list)


def test_translate_file_whole_writes_nested_text_runs_under_project_galtransl(tmp_path):
    project_root = tmp_path / "project"
    text_path = project_root / "Text" / "route_a" / "chapter_1" / "scene.csv"
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text("", encoding="utf-8")

    config = Config()
    config.proxy = "http://127.0.0.1:1080"
    translator = build_test_translator(tmp_path, config=config)
    text_file = DummyTextFile(text_path)

    def fake_run_worker(project_path, worker_settings, total_count=0):
        output_file = Path(project_path) / "gt_output" / f"{text_path.name}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("[]", encoding="utf-8")
        assert worker_settings["translation_method"] == config.galtransl_translation_method
        assert total_count == 1

    translator.run_worker = fake_run_worker

    result = translator.translate_file_whole(text_file)
    expected_workspace = project_root / "GalTransl" / "individual" / "route_a" / "chapter_1" / text_path.name

    assert result == success.SUCCESS
    assert text_file.generated_json_path == expected_workspace / "gt_input" / f"{text_path.name}.json"
    assert text_file.updated_json_path == expected_workspace / "gt_output" / f"{text_path.name}.json"
    assert text_file.generated_text_path == text_path
    assert (expected_workspace / "config.yaml").exists()
    assert not (project_root / "Text" / "GalTransl").exists()


def test_individual_workspace_is_human_readable_and_unique_for_duplicate_basenames(tmp_path):
    project_root = tmp_path / "project"
    first_file = project_root / "Text" / "route_a" / "shared.csv"
    second_file = project_root / "Text" / "route_b" / "shared.csv"

    first_workspace = GalTranslTranslator._resolve_individual_workspace(first_file)
    second_workspace = GalTranslTranslator._resolve_individual_workspace(second_file)

    assert first_workspace != second_workspace
    assert first_workspace == project_root / "GalTransl" / "individual" / "route_a" / "shared.csv"
    assert second_workspace == project_root / "GalTransl" / "individual" / "route_b" / "shared.csv"


def test_settings_bridge_writes_consistent_project_config_for_multiple_workspaces(tmp_path):
    config = Config()
    config.proxy = "http://127.0.0.1:1080"
    config.token = "test-token"
    config.endpoint = "https://example.invalid/v1"
    config.model_name = "test-model"
    config.galtransl_translation_method = "ForGal-json"

    settings_bridge = build_galtransl_settings_bridge(config)
    template_path = tmp_path / "template.yaml"
    build_template_config(template_path)

    target_a = tmp_path / "workspace_a" / "config.yaml"
    target_b = tmp_path / "workspace_b" / "config.yaml"
    target_a.parent.mkdir(parents=True, exist_ok=True)
    target_b.parent.mkdir(parents=True, exist_ok=True)

    write_galtransl_project_config(str(template_path), str(target_a), settings_bridge)
    write_galtransl_project_config(str(template_path), str(target_b), settings_bridge)

    yaml_a = yaml.safe_load(target_a.read_text(encoding="utf-8"))
    yaml_b = yaml.safe_load(target_b.read_text(encoding="utf-8"))

    assert yaml_a == yaml_b
    assert yaml_a["proxy"]["enableProxy"] is True
    assert yaml_a["proxy"]["proxies"][0]["address"] == config.proxy
    assert yaml_a["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["token"] == config.token
    assert yaml_a["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["endpoint"] == config.endpoint
    assert yaml_a["backendSpecific"]["OpenAI-Compatible"]["tokens"][0]["modelName"] == config.model_name
    assert yaml_a["common"]["gpt.numPerRequestTranslate"] == 10
    assert settings_bridge["worker"]["translation_method"] == config.galtransl_translation_method


def test_prepare_workspace_keeps_project_level_gt_folders_for_shared_readers(tmp_path):
    translator = build_test_translator(tmp_path)
    workspace = translator._prepare_workspace(tmp_path / "project" / "GalTransl", clear_json=True)

    assert workspace["workspace_path"] == tmp_path / "project" / "GalTransl"
    assert workspace["gt_input_folder"] == tmp_path / "project" / "GalTransl" / "gt_input"
    assert workspace["gt_output_folder"] == tmp_path / "project" / "GalTransl" / "gt_output"
    assert workspace["config_path"] == tmp_path / "project" / "GalTransl" / "config.yaml"


def test_collect_output_progress_recurses_into_nested_output_folders(tmp_path):
    output_root = tmp_path / "project" / "GalTransl" / "gt_output"
    first_output = output_root / "k_scenario" / "shared.csv.json"
    second_output = output_root / "EMB_patch" / "shared.csv.json"
    first_output.parent.mkdir(parents=True, exist_ok=True)
    second_output.parent.mkdir(parents=True, exist_ok=True)
    first_output.write_text("[]", encoding="utf-8")
    second_output.write_text("[]", encoding="utf-8")

    completed_count, latest_file = GalTranslTranslator._collect_output_progress(output_root, total_count=5)

    assert completed_count == 2
    assert latest_file in {
        "k_scenario\\shared.csv.json",
        "EMB_patch\\shared.csv.json",
    }


def test_translate_project_keeps_duplicate_basenames_separate_by_relative_path(tmp_path):
    project_root = tmp_path / "project"
    first_path = project_root / "Text" / "k_scenario" / "shared.csv"
    second_path = project_root / "Text" / "EMB_patch" / "shared.csv"
    first_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("", encoding="utf-8")
    second_path.write_text("", encoding="utf-8")

    first_text = DummyTextFile(first_path)
    second_text = DummyTextFile(second_path)
    project = DummyProject(project_root, [DummyScriptFile([first_text]), DummyScriptFile([second_text])])
    translator = build_test_translator(tmp_path)

    def fake_run_worker(project_path, worker_settings, total_count=0):
        first_output = translator._resolve_project_json_path(first_text.text_file_path, Path(project_path) / "gt_output")
        second_output = translator._resolve_project_json_path(second_text.text_file_path, Path(project_path) / "gt_output")
        first_output.parent.mkdir(parents=True, exist_ok=True)
        second_output.parent.mkdir(parents=True, exist_ok=True)
        first_output.write_text("[]", encoding="utf-8")
        second_output.write_text("[]", encoding="utf-8")
        assert first_output != second_output
        assert worker_settings["translation_method"] == translator.config.galtransl_translation_method
        assert total_count == 2

    translator.run_worker = fake_run_worker

    translator.translate_project(project)

    assert first_text.generated_json_path == project_root / "GalTransl" / "gt_input" / "k_scenario" / "shared.csv.json"
    assert second_text.generated_json_path == project_root / "GalTransl" / "gt_input" / "EMB_patch" / "shared.csv.json"
    assert first_text.updated_json_path == project_root / "GalTransl" / "gt_output" / "k_scenario" / "shared.csv.json"
    assert second_text.updated_json_path == project_root / "GalTransl" / "gt_output" / "EMB_patch" / "shared.csv.json"
    assert first_text.is_translated is True
    assert second_text.is_translated is True
