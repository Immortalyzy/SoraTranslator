""" This file defines the functions for dealing with the games from Magical-girl
    Last active game: 漆黒のルナリア ～淫らな館にとらわれる犬耳ロリータ～ on 2012
    Game engine: NScripter
    Text is stored in nscript.dat which defines a lot of things, including the text.
    The prepare_translation function should do the following things:
        1, extract the nscript.dat file,
        2, parse the nscript.dat file, separate the text into parts and save the text to text files
        3, update the script_file_list and to_translate_file_list
    Parameters to prepare:
        1, start line of the main script
"""

import importlib.util
import os
import shutil
from constants import LogLevel
from config import default_config
from game import Game
from scriptfile import ScriptFile, update_script_filelist
from .encoding_fix import fix_allfiles
from .parser import guess_file_type, parse_file, parse_block
from logger import log_message


class MagicalGirlGame(Game):
    """class for MagicalGirl Game"""

    def __init__(self, paths, name, config=default_config):
        super().__init__(paths, name, config)

        self.text_start = 0
        self.text_end = 0
