""" test the integration of Magical*Girl games"""

from pickle import dump, load
import shutil
import os
from scriptfile import ScriptFile
from block import Block
from config import default_config
from project import Project

from ..Integrators.utils import utilities as util
from ..Integrators.Magical_Girl.magical_girl_game import MagicalGirlGame
from ..Integrators.Magical_Girl.parser import (
    parse_file,
    parse_block,
    create_nscripter_command_list,
)

ns_file = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/RawText/result.txt"
project_path = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator"
game_object_path = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/game_object.pkl"


def test_parsing():
    """test parsing"""
    # read the file
    with open(ns_file, "r", encoding="gbk") as file:
        lines = file.readlines()
    command_strings = create_nscripter_command_list(lines)

    scriptfile = ScriptFile.from_originalfile(ns_file)
    scriptfile.parse(
        parse_file, parse_block, command_strings=command_strings, first_block="*n0101"
    )
    blocks = scriptfile.blocks
    textfiles = scriptfile.textfiles

    block: Block = blocks[4]
    parse_block(block, command_strings=command_strings)

    block.text_translated = "测试翻译结果？这只是个测试结果"
    block.speaker_translated = "Speaker"
    block.generate_full_rawblock()

    return


def test_nsdec_pyfun():
    """test the py version of nsdec"""
    nsdec_pyfun = util.NSDEC_PYFUN

    in_filename = "U:/Toys/Games/Gal/MagicalGirl/1/nscript.dat"
    out_filename = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslatorTemp/result.txt"
    nsdec_pyfun(in_filename, out_filename)


def test_extraction():
    """test extraction with nsdec"""
    # create paths
    paths = Project.create_paths(project_path)
    game = MagicalGirlGame.from_pythonfile(
        paths=paths,
        python_file="U:/Toys/Games/Gal/MagicalGirl/1/game_file.py",
        config=default_config,
    )
    game.prepare_translation(replace=True)
    with open(game_object_path, "wb") as file:
        dump(game, file)


def test_integration():
    """test integration with nscmake"""

    with open(game_object_path, "rb") as file:
        game = load(file)
    scriptfile = game.script_file
    # parse the scriptfile
    # test update from textfile
    scriptfile.update_from_textfiles()
    # generate file destination path
    relative_path = os.path.relpath(scriptfile.script_file_path, game.rawtext_directory)
    translated_path = os.path.join(game.translated_files_directory, relative_path)
    # test generate textfile
    scriptfile.generate_translated_rawfile(
        dest=translated_path, replace=True, encoding=game.target_encoding
    )

    return
