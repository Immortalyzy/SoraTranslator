""" test the integration of Magical*Girl games"""

from pickle import dump, load
import shutil
import os
from scriptfile import ScriptFile
from block import Block

from ..Integrators.utils import utilities as util
from ..Integrators.Magical_Girl.magical_girl_game import MagicalGirlGame
from ..Integrators.Magical_Girl.parser import (
    parse_file,
    parse_block,
    create_nscripter_command_list,
)

ns_file = "U:/Toys/Games/Gal/MagicalGirl/1/SoraTranslator/RawText/nscript.txt"


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

    block = blocks[23]
    parse_block(block, command_strings=command_strings)

    return


def test_extraction():
    """test extraction with nsdec"""


def test_integration():
    """test integration with nscmake"""
