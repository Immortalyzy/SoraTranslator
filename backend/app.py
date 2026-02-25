"""this file is for api for the frontend calls"""

import os
import json
import logging

from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from project import Project
from scriptfile import ScriptFile
from textfile import TextFile
from constants import DEFAULT_ENV_FILE, DEFAULT_USER_CONFIG_FILE
from config import Config, CONFIG
from Translators.all_translators import createTranslatorInstance
from logger import setup_logger
from translation_progress import GalTranslProgressTracker

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
        script_file = TextFile.from_textfile(data)
        print("Reading text file" + script_file.text_file_path)
        result = script_file.to_json()
        result["status"] = True
        return result
    except:
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

    try:
        text_file = TextFile.from_textfile(data["file_path"])
        logger.info("Translating file" + text_file.text_file_path)
        translator.translate_file_whole(text_file)
        result = {"status": True, "filePath": text_file.text_file_path}
        return result
    except Exception as e:
        logger.error("ERROR when trying to translate file " + text_file.text_file_path + " " + str(e))
        result = {"status": False, "filePath": text_file.text_file_path}
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
