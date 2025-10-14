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
from constants import DEFAULT_CONFIG_FILE
from config import Config
from Translators.all_translators import createTranslatorInstance
from logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)


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
    config = Config.from_json_file(DEFAULT_CONFIG_FILE)
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
    # read project
    # data is project path
    data = request.json
    project = Project().from_pickle(data["project_file_path"])
    # some translation settings are sent from the frontend
    config = Config.from_json_file(DEFAULT_CONFIG_FILE)

    # create translator instance
    translator = createTranslatorInstance(config.translator, config=config)

    try:
        logger.info("Translating project " + project.project_path)
        translator.translate_project(project)
        result = {"status": True}
        return result
    except Exception as e:
        logger.error("ERROR when trying to translate project " + project.project_path + " " + str(e))
        result = {"status": False}
        # get text json
        return result


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
        new_settings = request.json
        setting_passed = request.json
        config = Config.from_json_file(DEFAULT_CONFIG_FILE)
        config.from_json_obj(setting_passed)
        config.to_json_file(DEFAULT_CONFIG_FILE, replace=True)
        return jsonify(new_settings)
    else:  # GET request
        setting_from_file = Config.from_json_file(DEFAULT_CONFIG_FILE)
        return jsonify(setting_from_file.to_json_obj())


TRANSLATORS_PATH = os.path.join(os.path.dirname(__file__), "..", "translators.json")


def load_translators():
    """load translators from translators.json"""
    with open(TRANSLATORS_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for ep in cfg.get("endpoints", []):
        tok = ep.get("token", "")
        if isinstance(tok, str) and tok.startswith("ENV:"):
            env_name = tok.split(":", 1)[1]
            ep["token"] = os.getenv(env_name, "")
    return cfg


def save_selected(name: str, model_name: str):
    """update config file with the selected translator name"""
    config = Config.from_json_file(DEFAULT_CONFIG_FILE)
    # get the endpoint and token from translators.json
    items = load_translators()
    for t in items["endpoints"]:
        if t["name"] == name:
            config.endpoint_name = name
            config.endpoint = t.get("endpoint", "")
            config.token = t.get("token", "")
            config.model_name = model_name if model_name else t.get("model_names", ["gpt-4o-mini"])[0]
            break
    config.to_json_file(DEFAULT_CONFIG_FILE, replace=True)


@app.get("/endpoints")
def list_endpoints():
    """return available endpoints and the current one"""
    cfg = load_translators()
    sel = {"endpoint": Config.from_json_file(DEFAULT_CONFIG_FILE).endpoint_name}
    return jsonify({"endpoints": [e["name"] for e in cfg.get("endpoints", [])], "current": sel["endpoint"]})


@app.get("/endpoints/<endpoint_name>/models")
def list_models(endpoint_name):
    """return available models for an endpoint and the current one"""
    cfg = load_translators()
    ep = next((e for e in cfg.get("endpoints", []) if e["name"] == endpoint_name), None)
    if not ep:
        return jsonify({"error": "Unknown endpoint"}), 404
    sel = {
        "endpoint": Config.from_json_file(DEFAULT_CONFIG_FILE).endpoint_name,
        "model": Config.from_json_file(DEFAULT_CONFIG_FILE).model_name,
    }
    current_model = sel["model"] if sel["endpoint"] == endpoint_name else (ep["models"][0] if ep["models"] else None)
    return jsonify({"models": ep.get("models", []), "current": current_model})


@app.get("/translators/full")
def get_translators_full():
    """(Optional) Return full entries (backend use only)."""
    return jsonify(load_translators())


@app.post("/endpoints/select")
def select_endpoint():
    """select an endpoint"""
    data = request.get_json(force=True) or {}
    name = data.get("endpoint")
    cfg = load_translators()
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
    cfg = load_translators()
    sel = {
        "endpoint": Config.from_json_file(DEFAULT_CONFIG_FILE).endpoint_name,
        "model": Config.from_json_file(DEFAULT_CONFIG_FILE).model_name,
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
    sel = {
        "endpoint": Config.from_json_file(DEFAULT_CONFIG_FILE).endpoint_name,
        "model": Config.from_json_file(DEFAULT_CONFIG_FILE).model_name,
    }
    return jsonify(sel)


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
