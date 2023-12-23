""" this is the project class for SoraTranslator """

import datetime as dt
import os


class Project:
    """A project defines a translation work, storing information and configuration"""

    # game specific
    original_file_type = ".py"
    game_engine = "ChaosR"
    game_parser_python_file = ""
    # parsing functions
    script_file_parser = None
    block_parser = None

    GameResourcePath = ""
    OriginalFilesPath = ""
    RawTextPath = ""
    TextPath = ""
    TranslatedFilesPath = ""

    translation_engine = "gpt-3.5"
    translation_percentage = 0.0
    is_translation_complete = False
    original_language = "Japanese"
    target_language = "Chinese"

    def __init__(self):
        self.start_date = dt.datetime.now()
        self.name = ""

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
