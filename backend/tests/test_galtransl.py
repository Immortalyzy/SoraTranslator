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
    choose = 3
    for textfile in project.game.script_file_list[0].textfiles:
        if not textfile.is_empty and choose >= 1:
            break
        if not textfile.is_empty:
            choose += 1

    # create the API
    config = Config.from_json_file(DEFAULT_CONFIG_FILE)
    galtranslapi = GalTransl_Translator(config=config)

    # translate the textfile
    project_path = Path(project.project_path)
    galtranslapi.translate_file_whole(textfile)

    ## store each translate single file in a separate folder, the folder name is the same as the file name
    target_folder_path = project_path / "GalTransl"
    gt_output_folder = os.path.join(target_folder_path, "gt_output")

    def json_name_2_textfile(json_name):
        """return the textfile for the json file name"""
        for i, script_file in enumerate(project.game.script_file_list):
            for j, text_file in enumerate(script_file.textfiles):
                if os.path.join(gt_output_folder, Path(text_file.text_file_path).name + ".json") == json_name:
                    return text_file
        return None

    output_files = os.listdir(gt_output_folder)
    for output_file in output_files:
        output_file_path = os.path.join(gt_output_folder, output_file)
        text_file = json_name_2_textfile(output_file_path)
        if text_file is None:
            continue
        text_file.update_from_galtransl_json(output_file_path)
        # mark the file as translated, this will make the file appear as green in the GUI
        text_file.is_translated = True
        text_file.generate_textfile(text_file.text_file_path, replace=True)

    print("done!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return
