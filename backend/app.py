""" this file is for api for the frontend calls"""

import re
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from project import Project
from scriptfile import ScriptFile
from textfile import TextFile
from constants import DEFAULT_CONFIG_FILE, LogLevel
from config import Config
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
        log_message("ERROR when trying to integrate game " + str(e), LogLevel.ERROR)
        return json_data


@app.route("/change_file_property", methods=["POST"])
def change_file_property():
    """manually change a file's property, used for "Mark file as ..." """
    data = request.json
    try:
        log_message("Changing file property:" + data["file_path"], LogLevel.DEBUG)
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
    log_message("Loading translation status", LogLevel.DEBUG)
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
            log_message(
                "ERROR when trying to load translation status of file " + file_path + " " + str(e),
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
        file_path = data["filePath"]
        script_file = TextFile.from_textfile(file_path=file_path)
        if len(blocks) != len(script_file.blocks):
            log_message(
                "The number of blocks in the text file is not the same as the number of blocks in the json file",
                LogLevel.ERROR,
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

        log_message("Saving text file" + script_file.text_file_path, LogLevel.INFO)
        script_file.generate_textfile(script_file.text_file_path, replace=True)
        result = {"status": True}
        return result
    except Exception as e:
        log_message("ERROR trying to save file " + str(e), LogLevel.ERROR)
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
        log_message("Translating file" + text_file.text_file_path, LogLevel.INFO)
        translator.translate_file_whole(text_file)
        text_file.generate_textfile(text_file.text_file_path, replace=True)
        result = {"status": True, "filePath": text_file.text_file_path}
        return result
    except Exception as e:
        print(e)
        result = {"status": False, "filePath": text_file.text_file_path}
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
        log_message("ERROR trying to get file info " + str(e), LogLevel.ERROR)
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


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
