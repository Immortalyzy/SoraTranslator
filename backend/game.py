"""
This script defines the Game class that contains almost all the gama integration top-level functions.
All child classes should have these functions declared in this class as abstract methods.
"""

from abc import ABC, abstractmethod
import importlib
import os
from typing import List
from block import Block
from config import CONFIG
from scriptfile import ScriptFile
from textfile import TextFile
from pickle import dump, load
from global_name_replacement import (
    GLOBAL_NAME_REPLACEMENT_FILE_TYPE,
    GLOBAL_NAME_REPLACEMENT_SCRIPT_PATH,
    NameReplacementRow,
    build_name_replacement_mapping,
    global_name_replacement_path,
    normalize_name_replacement_rows,
    sort_name_replacement_rows_by_appearance,
)


class Game(ABC):
    """Parent class for all games."""

    def __init__(self, paths, name):
        self.name = name

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

        # list of string for the name of characters appearing in the game
        self.name_list_original = []
        self.name_list_translated = []
        self.name_list_count = []

    @classmethod
    @abstractmethod
    def from_pythonfile(cls, paths, python_file):
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

    def get_global_name_replacement_table_path(self):
        """Return path of managed global name replacement table in Text directory."""
        return global_name_replacement_path(self.text_directory)

    def _create_global_name_replacement_textfile(self, rows, table_path):
        """Create TextFile object for global name replacement table rows."""
        table_file = TextFile()
        table_file.text_file_path = table_path
        table_file.script_file_path = GLOBAL_NAME_REPLACEMENT_SCRIPT_PATH
        table_file.file_type = GLOBAL_NAME_REPLACEMENT_FILE_TYPE
        table_file.original_package = self.name
        table_file.is_translated = True
        table_file.need_manual_fix = False
        table_file.translation_percentage = 100.0
        table_file.blocks = []

        for index, row in enumerate(rows, start=1):
            block = Block(str(index), "")
            block.is_parsed = True
            block.speaker_original = row.source_name
            block.text_original = row.source_count
            block.speaker_translated = row.replacement_name
            block.text_translated = ""
            block.is_translated = True
            block.translation_engine = "manual"
            table_file.blocks.append(block)

        table_file.generate_name_list()
        return table_file

    def _load_existing_global_name_replacement_rows(self):
        """Load and normalize existing global name replacement rows from table file."""
        table_path = self.get_global_name_replacement_table_path()
        if not os.path.exists(table_path):
            return []

        try:
            existing_table = TextFile.from_textfile(table_path)
            return normalize_name_replacement_rows(existing_table.blocks)
        except Exception:
            return []

    def refresh_global_name_replacement_table(self):
        """
        Create or refresh global name replacement table for the game.
        Existing replacement values are preserved by source name.
        """
        table_path = self.get_global_name_replacement_table_path()
        existing_rows = self._load_existing_global_name_replacement_rows()
        existing_by_source = {row.source_name: row for row in existing_rows}

        merged_rows = []
        discovered_sources = set()

        for index, source_name in enumerate(self.name_list_original):
            discovered_sources.add(source_name)
            source_count = ""
            if index < len(self.name_list_count):
                source_count = str(self.name_list_count[index])

            existing_row = existing_by_source.get(source_name)
            replacement_name = existing_row.replacement_name if existing_row else ""
            merged_rows.append(
                NameReplacementRow(
                    source_name=source_name,
                    replacement_name=replacement_name,
                    source_count=source_count,
                )
            )

        for row in existing_rows:
            if row.source_name in discovered_sources:
                continue
            merged_rows.append(row)

        merged_rows = sort_name_replacement_rows_by_appearance(merged_rows)
        table_file = self._create_global_name_replacement_textfile(merged_rows, table_path)
        table_file.generate_textfile(dest=table_path, replace=True)

    def load_global_name_replacement_mapping(self):
        """Load mapping from global name replacement table."""
        table_path = self.get_global_name_replacement_table_path()
        if not os.path.exists(table_path):
            return {}

        table_file = TextFile.from_textfile(table_path)
        return build_name_replacement_mapping(table_file.blocks)
