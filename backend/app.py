""" this file is for api for the frontend calls"""
import re
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from project import Project
from scriptfile import ScriptFile
from constants import Config, DEFAULT_CONFIG_FILE, LogLevel
from Translators.all_translators import createTranslatorInstance
from logger import log_message


app = Flask(__name__)
CORS(app)


@app.route("/open_project", methods=["POST"])
def open_project():
    """receive a json data from frontend, load a project from pickle file"""
    data = request.json
    try:
        project = Project().from_pickle(data["project_file_path"])
        json_data = project.to_json()
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
    except:
        json_data = project.to_json()
        json_data["status"] = False
        project.save()
        return json_data


@app.route("/require_text_json", methods=["POST"])
def require_text_json():
    """return the text json file"""
    # read project
    data = request.json
    try:
        script_file = ScriptFile.from_textfile(data)
        print("Reading text file" + script_file.text_file_path)
        result = script_file.to_json()
        result["status"] = True
        print(len(result["blocks"]))
        return result
    except Exception as e:
        print(e)
        result = {"status": False}
        # get text json
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
    log_message("Loading translation status", LogLevel.DEBUG)
    for file_path in file_list:
        try:
            script_file = ScriptFile.from_textfile(file_path)
            if not script_file.is_translated:
                status_list.append("not_translated")
            if script_file.need_manual_fix:
                status_list.append("need_manual_fix")
            if script_file.is_translated and not script_file.need_manual_fix:
                status_list.append("translated")
        except Exception as e:
            log_message(
                "ERROR when trying to load translation status of file "
                + file_path
                + " "
                + str(e),
                LogLevel.ERROR,
            )
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
        file_path = data["file_path"]
        script_file = ScriptFile.from_textfile(file_path=file_path)
        if len(blocks) != len(script_file.blocks):
            log_message(
                "The number of blocks in the text file is not the same as the number of blocks in the json file",
                LogLevel.ERROR,
            )
            result = {"status": False}
            return result
        for i, block in enumerate(script_file.blocks):
            block.text_translated = blocks[i]["text_translated"]
            block.speaker_translated = blocks[i]["speaker_translated"]
            if blocks[i]["is_edited"]:
                block.is_translated = True
                block.translation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                block.translation_engine = "manual"

        log_message("Saving text file" + script_file.text_file_path, LogLevel.INFO)
        script_file.generate_textfile(script_file.text_file_path)
        result = {"status": True}
        return result
    except Exception as e:
        log_message(e, LogLevel.ERROR)
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
    config = Config.from_json(DEFAULT_CONFIG_FILE)
    config.temperature = data["temperature"]
    config.max_lines = data["max_lines"]

    # create translator instance
    translator = createTranslatorInstance("gpt", config=config)

    try:
        script_file = ScriptFile.from_textfile(data["file_path"])
        log_message("Translating file" + script_file.text_file_path, LogLevel.INFO)
        translator.translate_file_whole(script_file)
        script_file.generate_textfile(script_file.text_file_path, replace=True)
        result = {"status": True, "filePath": script_file.text_file_path}
        return result
    except Exception as e:
        print(e)
        result = {"status": False, "filePath": script_file.text_file_path}
        # get text json
        return result


if __name__ == "__main__":
    app.run(debug=True)
