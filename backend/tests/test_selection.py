"""test the integration with GalTransl and MagicalGirlGame"""

from pickle import dump, load
import shutil
import os
from scriptfile import ScriptFile
from block import Block
from config import Config, default_config
from constants import DEFAULT_CONFIG_FILE, LogLevel
from project import Project
from pathlib import Path

from ..Integrators.utils import utilities as util
from ..Integrators.Magical_Girl.magical_girl_game import MagicalGirlGame
from ..Integrators.Magical_Girl.parser import (
    parse_file,
    parse_block,
    create_nscripter_command_list,
)

from ..Translators.GalTransl_API import GalTransl_Translator

ns_file = "U:/Toys/Games/Gal/MagicalGirl/Junseitenshi/SoraTranslator/RawText/result.txt"
project_path = "U:/Toys/Games/Gal/MagicalGirl/Junseitenshi/SoraTranslator"
project_file_path = "U:/Toys/Games/Gal/MagicalGirl/Junseitenshi/SoraTranslator/Junseitenshi.soraproject"


def test_selection():
    """test translating and replacing selections"""
    with open(ns_file, "r", encoding="gbk") as file:
        lines = file.readlines()
    command_strings = create_nscripter_command_list(lines)

    # call galtransl
    project = Project.from_pickle(project_file_path)
    # find the first non-empty textfile
    choose = 0
    for textfile in project.game.script_file_list[0].textfiles:
        if not textfile.is_empty and choose >= 9:
            break
        if not textfile.is_empty:
            choose += 1

    block = textfile.blocks[-2]
    text_original = block.text_original
    block.text_translated = "testttt1/testaatewta2"
    raw_ge = block.generate_full_rawblock()

    return
