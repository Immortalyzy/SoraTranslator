"""this file is for api for the frontend calls"""

import os
import json
import logging

from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from block import Block
from project import Project
from scriptfile import ScriptFile
from textfile import TextFile
from constants import DEFAULT_ENV_FILE, DEFAULT_USER_CONFIG_FILE
from config import Config, CONFIG
from Translators.all_translators import createTranslatorInstance
from logger import setup_logger
from translation_progress import GalTranslProgressTracker
from global_name_replacement import (
    GLOBAL_NAME_REPLACEMENT_FILE_TYPE,
    GLOBAL_NAME_REPLACEMENT_SCRIPT_PATH,
    NameReplacementRow,
    build_name_replacement_mapping,
    global_name_replacement_path,
    is_global_name_replacement_file,
    normalize_name_replacement_rows,
    sort_name_replacement_rows_by_appearance,
)

setup_logger()
logger = logging.getLogger(__name__)
logger.info("Logger setuped.")


def refresh_global_config():
    runtime_cfg = Config.load_runtime(resolve_env_tokens=True)
    CONFIG.from_json_obj(runtime_cfg.to_json_obj())
    return runtime_cfg


refresh_global_config()
logger.info("Runtime configurations loaded.")

app = Flask(__name__)
CORS(app)
GALTRANSL_PROGRESS = GalTranslProgressTracker()


def build_global_name_replacement_textfile(file_path: str, rows: list[NameReplacementRow]):
    """Build canonical TextFile payload for global name replacement table."""
    text_file = TextFile()
    text_file.text_file_path = file_path
    text_file.script_file_path = GLOBAL_NAME_REPLACEMENT_SCRIPT_PATH
    text_file.file_type = GLOBAL_NAME_REPLACEMENT_FILE_TYPE
    text_file.original_package = "global"
    text_file.is_translated = True
    text_file.need_manual_fix = False
    text_file.translation_percentage = 100.0
    text_file.blocks = []

    for index, row in enumerate(rows, start=1):
        block = Block(str(index), "")
        block.is_parsed = True
        block.speaker_original = row.source_name
        block.text_original = row.source_count
        block.speaker_translated = row.replacement_name
        block.text_translated = ""
        block.is_translated = True
        block.translation_engine = "manual"
        text_file.blocks.append(block)

    text_file.generate_name_list()
    return text_file


def canonicalize_global_name_replacement_file(file_path, rows=None):
    """
    Canonicalize global name replacement file using normalization policy:
    duplicate sources keep last row, empty replacement means no replacement.
    """
    if rows is None:
        if os.path.exists(file_path):
            source_textfile = TextFile.from_textfile(file_path)
            rows = normalize_name_replacement_rows(source_textfile.blocks)
        else:
            rows = []
    else:
        rows = normalize_name_replacement_rows(rows)

    rows = sort_name_replacement_rows_by_appearance(rows)
    text_file = build_global_name_replacement_textfile(file_path, rows)
    text_file.generate_textfile(dest=file_path, replace=True)
    return text_file


def find_global_name_replacement_table_path(file_path):
    """Find nearest global name replacement table path for a given text file."""
    current_directory = os.path.dirname(file_path)
    while True:
        candidate = global_name_replacement_path(current_directory)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(current_directory)
        if parent == current_directory:
            return ""
        current_directory = parent


def load_global_name_replacement_mapping_for_file(file_path):
    """Load global name replacement mapping for a text file path."""
    table_path = find_global_name_replacement_table_path(file_path)
    if table_path == "":
        return {}
    table_file = TextFile.from_textfile(table_path)
    return build_name_replacement_mapping(table_file.blocks)


def apply_name_mapping_to_text_directory(text_directory, mapping):
    """Apply name mapping to all text csv files under text_directory."""
    if not mapping:
        return 0, 0

    updated_file_count = 0
    updated_block_count = 0
    for root, _, files in os.walk(text_directory):
        for file_name in files:
            if not file_name.lower().endswith(".csv"):
                continue
            full_path = os.path.join(root, file_name)
            if is_global_name_replacement_file(full_path):
                continue
            try:
                text_file = TextFile.from_textfile(full_path)
            except Exception as error:
                logger.warning("Skipping name propagation for %s due to load error: %s", full_path, error)
                continue
            if text_file.file_type == GLOBAL_NAME_REPLACEMENT_FILE_TYPE:
                continue

            changed_blocks = text_file.update_name_translation(mapping)
            if changed_blocks <= 0:
                continue
            text_file.generate_textfile(text_file.text_file_path, replace=True)
            updated_file_count += 1
            updated_block_count += changed_blocks

    return updated_file_count, updated_block_count


