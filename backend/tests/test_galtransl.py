""" test the integration with GalTransl and MagicalGirlGame """

from pickle import dump, load
import shutil
import os
from scriptfile import ScriptFile
from block import Block
from config import Config, default_config
from constants import DEFAULT_CONFIG_FILE, LogLevel
from project import Project

from ..Integrators.utils import utilities as util
from ..Integrators.Magical_Girl.magical_girl_game import MagicalGirlGame
from ..Integrators.Magical_Girl.parser import (
    parse_file,
    parse_block,
    create_nscripter_command_list,
)

from ..Translators.GalTransl_API import GalTransl_Translator

ns_file = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/RawText/result.txt"
project_path = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator"
project_file_path = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/magicalgirl1.soraproject"
game_object_path = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/game_object.pkl"
temp_json_file_path = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/gt_input/temp.json"


def test_galtransl_onefile():
    """test parsing"""
    # read the file
    with open(ns_file, "r", encoding="gbk") as file:
        lines = file.readlines()
    command_strings = create_nscripter_command_list(lines)

    # call galtransl
    project = Project.from_pickle(project_file_path)
    # find the first non-empty textfile
    for textfile in project.game.script_file_list[0].textfiles:
        if not textfile.is_empty:
            break

    # create the API
    config = Config.from_json_file(DEFAULT_CONFIG_FILE)
    galtranslapi = GalTransl_Translator(config=config)

    # translate the textfile
    galtranslapi.translate_file_whole(textfile)

    print("done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return
