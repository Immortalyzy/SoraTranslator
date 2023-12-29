""" this file is for api for the frontend calls"""
import re
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from project import Project
from scriptfile import ScriptFile


app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "Hello, Flask!"


@app.route("/test", methods=["POST"])
def test():
    print("test")
    return "test"


@app.route("/hello/<name>")
def hello_there(name):
    now = datetime.now()
    formatted_now = now.strftime("%A, %d %B, %Y at %X")

    # Filter the name argument to letters only using regular expressions. URL arguments
    # can contain arbitrary text, so we restrict to safe characters only.
    match_object = re.match("[a-zA-Z]+", name)
    print("test")
    app.logger.debug("test")

    if match_object:
        clean_name = match_object.group(0)
    else:
        clean_name = "Friend"

    content = "Hello there, " + clean_name + "! It's " + formatted_now
    return content


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


if __name__ == "__main__":
    app.run(debug=True)