def read_env_entries(env_path=DEFAULT_ENV_FILE):
    """Read KEY=VALUE lines from .env-style file."""
    entries = {}
    if not os.path.exists(env_path):
        return entries

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            content = line.strip()
            if not content or content.startswith("#") or "=" not in content:
                continue
            key, value = content.split("=", 1)
            entries[key.strip()] = value.strip()
    return entries


def write_env_entries(updates, env_path=DEFAULT_ENV_FILE):
    """Merge updates into .env-style file and current process environment."""
    existing = read_env_entries(env_path)
    for key, value in updates.items():
        if value is None or value == "":
            existing.pop(key, None)
            os.environ.pop(key, None)
        else:
            existing[key] = value
            os.environ[key] = value

    with open(env_path, "w", encoding="utf-8") as file:
        for key in sorted(existing.keys()):
            file.write(f"{key}={existing[key]}\n")


def save_user_config(partial_updates):
    """Merge updates into config.user.json and persist."""
    current = Config._load_json_dict(DEFAULT_USER_CONFIG_FILE) or {}
    current.update(partial_updates)
    with open(DEFAULT_USER_CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(current, file, indent=4, ensure_ascii=False)


def derive_env_name_for_endpoint(endpoint_name, token_value):
    """Derive environment variable name for endpoint tokens."""
    if isinstance(token_value, str) and token_value.startswith("ENV:"):
        return token_value.split(":", 1)[1]

    sanitized = "".join(char if char.isalnum() else "_" for char in endpoint_name.upper()).strip("_")
    if not sanitized:
        sanitized = "SORA_ENDPOINT"
    return f"{sanitized}_API_KEY"


@app.route("/health", methods=["GET"])
def health():
    """Lightweight readiness probe for launcher health checks."""
    return {"status": "ok"}


@app.route("/get_project", methods=["GET"])
def get_project():
    """API used to store the initial project"""
    project_name = os.environ.get("PROJECT_NAME", "default_project")
    if not project_name or project_name == "default_project" or project_name.strip() == "":
        project_name = "default_project"
    # check if a valid project name (should be a file path, should not be empty)
    logger.info("Setting initial project " + project_name)
    return {"project": project_name}


@app.route("/open_project", methods=["POST"])
def open_project():
    """receive a json data from frontend, load a project from pickle file"""
    data = request.json
    try:
        project = Project().from_pickle(data["project_file_path"])
        json_data = project.to_json()
        json_data["project_file_path"] = data["project_file_path"]
        # add status: True to the json data
        json_data["status"] = True
        return json_data
    except:
        json_data = {"status": False}
        return json_data


@app.route("/create_project", methods=["POST"])
def create_project():
    """receive a json data from frontend, create a project and save it to a pickle file"""
    data = request.json
    project = Project().from_json(data)
    success = project.save()
    # create a .bat file at the project file path to run the run.bat with the project file path as argument
    if success:
        try:
            this_dir = os.path.dirname(os.path.realpath(__file__))
            # run .bat is in this_dir/../run.bat
            run_bat_dir = os.path.abspath(os.path.join(this_dir, ".."))
            run_bat_path = os.path.abspath(os.path.join(this_dir, "..", "run.bat"))
            with open(os.path.join(project.project_path, "openSoraTranslator.bat"), "w") as f:
                f.write(f"cd /d {run_bat_dir}\n")
                f.write(run_bat_path + " " + project.project_file_path)
        except Exception as e:
            logger.error("ERROR when trying to create project file " + str(e))
            success = False
    return {"status": success, "project_file_path": project.project_file_path}


@app.route("/initialize_game", methods=["POST"])
def initialize_game():
    """initialize the game, prepare for translation"""
    # read project
    data = request.json
    # load project from pickle file
    project = Project().from_json(data)
    project.save()

    # initiate game
    try:
        success = project.initiate_game()
        json_data = project.to_json()
        project.save()
        json_data["status"] = success
        return json_data
    except Exception as e:
        logger.error("ERROR when trying to initialize game " + str(e))
        json_data = project.to_json()
        json_data["status"] = False
        project.save()
        return json_data


@app.route("/integrate_game", methods=["POST"])
def integrate_game():
    """integrate the game, runs the integrate() function of Game"""
    data = request.json
    json_data = {}
    try:
        project = Project().from_pickle(data["project_file_path"])
        indication = project.integrate_game()
        # this process will read aditional info to project instance
        project.save()
        json_data["status"] = True
        json_data["indication"] = indication
        return json_data
    except Exception as e:
        json_data = {"status": False}
        logger.error("ERROR when trying to integrate game " + str(e))
        return json_data


@app.route("/change_file_property", methods=["POST"])
def change_file_property():
    """manually change a file's property, used for "Mark file as ..." """
    data = request.json
    try:
        logger.debug("Changing file property:" + data["file_path"])
        text_file = TextFile.from_textfile(data["file_path"])
        property_name = data["property_name"]
        property_value = data["property_value"]
        setattr(text_file, property_name, property_value)
        text_file.generate_textfile(text_file.text_file_path, replace=True)
        result = {"status": True}
        return result
    except:
        result = {"status": False}
        return result


@app.route("/require_text_json", methods=["POST"])
def require_text_json():
    """return the text json file"""
    # read project
    data = request.json
    try:
        if is_global_name_replacement_file(data):
            script_file = canonicalize_global_name_replacement_file(data)
        else:
            script_file = TextFile.from_textfile(data)
        print("Reading text file" + script_file.text_file_path)
        result = script_file.to_json()
        result["status"] = True
        return result
    except Exception as e:
        logger.error("ERROR trying to load text json for %s: %s", data, e)
        result = {"status": False}
        return result


@app.route("/require_translation_status", methods=["POST"])
def require_tranlsation_status():
    """return the translation status for frontend to display"""
    # there are three types of status
    # 1. white: not translated
    # 2. red (or yellow): translated but need manual fix
    # 3. green: translated and no need to fix
    # 4, black or red : invaild file
    file_list = request.json["file_paths"]
    result = {"file_paths": file_list}
    status_list = []
    logger.debug("Loading translation status")
    for file_path in file_list:
        try:
            if is_global_name_replacement_file(file_path):
                status_list.append("name_replacement")
                continue

            script_file = TextFile.from_textfile(file_path)
            if not script_file.is_translated:
                status_list.append("not_translated")
            else:  # is translated
                if script_file.need_manual_fix:
                    status_list.append("need_manual_fix")
                else:
                    status_list.append("translated")

        except Exception as e:
            logger.error("ERROR when trying to load translation status of file " + file_path + " " + str(e))
            status_list.append("invalid_file")
    result["status_list"] = status_list
    result["status"] = True
    return result


@app.route("/save_text_from_json", methods=["POST"])
def save_text_from_json():
    """save the text json file"""
    # read project
    data = request.json
    # read config from local file
    try:
        blocks = data["blocks"]
        file_path = data["filePath"]
        if is_global_name_replacement_file(file_path):
            normalized_rows = normalize_name_replacement_rows(blocks)
            mapping = build_name_replacement_mapping(normalized_rows)
            canonicalize_global_name_replacement_file(file_path, normalized_rows)
            updated_files, updated_blocks = apply_name_mapping_to_text_directory(os.path.dirname(file_path), mapping)
            logger.info(
                "Saving global name replacement table %s: %d rows, %d active mappings, %d files/%d blocks updated.",
                file_path,
                len(normalized_rows),
                len(mapping),
                updated_files,
                updated_blocks,
            )
            result = {"status": True}
            return result

        script_file = TextFile.from_textfile(file_path=file_path)
        if len(blocks) != len(script_file.blocks):
            logger.error(
                "The number of blocks in the text file is not the same as the number of blocks in the json file"
            )
            result = {"status": False}
            return result
        for i, block in enumerate(script_file.blocks):
            block.text_translated = blocks[i]["text_translated"] if blocks[i]["text_translated"] else ""
            block.speaker_translated = blocks[i]["speaker_translated"] if blocks[i]["speaker_translated"] else ""
            if blocks[i]["is_edited"]:
                block.is_translated = True
                block.translation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                block.translation_engine = "manual"

        logger.info("Saving text file" + script_file.text_file_path)
        script_file.generate_textfile(script_file.text_file_path, replace=True)
        result = {"status": True}
        return result
    except Exception as e:
        logger.error("ERROR trying to save file " + str(e))
        result = {"status": False}
        # get text json
        return result


@app.route("/translate_text", methods=["POST"])
def translate_text():
    """translate a file"""
    # read project
    # data is file path
    data = request.json
    # some translation settings are sent from the frontend
    config = Config.load_runtime(resolve_env_tokens=True)
    config.gpt_temperature = float(data["temperature"])
    config.gpt_max_lines = int(data["max_lines"])

    # create translator instance
    translator = createTranslatorInstance(config.translator, config=config)

    text_file = None
    try:
        if is_global_name_replacement_file(data["file_path"]):
            result = {
                "status": False,
                "filePath": data["file_path"],
                "error": "Global name replacement table is settings-only and cannot be translated.",
            }
            return result

        text_file = TextFile.from_textfile(data["file_path"])
        logger.info("Translating file" + text_file.text_file_path)
        translator.translate_file_whole(text_file)
        mapping = load_global_name_replacement_mapping_for_file(text_file.text_file_path)
        changed_name_count = text_file.update_name_translation(mapping)
        if changed_name_count > 0:
            logger.info(
                "Applied %d global name updates after translating %s",
                changed_name_count,
                text_file.text_file_path,
            )
            text_file.generate_textfile(text_file.text_file_path, replace=True)
        result = {"status": True, "filePath": text_file.text_file_path}
        return result
    except Exception as e:
        file_hint = text_file.text_file_path if text_file is not None else data.get("file_path", "")
        logger.error("ERROR when trying to translate file %s %s", file_hint, str(e))
        result = {"status": False, "filePath": file_hint}
        # get text json
        return result


@app.route("/translate_project", methods=["POST"])
def translate_project():
    """translate the project, for better integration with GalTransl"""
    data = request.json
    config = Config.load_runtime(resolve_env_tokens=True)
    is_galtransl = config.translator == "galtransl"

    if is_galtransl:
        project_hint = data.get("project_file_path", "")
        if not GALTRANSL_PROGRESS.try_start(project_hint):
            return {
                "status": False,
                "busy": True,
                "error": "A GalTransl project translation is already running.",
            }, 409
        GALTRANSL_PROGRESS.update(
            phase="preparing",
            totalCount=0,
            completedCount=0,
            currentFile="",
            error="",
        )

    project = None
    try:
        project = Project().from_pickle(data["project_file_path"])
        # create translator instance
        translator = createTranslatorInstance(config.translator, config=config)
        if is_galtransl and hasattr(translator, "set_progress_callback"):
            GALTRANSL_PROGRESS.update(projectPath=project.project_path)
            translator.set_progress_callback(GALTRANSL_PROGRESS.update)

        logger.info("Translating project " + project.project_path)
        translator.translate_project(project)
        if project.game is not None:
            mapping = project.game.load_global_name_replacement_mapping()
            updated_files, updated_blocks = apply_name_mapping_to_text_directory(project.game.text_directory, mapping)
        else:
            updated_files, updated_blocks = (0, 0)
        if updated_files > 0:
            logger.info(
                "Applied global name propagation after project translation: %d files, %d blocks.",
                updated_files,
                updated_blocks,
            )
        if is_galtransl:
            snapshot = GALTRANSL_PROGRESS.snapshot()
            final_total = max(snapshot.get("totalCount", 0), snapshot.get("completedCount", 0))
            GALTRANSL_PROGRESS.complete(force_total=final_total)
        result = {"status": True}
        return result
    except Exception as e:
        project_path = project.project_path if project is not None else data.get("project_file_path", "")
        logger.error("ERROR when trying to translate project " + project_path + " " + str(e))
        if is_galtransl:
            GALTRANSL_PROGRESS.fail(str(e))
        result = {"status": False, "error": str(e)}
        # get text json
        return result


@app.route("/translate_project_progress", methods=["GET", "POST"])
def translate_project_progress():
    """return current GalTransl project translation progress"""
    return {"status": True, "progress": GALTRANSL_PROGRESS.snapshot()}


@app.route("/request_file_info", methods=["POST"])
def request_file_info():
    """return the file info"""
    # read project
    data = request.json
    result = {}
    try:
        file_type = data["file_type"]
        file_path = data["file_path"]
        if file_type == "raw_text" or file_type == "translated_file":
            script_file = ScriptFile.from_originalfile(file_path)
            result["File path"] = script_file.original_file_path
        elif file_type == "text":
            script_file = TextFile.from_textfile(file_path)
            if script_file.file_type == GLOBAL_NAME_REPLACEMENT_FILE_TYPE or is_global_name_replacement_file(file_path):
                replacement_map = build_name_replacement_mapping(script_file.blocks)
                result["Info"] = {
                    "table": "Global name replacement table for Chaos-R integration.",
                    "rules": "Duplicate source rows use the last row. Empty replacement means no replacement.",
                    "active_replacements": len(replacement_map),
                }
                result["Trnslted?"] = True
                result["Need fix?"] = False
                result["Percent"] = 100.0
                result["Parsed on"] = script_file.read_date
                result["File type"] = GLOBAL_NAME_REPLACEMENT_FILE_TYPE
                result["Package"] = "global"
            else:
                result["Info"] = script_file.info
                # info is a dict, so add N of parts, N of blocks each part and parts that have problems here

                result["Trnslted?"] = script_file.is_translated
                result["Need fix?"] = script_file.need_manual_fix
                result["Percent"] = script_file.translation_percentage

                # result["Script file"] = script_file.original_file_path
                result["Parsed on"] = script_file.read_date
                result["File type"] = script_file.file_type
                result["Package"] = script_file.original_package
        else:
            result["info"] = "Unsupported info type"
        response = {
            "status": True,
            "info": result,
        }
        return response
    except Exception as e:
        logger.error("ERROR trying to get file info " + str(e))
        response = {"status": False}
        return response


@app.route("/preferences", methods=["GET", "POST"])
def preferences():
    """require or save settings"""
    if request.method == "POST":
        setting_passed = request.get_json(force=True) or {}
        filtered = {}
        for key, value in setting_passed.items():
            if hasattr(CONFIG, key):
                if Config._is_plaintext_secret(key, value):
                    logger.warning(
                        "Legacy plaintext secret received in /preferences for key '%s'. Consider ENV:<KEY> migration.",
                        key,
                    )
                filtered[key] = value
            else:
                logger.warning("Unknown /preferences key '%s' ignored.", key)

        save_user_config(filtered)
        refresh_global_config()
        return jsonify({"status": True, "saved_keys": list(filtered.keys())})

    setting_from_file = Config.load_runtime(resolve_env_tokens=False)
    return jsonify(setting_from_file.to_json_obj())


TRANSLATORS_PATH = os.path.join(os.path.dirname(__file__), "..", "translators.json")


def load_translators(resolve_tokens=True):
    """load translators from translators.json"""
    with open(TRANSLATORS_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if resolve_tokens:
        for ep in cfg.get("endpoints", []):
            tok = ep.get("token", "")
            if isinstance(tok, str) and tok.startswith("ENV:"):
                env_name = tok.split(":", 1)[1]
                ep["token"] = os.getenv(env_name, "")
    return cfg


def save_selected(name: str, model_name: str):
    """update user config with selected translator name"""
    items = load_translators(resolve_tokens=False)
    for t in items["endpoints"]:
        if t["name"] == name:
            selected_model = model_name if model_name else (t.get("models") or ["gpt-4o-mini"])[0]
            updates = {
                "endpoint_name": name,
                "endpoint": t.get("endpoint", ""),
                "token": t.get("token", ""),
                "model_name": selected_model,
            }
            if name == "OpenAI":
                updates["openai_api_key"] = t.get("token", "")

            save_user_config(updates)
            refresh_global_config()
            break


@app.get("/setup/options")
def setup_options():
    """return simple setup options for first-run key onboarding"""
    cfg = load_translators(resolve_tokens=False)
    current = Config.load_runtime(resolve_env_tokens=False)
    return jsonify(
        {
            "endpoints": [
                {
                    "name": ep.get("name"),
                    "models": ep.get("models", []),
                }
                for ep in cfg.get("endpoints", [])
            ],
            "current": {
                "endpoint": current.endpoint_name,
                "model": current.model_name,
                "proxy": current.proxy,
            },
        }
    )


@app.post("/setup/save")
def setup_save():
    """save essential first-run settings with env-backed key storage"""
    data = request.get_json(force=True) or {}
    endpoint_name = str(data.get("endpoint") or "").strip()
    model_name = str(data.get("model") or "").strip()
    api_key = str(data.get("api_key") or "").strip()
    proxy = str(data.get("proxy") or "").strip()

    if not endpoint_name:
        return jsonify({"ok": False, "error": "Endpoint is required"}), 400
    if not model_name:
        return jsonify({"ok": False, "error": "Model is required"}), 400
    if not api_key:
        return jsonify({"ok": False, "error": "API key is required"}), 400

    translators = load_translators(resolve_tokens=False)
    endpoint_cfg = next((ep for ep in translators.get("endpoints", []) if ep.get("name") == endpoint_name), None)
    if not endpoint_cfg:
        return jsonify({"ok": False, "error": "Unknown endpoint"}), 400

    models = endpoint_cfg.get("models") or []
    if model_name not in models:
        return jsonify({"ok": False, "error": "Model not available for selected endpoint"}), 400

    env_name = derive_env_name_for_endpoint(endpoint_name, endpoint_cfg.get("token", ""))
    env_updates = {env_name: api_key}
    if proxy:
        env_updates["SORA_PROXY"] = proxy
    else:
        env_updates["SORA_PROXY"] = None

    write_env_entries(env_updates)

    user_updates = {
        "endpoint_name": endpoint_name,
        "model_name": model_name,
        "endpoint": endpoint_cfg.get("endpoint", ""),
        "token": f"ENV:{env_name}",
        "proxy": proxy if proxy else None,
    }
    if endpoint_name == "OpenAI":
        user_updates["openai_api_key"] = "ENV:OPENAI_API_KEY" if env_name == "OPENAI_API_KEY" else f"ENV:{env_name}"

    save_user_config(user_updates)
    refresh_global_config()

    return jsonify({"ok": True, "endpoint": endpoint_name, "model": model_name})


@app.get("/endpoints")
def list_endpoints():
    """return available endpoints and the current one"""
    cfg = load_translators()
    sel = {"endpoint": Config.load_runtime(resolve_env_tokens=False).endpoint_name}
    return jsonify({"endpoints": [e["name"] for e in cfg.get("endpoints", [])], "current": sel["endpoint"]})


@app.get("/endpoints/<endpoint_name>/models")
def list_models(endpoint_name):
    """return available models for an endpoint and the current one"""
    cfg = load_translators(resolve_tokens=False)
    ep = next((e for e in cfg.get("endpoints", []) if e["name"] == endpoint_name), None)
    if not ep:
        return jsonify({"error": "Unknown endpoint"}), 404
    runtime_cfg = Config.load_runtime(resolve_env_tokens=False)
    sel = {
        "endpoint": runtime_cfg.endpoint_name,
        "model": runtime_cfg.model_name,
    }
    current_model = sel["model"] if sel["endpoint"] == endpoint_name else (ep["models"][0] if ep["models"] else None)
    return jsonify({"models": ep.get("models", []), "current": current_model})


@app.get("/translators/full")
def get_translators_full():
    """(Optional) Return full entries (backend use only)."""
    return jsonify(load_translators(resolve_tokens=False))


@app.post("/endpoints/select")
def select_endpoint():
    """select an endpoint"""
    data = request.get_json(force=True) or {}
    name = data.get("endpoint")
    cfg = load_translators(resolve_tokens=False)
    ep = next((e for e in cfg.get("endpoints", []) if e["name"] == name), None)
    if not ep:
        return jsonify({"ok": False, "error": "Unknown endpoint"}), 400
    # when endpoint changes, default model becomes the endpoint's first model
    default_model = ep["models"][0] if ep.get("models") else None
    save_selected(name, default_model)
    return jsonify({"ok": True, "endpoint": name, "model": default_model})


@app.post("/models/select")
def select_model():
    """select a model for the current endpoint"""
    data = request.get_json(force=True) or {}
    model = data.get("model")
    cfg = load_translators(resolve_tokens=False)
    runtime_cfg = Config.load_runtime(resolve_env_tokens=False)
    sel = {
        "endpoint": runtime_cfg.endpoint_name,
        "model": runtime_cfg.model_name,
    }
    ep = next((e for e in cfg.get("endpoints", []) if e["name"] == sel["endpoint"]), None)
    if not ep:
        return jsonify({"ok": False, "error": "No endpoint selected"}), 400
    if model not in (ep.get("models") or []):
        return jsonify({"ok": False, "error": "Model not available for current endpoint"}), 400
    save_selected(sel["endpoint"], model)
    return jsonify({"ok": True, "endpoint": sel["endpoint"], "model": model})


@app.get("/translators/selected")
def get_selected_translator():
    """return the current selected translator"""
    runtime_cfg = Config.load_runtime(resolve_env_tokens=False)
    sel = {
        "endpoint": runtime_cfg.endpoint_name,
        "model": runtime_cfg.model_name,
    }
    return jsonify(sel)


if __name__ == "__main__":
    logger.info("Starting Flask server...")
    app.run(debug=False, threaded=True)
