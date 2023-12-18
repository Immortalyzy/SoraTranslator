""" parser provides functions that help parse the script files and create text files"""
#!! IMPORTANT: the file passed to parser should be in utf_16 encoding

from typing import List
import re
from ...scriptfile import ScriptFile
from ...block import Block
from ...logger import log_message
from ...constants import LogLevel

def parse_file(script_file: ScriptFile) -> List[Block]:
    """ this function will parse a script file to blocks, this parser will omit the text at the beging of file outside of any blocks """
    file_path = script_file.script_file_path
    try:
        with open(file_path, "r", encoding="utf_16") as file:
            lines = file.readlines()
    except FileNotFoundError:
        log_message(f"File {file_path} not found for parsing", log_level=LogLevel.WARNING)

    block_list = [] # list of all blocks in this file
    block_name = ""
    block_content = [] # a list of lines

    for line in lines:
        # check if is a comment line
        if line.startswith(';'):
            continue
        # Check if the line is the start of a block
        if line.startswith('*'):
            # If there is an ongoing block, save its content first
            if block_content:
                # if there is a block being recorded, save it to the block list
                block = Block(block_name, block_content)
                block_list.append(block)
                # reset the block content
                block_content = []
            # Save the new block name
            block_name = line[1:].strip()  # remove '*' and strip whitespace
        else:
            # Add line to the current block's content
            block_content.append(line)

    # Add the last block's content if there is any
    if block_content:
        block = Block(block_name, block_content)
        block_list.append(block)

    log_message(f"File {file_path} parsed, {len(block_list)} blocks found", log_level=LogLevel.INFO)
    return block_list


def parse_block(block: Block) -> (str, str):
    """parse the block"""
    speaker = "narration"
    content = ""
    marco_indicator = r'\[.*?\]'
    for line in block.block_content:
        clean_block = re.sub(marco_indicator, '', line)
        content += clean_block.strip()

    # find the speaker if any
    search_pattern = r"\[【(.*?)】\]"
    found_speakers = []
    for line in block.block_content:
        # check if the line contains the [【speaker】]
        found_speaker = re.search(search_pattern, line)
        if found_speaker:
            found_speakers.append(found_speaker.group(1))

    if len(found_speakers) > 1:
        log_message(f"Multiple speakers found in block {block.block_name}, using the first one", log_level=LogLevel.WARNING)
    if len(found_speakers) > 0:
        speaker = found_speakers[0]

    log_message(f"Block {block.block_name} parsed, speaker: {speaker}, content: {content}", log_level=LogLevel.DEBUG)
    return speaker, content
