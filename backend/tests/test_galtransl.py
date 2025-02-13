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

from ..Translators.GalTransl_API import GalTranslAPI

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

    scriptfile = ScriptFile.from_originalfile(ns_file)
    scriptfile.parse(parse_file, parse_block, command_strings=command_strings, first_block="*n0101")
    blocks = scriptfile.blocks
    textfiles = scriptfile.textfiles

    # choose the first non-empty file
    for textfile in textfiles:
        if not textfile.is_empty:
            break

    # generate the json file
    textfile.generate_galtransl_json(dest=temp_json_file_path, replace=True)

    # call galtransl
    project = Project.from_pickle(project_file_path)
    # create the API
    config = Config.from_json_file(DEFAULT_CONFIG_FILE)
    galtranslapi = GalTranslAPI(config=config, project=project)

    # translate the textfile
    galtranslapi.translate_project()

    print("done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return
