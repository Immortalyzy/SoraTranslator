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
from textfile import TextFile
from block import Block
from ..utils import utilities as util

# lines starting with this will be ignored
COMMENT = ";"
SPLITER = r"[ \t]+"


def create_nscripter_command_list(lines: List[str]) -> List[str]:
    """based on the file content, check for defined commands"""
    # read official command list
    official_commands = util.get_ns_command_list()
    # custom commands are defined uisng defsub
    custom_commands = []
    for line in lines:
        if line.startswith("defsub"):
            # get the command name
            command_name = re.split(SPLITER, line)[1].strip()
            # add the command name to the custom command list
            custom_commands.append(command_name)
    # combine the two lists
    command_list = official_commands + custom_commands
    return command_list


def parse_part(lines: List[str]) -> List[Block]:
    """parse a part of the script file, return a list of blocks"""
    block_list: List[Block] = []

    block_name = ""
    block_content = []  # a list of lines

    for line in lines:
        # check if is a comment line
        # Check if the line is the end of a block
        if line.strip().endswith("\\"):
            # if there is a block being recorded, save it to the block list
            block_content.append(line)

            # Save the new block name, the block name is set to be the number of the block
            block_name = str(len(block_list) + 1)
            block = Block(block_name, block_content)
            block_list.append(block)

            # reset the block content
            block_content = []
        else:
            # Add line to the current block's content
            block_content.append(line)

    # Add the last block's content if there is any
    if block_content:
        block = Block(block_name, block_content)
        block_list.append(block)
    return block_list


def parse_file(script_file: ScriptFile, **kwargs) -> List[Block]:
    """this function will parse a script file to blocks, this parser will omit the text at the beging of file outside of any blocks"""
    file_path = script_file.script_file_path
    try:
        with open(file_path, "r", encoding="gbk") as file:
            lines = file.readlines()
    except FileNotFoundError:
        log_message(
            f"File {file_path} not found for parsing", log_level=LogLevel.WARNING
        )

    # create command list
    command_strings = create_nscripter_command_list(lines)
    # add ; to the command list, this is for comments
    command_strings.append(";")

    # in nscript parts are separated by "*"
    part_list = []
    # this is a list of list of blocks
    # each list of blocks inside this list is a part
    block_list_list = []

    part_content = []  # a list of lines
    part_names = []  # a list of part names

    # ingore everything before *define
    defining = False
    comment_list = []
    comment_line_numbers = []

    # leave everything unchagned between *define and *start
    started = False

    for number, line in enumerate(lines):
        # check if is a comment line
        if line.strip().startswith(COMMENT):
            part_content.append(line)
            comment_list.append(line)
            comment_line_numbers.append(number)
            continue
        # check if start defining
        if not defining and line.strip().startswith("*define"):
            defining = True
            part_content.append(line)
            continue

        # during defining, record everything until *start
        if line.strip() == (kwargs.get("first_block", "*start")):
            started = True
            defining = False

            # push define part
            part_names.append("define")
            part_list.append(part_content)

            # push start part name
            part_names.append(kwargs.get("first_block", "*start").strip()[1:])

            part_content = []
            part_content.append(line)
            continue

        # skip everything before *define
        if (not defining) and (not started):
            # push first lines
            part_content.append(line)
            continue
        # record everything beween *define and *start without change
        if defining:
            part_content.append(line)
            continue

        # started here
        if line.strip().startswith("*"):
            # If there is an ongoing block, save its content first
            if part_content:
                # if there is a block being recorded, save it to the block list
                part_list.append(part_content)
                # push name of next part
                part_names.append(line[1:].strip())
                # reset the block content
                part_content = []
            # save the part content
            part_content.append(line)

        else:
            # Add line to the current part's content
            part_content.append(line)

    # Add the last part's content if there is any
    if part_content:
        part_list.append(part_content)

    # parse each part
    for part in part_list:
        blocks = parse_part(part)
        block_list_list.append(blocks)

    # combine all blocks
    all_blocks = []
    # empty the textfile list
    script_file.textfiles = []
    for i, block_list in enumerate(block_list_list):
        # do not parse the define part
        if part_names[i] == "define":
            all_blocks += block_list
        else:
            for block in block_list:
                parse_block(block, command_strings=command_strings)
            all_blocks += block_list

        # create a TextFile for each list
        textfile = TextFile.from_blocks(blocks=block_list)
        textfile.original_package = script_file.original_package
        textfile.script_file_path = script_file.script_file_path
        textfile.subname = util.to_valid_filename(part_names[i])
        if part_names[i] == "define":
            textfile.subname = "define"
            textfile.is_empty = True
            textfile.file_type = "system"

        script_file.textfiles.append(textfile)
        script_file.blocks_count_in_textfile.append(len(block_list))

    log_message(
        f"File {file_path} parsed, {len(block_list_list)} parts, {len(all_blocks)} blocks in total found",
        log_level=LogLevel.INFO,
    )
    script_file.blocks = all_blocks
    return 0


