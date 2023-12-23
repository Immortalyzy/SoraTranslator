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
        # script file list, stores ScriptFile instances
        self.script_file_list = []
        self.scriptfile_list_file = ""
        # to_translate file list, stores ScriptFile instances
        self.to_translate_file_list = []
        # to_translate file list file
        self.to_translate_file_list_file = ""

        # temp file info storage
        self.temp_unpack_directory = ""

    @abstractmethod
    def prepare_raw_text(self):
        """
        This generalized function should provide a combination of operations that take the raw text from the game, save it to GameResources/RawText and prepare it for further processing.
        """
        pass

    @abstractmethod
    def integrate_from_text(self, text):
        """
        This generalized function should provide a combination of operations that take the text from the GameResources/Text folder and integrate it into the game.
        """
        pass
