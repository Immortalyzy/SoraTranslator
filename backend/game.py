"""
This script defines the Game class that contains almost all the gama integration top-level functions.
All child classes should have these functions declared in this class as abstract methods.
"""

from abc import ABC, abstractmethod
import importlib
import os
from typing import List
from config import default_config
from scriptfile import ScriptFile
from pickle import dump, load


class Game(ABC):
    """Parent class for all games."""

    def __init__(self, paths, name, config):
        self.name = name
        self.config = config

        # Game Resources directory, no matter the original file directory the output will be put under RawText of this folder
        self.game_resources_directory = paths["project_path"]
        self.rawtext_directory = paths["rawtext_directory"]
        self.text_directory = paths["text_directory"]
        self.translated_files_directory = paths["translated_files_directory"]

        # directory
        self.directory = ""

        # script file list, stores all script files
        self.script_file_list: List[ScriptFile] = []
        self.scriptfile_list_file = ""

        # to_translate file list, stores ScriptFile instances
        self.to_translate_file_list: List[ScriptFile] = []
        self.to_translate_file_list_file: str = ""

        # for H game, there should be a list of dangerous files
        # dangerous files cannot be directly translated by openAI GPT
        self.dangerous_file_list: List[ScriptFile] = []
        self.dangerous_file_list_file: str = ""

    @classmethod
    @abstractmethod
    def from_pythonfile(cls, paths, python_file, config=default_config):
        """create a game instance from a python file"""
        pass

    @abstractmethod
    def prepare_translation(self):
        """
        This generalized function should provide a combination of operations that prepare the game for translation.
        It includes (if necessary) extract game scripts, parsing game scripts and save them to text files.
        The method should fill the folder SoraTranslator/Text with all the text files that need to be translated.
        This method should update for the instance of the game the following variables:
        *   self.script_file_list
        *   self.to_translate_file_list
        And create the following files in SoraTranslator folder (and save the path to the corresponding variables):
        *   self.scriptfile_list_file
        *   self.to_translate_file_list_file
        """
        # todo: preparation of these list might not be needed because the translator could read directly all files under Text
        pass

    @abstractmethod
    def integrate(self):
        """
        This generalized function should provide a combination of operations that take the text from the SoraTranslator/Text folder and integrate it into the game.
        This funciton should also return some instructions for the user to follow to finalize the integration.
        """
        pass

    def save_game(self, file_path):
        """save the game instance to a file"""
        with open(file_path, "wb") as file:
            dump(self, file)
