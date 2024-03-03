""" parser provides functions that help parse the script files and create text files"""
#!! IMPORTANT: the file passed to parser should be in utf_16 encoding

from typing import List
import re
import os
from logger import log_message
from constants import LogLevel
from scriptfile import ScriptFile
from block import Block


def parse_file(script_file: ScriptFile) -> List[Block]:
    """this function will parse a script file to parsed blocks, this parser will omit the text at the beging of file outside of any blocks"""
    file_path = script_file.script_file_path
    try:
        with open(file_path, "r", encoding="utf_16") as file:
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
        if line.strip().startswith("*"):
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

    # parse each block before pushing them to the script file
    for block in block_list:
        parse_block(block)

    script_file.blocks = block_list
    script_file.non_block_string_between_blocks = non_block_string_between_blocks
    script_file.block_number_for_non_block_string = block_number_for_non_block_string
    return 0


# speaker indicator for non-heroine speakers
macro_indicator = r"\[ns\].*?\[nse\]"
# general macro indicator
macro_indicator2 = r"\[([^\[\]]*)\]"
# block name
block_name_indicator = r"\*.*\n"


def parse_block(block: Block) -> (str, str, (int, int), (int, int)):
    """parse the block"""
    speaker = ""
    speaker_line = 0
    speaker_start_end = (0, 0)
    text = ""
    texts = []
    text_line = 0
    text_start_end = (0, 0)
    # indicator for "other" speakers, this MUST be kept in this order
    # Keep replacing innermost brackets until there are none left

    # check if the block is a selection block
    # selection blocks for choas-r games has a name start with \*SEL***
    if block.block_name.startswith("*SEL"):
        block.block_type = "selection"
        for i, line in enumerate(block.block_content):
            # skip the block name line
            if "*" in line:
                continue
        return speaker, text, speaker_line, speaker_start_end, text_line, text_start_end

    texts, text_lines, text_positions = parse_text("".join(block.block_content))
    text = "".join(texts)

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
    block.speaker_original = speaker
    block.text_original = text
    block.texts_original = texts
    block.speaker_line = speaker_line
    block.speaker_start_end = speaker_start_end
    block.text_lines = text_lines
    block.text_positions = text_positions
    block.texts = texts

    return True


def parse_text(text):
    """parse the text and return the text array, line numbers and positions, generated by chatgpt"""
    # Find all positions of macros using both regular expressions
    macros1 = [(m.start(), m.end()) for m in re.finditer(macro_indicator, text)]
    macros2 = [(m.start(), m.end()) for m in re.finditer(macro_indicator2, text)]
    macros3 = [(m.start(), m.end()) for m in re.finditer(block_name_indicator, text)]

    # Combine and sort the positions of both types of macros
    all_macros = sorted(macros1 + macros2 + macros3, key=lambda x: x[0])

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
    if current_pos < len(text):
        text_array.append(text[current_pos:])
        line_numbers.append(line_number)
        positions.append((current_pos, len(text)))

    ## Remove empty lines
    # Create new lists to hold the filtered elements
    filtered_text_array = []
    filtered_line_numbers = []
    filtered_positions = []

    # Iterate over the original list and only add non-empty lines and corresponding elements
    for i, line in enumerate(text_array):
        if line.strip() != "":  # Check if the line is not just whitespace
            filtered_text_array.append(line)
            filtered_line_numbers.append(line_numbers[i])
            filtered_positions.append(positions[i])

    # Now, if you want to replace the original lists with the filtered lists:
    text_array = filtered_text_array
    line_numbers = filtered_line_numbers
    positions = filtered_positions

    return text_array, line_numbers, positions


possible_content_re_default = [r"^(?!_).*dakr.*\.ks", r"^(?!_)luna.*\.ks", r"est.*\.ks"]


def guess_file_type(
    script_file: ScriptFile, possible_content_re=possible_content_re_default
) -> str:
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
