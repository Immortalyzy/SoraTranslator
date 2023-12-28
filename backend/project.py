""" this is the project class for SoraTranslator """

import datetime as dt
import os
import pickle
import importlib.util
import shutil

from game import Game
from constants import default_config
from Integrators.Chaos_R.chaosr_game import ChaosRGame

supported_game_engines = {"ChaosR": ChaosRGame}


class Project:
    """A project defines a translation work, storing information and configuration"""

    # this sync with the frontend storage
    name = "Default Project Name"
    project_path = ""
    project_file_path = ""
    game_path = ""
    original_files_directory = ""
    rawtext_directory = ""
    text_directory = ""
    translated_files_directory = ""

    is_initialized = False

    # game specific
    original_file_type = ".py"
    game_engine = "ChaosR"
    game_parser_python_file = ""
    # parsing functions
    script_file_parser = None
    block_parser = None

    translation_engine = "gpt-3.5"
    translation_percentage = 0.0
    is_translation_complete = False
    original_language = "Japanese"
    target_language = "Chinese (Simplified)"

    def __init__(self):
        self.start_date = dt.datetime.now()
        self.game = None
        self.config = default_config

    @classmethod
    def from_json(cls, json_data):
        """load a project from json data, usually used to create a project from frontend"""
        print(json_data)
        instance = cls()
        instance.name = json_data.get("name", "Default Project Name")
        instance.project_path = json_data.get("project_path", None)
        instance.game_path = json_data.get("game_path", None)
        instance.translation_engine = json_data.get("translator", None)
        instance.original_language = json_data.get("original_language", None)
        instance.target_language = json_data.get("target_language", None)
        paths = instance.create_paths(instance.project_path)
        instance.original_files_directory = paths["original_files_directory"]
        instance.rawtext_directory = paths["rawtext_directory"]
        instance.text_directory = paths["text_directory"]
        instance.translated_files_directory = paths["translated_files_directory"]
        return instance

    @classmethod
    def from_pickle(cls, pickle_file):
        """load a project from a pickle file"""
        # load the project from pickle file
        with open(pickle_file, "rb") as pickle_file:
            instance = pickle.load(pickle_file)
        return instance

    def to_json(self):
        """return a json data of the project"""
        return {
            "name": self.name,
            "project_path": self.project_path,
            "game_path": self.game_path,
            "original_files_directory": self.original_files_directory,
            "rawtext_directory": self.rawtext_directory,
            "text_directory": self.text_directory,
            "translated_files_directory": self.translated_files_directory,
            "original_language": self.original_language,
            "target_language": self.target_language,
        }

    def initiate_game(self):
        """create a game instance, store it in self.game"""
        # create paths for the project
        paths = self.create_paths(self.project_path)

        if self.game_path.endswith(".py"):
            # copy this flle to the original files directory
            shutil.copyfile(
                self.game_path,
                os.path.join(paths["original_files_directory"], "game.py"),
            )

            # load the file and check engine
            if not os.path.exists(self.game_path):
                raise FileNotFoundError(f"Game file {self.game_path} not found.")
            spec = importlib.util.spec_from_file_location("game_module", self.game_path)
            game_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(game_module)
            if not hasattr(game_module, "Game"):
                print(
                    "Game class not defined in the game file. Check if using supported game engine."
                )
                if not hasattr(game_module, "GAME_ENGINE"):
                    print(
                        "GAME_ENGINE not defined in the game file. Check if using supported game engine."
                    )
                    return False
                else:
                    self.game_engine = game_module.GAME_ENGINE
                    if self.game_engine not in supported_game_engines:
                        print(
                            f"Game engine {self.game_engine} not supported. Check if using supported game engine."
                        )
                        return False
                    else:
                        # create game instance using python file
                        GameClass = supported_game_engines[self.game_engine]
                        self.game = GameClass.from_pythonfile(
                            paths=paths,
                            python_file=self.game_path,
                            config=self.config,
                        )
                        print(self.game.rawtext_directory)
            else:
                GameClass = getattr(game_module, "Game")
                self.game = GameClass()
        else:
            print("Not supported")
            return False

        # prepare translation
        try:
            success = self.game.prepare_translation(replace=True)
            if success:
                self.is_initialized = True
            return success
        except:
            return False

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

    @staticmethod
    def create_paths(project_path):
        """create paths for the project"""
        # create paths for the project
        paths = {}
        paths["project_path"] = project_path
        paths["original_files_directory"] = os.path.join(project_path, "OriginalFiles")
        paths["rawtext_directory"] = os.path.join(project_path, "RawText")
        paths["text_directory"] = os.path.join(project_path, "Text")
        paths["translated_files_directory"] = os.path.join(
            project_path, "TranslatedFiles"
        )
        # create directories
        for path in paths.values():
            if not os.path.exists(path):
                os.makedirs(path)
        return paths
