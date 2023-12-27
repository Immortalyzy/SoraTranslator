""" this is the project class for SoraTranslator """

import datetime as dt
import os
import pickle


class Project:
    """A project defines a translation work, storing information and configuration"""

    name = "Default Project Name"
    project_file_path = ""

    # game specific
    original_file_type = ".py"
    game_engine = "ChaosR"
    game_parser_python_file = ""
    # parsing functions
    script_file_parser = None
    block_parser = None

    # paths
    project_path = ""
    game_path = ""

    translation_engine = "gpt-3.5"
    translation_percentage = 0.0
    is_translation_complete = False
    original_language = "Japanese"
    target_language = "Chinese"

    def __init__(self):
        self.start_date = dt.datetime.now()
        self.name = ""

    @classmethod
    def from_json(cls, json_data):
        """load a project from json data, usually used to create a project from frontend"""
        print(json_data)
        instance = cls()
        instance.name = json_data.get("projectName", "Default Project Name")
        instance.project_path = json_data.get("projectPath", None)
        instance.game_path = json_data.get("gamePath", None)
        instance.translation_engine = json_data.get("translator", None)
        instance.original_language = json_data.get("fromLanguage", None)
        instance.target_language = json_data.get("toLanguage", None)
        return instance

    @classmethod
    def from_pickle(cls, pickle_file):
        """load a project from a pickle file"""
        instance = pickle.load(pickle_file)
        return instance

    def create_project(self, **kwargs):
        """create a new project, with most basic information"""
        self.game_engine = kwargs.get("game_engine", None)
        self.open_game(kwargs.get("game_path", None))
        self.original_language = kwargs.get("original_language", self.original_language)
        self.target_language = kwargs.get("target_language", self.target_language)

    def open_game(self, game_path):
        """open a game in the project"""
        # analyse the path type
        # if it is a file
        if os.path.isfile(game_path):
            # if it is a file, check if it is a supported file
            if game_path.endswith(".py"):
                self.original_file_type = ".py"
        # if it is a folder
        elif os.path.isdir(game_path):
            # if it is a folder, check if it is a supported folder
            self.original_file_type = "directory"
        elif game_path is None:
            # if it is not specified, ask user to specify
            pass

    def load_project(self, project_path):
        """load a project from a project file"""
        pass

    def save(self):
        """save the project to a project file"""
        file_name = f"{self.name}.soraproject"
        full_path = os.path.join(self.project_path, file_name)
        self.project_file_path = full_path
        print(f"Saving project to {full_path}...")
        try:
            self.save_project_to(full_path)
        except:
            return False

    def save_project_to(self, project_path):
        """save a project to a project file"""
        with open(project_path, "wb") as pickle_file:
            pickle.dump(self, pickle_file)
