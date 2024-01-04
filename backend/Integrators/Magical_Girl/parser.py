""" parser provides functions that help parse the script files and create text files
    For magical Girl games, based on the tutorials of Dir-A, GBK encoding must be used
    format of Nscripter:
    for identifying non-text:
        the commands are defined at the begining of the file using defsub
    for text:
        *block indicator: at the end of each block a "@" or "\\" is added ("\\" means clear the screen)
        *speaker indicator: [speaker], it seems the [] symbol will not be displayed and the content inside is rendered before the main text

    for separating text:
        "*" starts a new part, so the subfiles could be divided into parts that is easier to manually improve

"""

from typing import List
import re
import os
from logger import log_message
from constants import LogLevel
from scriptfile import ScriptFile
from block import Block

marco_indicator = r"\[ns\].*?\[nse\]"
macro_indicator2 = r"\[([^\[\]]*)\]"

# there cannot be any "?" symbol in the BGK format
# the script file is singular so no need to write scripts for integration


def parse_file(script_file: ScriptFile) -> List[Block]:
    """this function will parse a script file to blocks, this parser will omit the text at the beging of file outside of any blocks"""
    file_path = script_file.script_file_path
    try:
        with open(file_path, "r", encoding="gbk") as file:
            lines = file.readlines()
    except FileNotFoundError:
        log_message(
            f"File {file_path} not found for parsing", log_level=LogLevel.WARNING
        )

    # list of all blocks in this file
    block_list = []
    non_block_string_between_blocks = []
    block_number_for_non_block_string = []

    block_name = "start_of_file"
    block_content = []  # a list of lines

    for line in lines:
        # check if is a comment line
        if line.strip().startswith(";"):
            continue
        # Check if the line is the start of a block
        if line.startswith("*"):
            # If there is an ongoing block, save its content first
            if block_content:
                # if there is a block being recorded, save it to the block list
                block = Block(block_name, block_content)
                block_list.append(block)
                # reset the block content
                block_content = []
            # Save the new block name
            block_name = line[1:].strip()  # remove '*' and strip whitespace
            block_content.append(line)
        else:
            # Add line to the current block's content
            block_content.append(line)

    # Add the last block's content if there is any
    if block_content:
        block = Block(block_name, block_content)
        block_list.append(block)

    log_message(
        f"File {file_path} parsed, {len(block_list)} blocks found",
        log_level=LogLevel.INFO,
    )
    return (
        block_list,
        non_block_string_between_blocks,
        block_number_for_non_block_string,
    )


def parse_block(block: Block) -> (str, str, (int, int), (int, int)):
    """parse the block"""
    speaker = ""
    speaker_line = 0
    speaker_start_end = (0, 0)
    text = ""
    text_line = 0
    text_start_end = (0, 0)
    # indicator for "other" speakers, this MUST be kept in this order
    # Keep replacing innermost brackets until there are none left

    # this only works when there is only one text in one line
    for i, line in enumerate(block.block_content):
        # skip the block name line
        if "*" in line:
            continue
        clean_block = re.sub(marco_indicator, "", line)
        while True:
            clean_block, count = re.subn(macro_indicator2, "", clean_block)
            if count == 0:
                break
        text += clean_block.strip()

    if text == "":
        # empty block
        return speaker, text, speaker_line, speaker_start_end, text_line, text_start_end

    for i, line in enumerate(block.block_content):
        found_text = re.search(text, line)
        if found_text:
            text_line = i
            text_start_end = found_text.span()
            break
        else:
            log_message(
                f"Text found in block {block.block_name} but cannot locate in block_content",
                log_level=LogLevel.ERROR,
            )
            # add a temporary solution by remove all middle script commands
            # find the start of the text, take the first 2 characters
            text_start = text[:1]
            found_text = re.search(text_start, line)
            if found_text:
                text_line = i
                text_start_end = (found_text.span()[0], text_start_end[1])
            # find the end of the text, take the last 2 characters
            text_end = text[-1:]
            matches = list(re.finditer(text_end, line))
            if matches:
                last_match = matches[-1]
                text_start_end = (text_start_end[0], last_match.span()[1])

            if text_start_end[1] < text_start_end[0]:  # it HAS TO BE < instead of <=
                # this usually means that the text is not in the same line
                return parse_block(fix_multiline_block(block))
            if found_text and matches:
                break

    # find the speaker if any
    search_pattern = r"\[【(.*?)】\]"
    # this marks the "other" speakers (other than heroines)
    search_pattern2 = r"\[ns\](.*?)\[nse\]"
    found_speakers = []
    for i, line in enumerate(block.block_content):
        # check if the line contains the [【speaker】]
        if "*" in line:
            continue
        found_speaker = re.search(search_pattern, line)
        found_speaker2 = re.search(search_pattern2, line)
        if found_speaker2:
            found_speakers.append(found_speaker2.group(1))
            speaker_line = i
            speaker_start_end = found_speaker2.span(1)
            break
        if found_speaker:
            found_speakers.append(found_speaker.group(1))
            speaker_line = i
            speaker_start_end = found_speaker.span(1)
            break
        # ! warning: if both exist, only the second one will be used

    if len(found_speakers) > 1:
        log_message(
            f"Multiple speakers found in block {block.block_name}, using the first one",
            log_level=LogLevel.WARNING,
        )
    if len(found_speakers) > 0:
        speaker = found_speakers[0]
    if text == "":
        # empty block
        speaker = ""

    log_message(
        f"Block {block.block_name} parsed, speaker: {speaker}, content: {text}",
        log_level=LogLevel.DEBUG,
    )
    return speaker, text, speaker_line, speaker_start_end, text_line, text_start_end


def fix_multiline_block(block: Block):
    """This function will fix the multiline block, combine all lines with text to one line
    !!! this function will modify the block, generated block will be different from the original block
    """
    lines_containing_text = []
    for i, line in enumerate(block.block_content):
        # skip the block name line
        if "*" in line:
            continue
        clean_line = re.sub(marco_indicator, "", line)
        while True:
            clean_line, count = re.subn(macro_indicator2, "", clean_line)
            if count == 0:
                break

        if clean_line.strip() != "":
            lines_containing_text.append(i)
    # check if the lines are continuous
    for i in range(len(lines_containing_text) - 1):
        if lines_containing_text[i + 1] - lines_containing_text[i] != 1:
            # raise ValueError("Lines are not continuous")
            log_message(
                "Lines are not continuous, moving all text to first line",
                log_level=LogLevel.WARNING,
            )

    # combine all lines with text to one line
    all_text_lines = ""
    for i in lines_containing_text:
        # remove "\n" before adding to the all text
        all_text_lines += block.block_content[i].strip()

    # replace first line with all text
    block.block_content[lines_containing_text[0]] = all_text_lines

    # remove all other lines
    for i in lines_containing_text[1:]:
        block.block_content[i] = ""

    return block


possible_content_re = [r"^(?!_).*dakr.*\.ks", r"^(?!_)luna.*\.ks", r"est.*\.ks"]


def guess_file_type(script_file: ScriptFile) -> str:
    """guess the file type based on the file name"""
    # get the file extension
    file_extension = os.path.splitext(script_file.script_file_path)[1]

    if file_extension != ".ks":
        return "system"

    # get the file basename
    file_basename = os.path.basename(script_file.script_file_path)
    # match the file with possible content file re
    for re_string in possible_content_re:
        if re.match(re_string, file_basename):
            if file_basename.endswith("H.ks"):
                return "Hcontent"
            return "content"

    return "other"
