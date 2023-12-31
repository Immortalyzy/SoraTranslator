""" this file is for api for the frontend calls"""
import re
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from project import Project
from scriptfile import ScriptFile
from constants import Config, DEFAULT_CONFIG_FILE
from Translators.all_translators import createTranslatorInstance


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


@app.route("/save_text_from_json", methods=["POST"])
def save_text_from_json():
    """save the text json file"""
    # read project
    data = request.json
    # read config from local file
    config = Config.from_json(DEFAULT_CONFIG_FILE)
    # apply temperatory config for this request
    config.gpt_temperature = data["gpt_temperature"]
    config.gpt_max_lines = data["gpt_max_lines"]

    # create translator instance
    translator = createTranslatorInstance("gpt", config)
    try:
        script_file = ScriptFile.from_textfile(data["file_path"])
        print("Saving text file" + script_file.text_file_path)
        script_file.generate_textfile(script_file.text_file_path)
        result = {"status": True}
        return result
    except Exception as e:
        print(e)
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
        print("Translating file" + script_file.text_file_path)
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