def parse_block(block: Block, command_strings) -> (str, str, (int, int), (int, int)):
    """parse the block"""
    speaker = ""
    speaker_line = 0
    speaker_start_end = (0, 0)
    text = ""
    texts = []
    # indicator for "other" speakers, this MUST be kept in this order
    # Keep replacing innermost brackets until there are none left

    texts, text_lines, text_positions = parse_text(
        "".join(block.block_content), command_strings=command_strings
    )
    text = "".join(texts)

    # find the speaker if any
    search_pattern = r"\[【(.*?)】\]"
    found_speakers = []
    for i, line in enumerate(block.block_content):
        # check if the line contains the [【speaker】]
        found_speaker = re.search(search_pattern, line)
        if found_speaker:
            found_speakers.append(found_speaker.group(1))
            speaker_line = i
            speaker_start_end = found_speaker.span(1)
            break

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
    block.speaker_original = speaker
    block.text_original = text
    block.texts_original = texts
    block.speaker_line = speaker_line
    block.speaker_start_end = speaker_start_end
    block.text_lines = text_lines
    block.text_positions = text_positions

    block.is_parsed = True
    if block.text_original == "":
        block.is_translated = True

    return True


# speaker indicator
speaker_indicator = r"\[([^\[\]]*)\]"


def parse_text(text, command_strings):
    """parse the text and return the text array, line numbers and positions, generated by chatgpt"""
    escaped_command_strings = [re.escape(cmd) for cmd in command_strings]
    # the look behind is to make sure the command is at the beginning of the line
    # this is specific for nscripter or other scripting language where the command must be at the beginning of the line
    # !but this might double the parsing time
    safe_command_pattern = (
        r"(?<=^) *\t*(" + "|".join(escaped_command_strings) + r").*?\n"
    )
    safe_command_pattern2 = (
        r"(?<=\n) *\t*(" + "|".join(escaped_command_strings) + r").*?\n"
    )

    # Find all positions of macros using regular expressions
    macros_general = [
        (m.start(), m.end()) for m in re.finditer(speaker_indicator, text)
    ]

    macros_ns = [(m.start(), m.end()) for m in re.finditer(safe_command_pattern, text)]
    macros_ns2 = [
        (m.start(), m.end()) for m in re.finditer(safe_command_pattern2, text)
    ]

    # Combine and sort the positions of both types of macros
    all_macros = sorted(macros_general + macros_ns + macros_ns2, key=lambda x: x[0])

    # Remove nested macros
    non_nested_macros = []
    for current_macro in all_macros:
        is_nested = False
        for other_macro in all_macros:
            if (
                current_macro != other_macro
                and other_macro[0]
                <= current_macro[0]
                < current_macro[1]
                <= other_macro[1]
            ):
                is_nested = True
                break
        if not is_nested:
            non_nested_macros.append(current_macro)

    all_macros = non_nested_macros

    # Initialize arrays
    text_array = []
    line_numbers = []
    positions = []

    # Current position in file, line, and line number
    current_pos = 0
    line_number = 1

    # Iterate over each character in the text
    for i, char in enumerate(text):
        # Check if we've reached a macro
        if all_macros and i == all_macros[0][0]:
            # Add the text before the macro to the arrays
            if current_pos < i:
                text_array.append(text[current_pos:i])
                line_numbers.append(line_number)
                positions.append((current_pos, i))

            # Update current position and remove the found macro from the list
            current_pos = all_macros.pop(0)[1]

        # Check for line breaks
        if char == "\n":
            line_number += 1
            if current_pos < i:
                text_array.append(text[current_pos:i])
                line_numbers.append(line_number - 1)
                positions.append((current_pos, i))
            current_pos = i + 1

    # Add the last segment of text if any
    if current_pos < len(text) and not any(
        text[current_pos:].lstrip().startswith(cmd) for cmd in command_strings
    ):
        text_array.append(text[current_pos:])
        line_numbers.append(line_number)
        positions.append((current_pos, len(text)))

    # remove the \\ at the end of the last text at each block
    if len(text_array) >= 1 and text_array[-1].endswith("\\"):
        text_array[-1] = text_array[-1][:-1]
        positions[-1] = (positions[-1][0], positions[-1][1] - 1)

    return text_array, line_numbers, positions
