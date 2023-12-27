"""
This script defines the Game class that contains almost all the gama integration top-level functions.
All child classes should have these functions declared in this class as abstract methods.
"""

from abc import ABC, abstractmethod
from .constants import (
    DEFAULT_GAME_RESOURCES_DIRECTORY,
    DEFAULT_GAME_RESOURCES_RAWTEXT_DIRECTORY,
    DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY,
    DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY,
)
from pickle import dump, load


class Game(ABC):
    """Parent class for all games."""

    def __init__(self, name):
        self.name = name

        # Game Resources directory, no matter the original file directory the output will be put under RawText of this folder
        self.game_resources_directory = DEFAULT_GAME_RESOURCES_DIRECTORY
        self.rawtext_directory = DEFAULT_GAME_RESOURCES_RAWTEXT_DIRECTORY
        self.text_directory = DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY
        self.translated_files_directory = (
            DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY
        )

        # directory
        self.directory = ""

        # script file list, stores all script files
        self.script_file_list = []
        self.scriptfile_list_file = ""

        # to_translate file list, stores ScriptFile instances
        self.to_translate_file_list = []
        self.to_translate_file_list_file = ""

        # for H game, there should be a list of dangerous files
        # dangerous files cannot be directly translated by openAI GPT
        self.dangerous_file_list = []
        self.dangerous_file_list_file = ""

        # temp file info storage
        self.temp_unpack_directory = ""

    @abstractmethod
    def prepare_translation(self):
        """
        This generalized function should provide a combination of operations that prepare the game for translation.
        Fill the folder GameResources/Text with all the text files that need to be translated.
        """
        pass

    @abstractmethod
    def integrate_from_text(self, text):
        """
        This generalized function should provide a combination of operations that take the text from the GameResources/Text folder and integrate it into the game.
        This funciton should also return some instructions for the user to follow to finalize the integration.
        """
        pass

    def save_game(self, file_path):
        """save the game instance to a file"""
        with open(file_path, "wb") as file:
            dump(self, file)
