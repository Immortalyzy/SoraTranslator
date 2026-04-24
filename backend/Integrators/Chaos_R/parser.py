"""parser provides functions that help parse the script files and create text files"""

#!! IMPORTANT: the file passed to parser should be in utf_8 encoding

from typing import List
import re
import os
from logging import getLogger

from scriptfile import ScriptFile
from block import Block

logger = getLogger(__name__)
SELECTION_COMMAND_PATTERN = re.compile(r"""\[sel\d+[^\]]*?\btext=(['"])(.*?)\1[^\]]*\]""", re.IGNORECASE)
SELECTION_TARGET_PATTERN = re.compile(r"^SEL\d+_\d+$", re.IGNORECASE)


def find_label_marker_index(line: str):
    """Return the index of a label marker when the first non-whitespace character is '*'."""
    stripped_line = line.lstrip(" \t")
    if not stripped_line.startswith("*"):
        return None
    return len(line) - len(stripped_line)


def is_comment_line(line: str) -> bool:
    """Return whether the first non-whitespace character starts a comment."""
    return line.lstrip(" \t").startswith(";")


def parse_file(script_file: ScriptFile, encoding="utf_16") -> List[Block]:
    """this function will parse a script file to parsed blocks, this parser will omit the text at the beging of file outside of any blocks"""
    file_path = script_file.script_file_path
    try:
        with open(file_path, "r", encoding=encoding) as file:
            lines = file.readlines()
    except FileNotFoundError:
        logger.warning(f"File {file_path} not found for parsing")
        return 1

    # list of all blocks in this file
    block_list = []
    non_block_string_between_blocks = []
    block_number_for_non_block_string = []

    block_name = "start_of_file"
    block_content = []  # a list of lines

    for line in lines:
        # Check if the line is the start of a block
        label_marker_index = find_label_marker_index(line)
        if label_marker_index is not None:
            # If there is an ongoing block, save its content first
            if block_content:
                # if there is a block being recorded, save it to the block list
                block = Block(block_name, block_content)
                block_list.append(block)
                # reset the block content
                block_content = []
            # Save the new block name
            block_name = line[label_marker_index + 1 :].strip()  # remove '*' and strip whitespace
            block_content.append(line)
        else:
            # Add line to the current block's content
            block_content.append(line)

    # Add the last block's content if there is any
    if block_content:
        block = Block(block_name, block_content)
        block_list.append(block)

    logger.info(f"File {file_path} parsed, {len(block_list)} blocks found")

    # parse each block before pushing them to the script file
    for block in block_list:
        parse_block(block)

    script_file.blocks = block_list
    script_file.non_block_string_between_blocks = non_block_string_between_blocks
    script_file.block_number_for_non_block_string = block_number_for_non_block_string
    return 0


NON_HEROINE_SPEAKER_START = "[ns]"
NON_HEROINE_SPEAKER_END = "[nse]"


def parse_block(block: Block) -> (str, str, (int, int), (int, int)):
    """parse the block"""
    if is_selection_source_block(block):
        selections, selection_positions = parse_selection("".join(block.block_content))
        block.block_type = "selection"
        block.selection_original = selections
        block.selection_positions = selection_positions
        block.text_original = "/".join(selections)
        block.texts_original = selections.copy()
        block.is_parsed = True
        if block.text_original == "":
            block.is_translated = True
        return True

    speaker = ""
    speaker_line = 0
    speaker_start_end = (0, 0)
    text = ""
    texts = []
    text_line = 0
    text_start_end = (0, 0)
    # indicator for "other" speakers, this MUST be kept in this order
    # Keep replacing innermost brackets until there are none left

    texts, text_lines, text_positions = parse_text("".join(block.block_content))
    text = "".join(texts)

    # find the speaker if any
    search_pattern = r"\[【(.*?)】\]"
    # this marks the "other" speakers (other than heroines)
    search_pattern2 = r"\[ns\](.*?)\[nse\]"
    found_speakers = []
    for i, line in enumerate(block.block_content):
        # check if the line contains the [【speaker】]
        if is_comment_line(line) or find_label_marker_index(line) is not None:
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
        logger.warning(f"Multiple speakers found in block {block.block_name}, using the first one")
    if len(found_speakers) > 0:
        speaker = found_speakers[0]
    if text == "":
        # empty block
        speaker = ""
    # this debug output is expensive, disabled even for debug output
    # logger.debug(f"Block {block.block_name} parsed, speaker: {speaker}, content: {text}")
    block.speaker_original = speaker
    block.text_original = text
    block.texts_original = texts
    block.speaker_line = speaker_line
    block.speaker_start_end = speaker_start_end
    block.text_lines = text_lines
    block.text_positions = text_positions
    block.texts = texts
    block.is_parsed = True
    if block.text_original == "":
        block.is_translated = True

    return True


def find_command_span_end(text, start_index):
    """return the exclusive end position of a bracketed command span"""
    if start_index >= len(text) or text[start_index] != "[":
        return None

    depth = 1
    cursor = start_index + 1
    while cursor < len(text):
        if text[cursor] == "[":
            depth += 1
        elif text[cursor] == "]":
            depth -= 1
            if depth == 0:
                return cursor + 1
        cursor += 1

    return None


def find_structural_spans(text):
    """return sorted spans for labels and control commands that are not player-facing text"""
    spans = []
    cursor = 0
    text_length = len(text)

    while cursor < text_length:
        if text.startswith(NON_HEROINE_SPEAKER_START, cursor):
            speaker_end = text.find(NON_HEROINE_SPEAKER_END, cursor + len(NON_HEROINE_SPEAKER_START))
            if speaker_end != -1:
                speaker_end += len(NON_HEROINE_SPEAKER_END)
                spans.append((cursor, speaker_end))
                cursor = speaker_end
                continue

        if text[cursor] == ";":
            line_start = text.rfind("\n", 0, cursor) + 1
            if text[line_start:cursor].strip(" \t") == "":
                line_end = text.find("\n", cursor)
                if line_end == -1:
                    spans.append((line_start, text_length))
                    break
                spans.append((line_start, line_end + 1))
                cursor = line_end + 1
                continue

        if text[cursor] == "*":
            line_start = text.rfind("\n", 0, cursor) + 1
            if text[line_start:cursor].strip(" \t") == "":
                line_end = text.find("\n", cursor)
                if line_end == -1:
                    spans.append((line_start, text_length))
                    break
                spans.append((line_start, line_end + 1))
                cursor = line_end + 1
                continue

        if text[cursor] == "[":
            command_end = find_command_span_end(text, cursor)
            if command_end is not None:
                spans.append((cursor, command_end))
                cursor = command_end
                continue

        cursor += 1

    return spans


def parse_text(text):
    """parse the text and return the text array, line numbers and positions"""
    all_macros = find_structural_spans(text)

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


def normalize_block_name(block_name: str) -> str:
    """return the label identifier without inline caption text"""
    return block_name.split("|", 1)[0].strip()


def is_selection_target_block(block_name: str) -> bool:
    """return if the label is a selection branch target"""
    return bool(SELECTION_TARGET_PATTERN.fullmatch(normalize_block_name(block_name)))


def is_selection_source_block(block: Block) -> bool:
    """return if the block contains a selectable choice definition"""
    block_label = normalize_block_name(block.block_name)
    if not block_label.upper().startswith("SEL"):
        return False
    block_text = "".join(line for line in block.block_content if not is_comment_line(line))
    if SELECTION_COMMAND_PATTERN.search(block_text):
        return True
    return "|" in block.block_name and not is_selection_target_block(block.block_name)


def parse_selection(text):
    """extract choice text and positions from a Chaos_R selection block"""
    texts = []
    text_positions = []

    for match in SELECTION_COMMAND_PATTERN.finditer(text):
        texts.append(match.group(2))
        text_positions.append((match.start(2), match.end(2)))

    if texts:
        return texts, text_positions

    first_line_end = text.find("\n")
    first_line = text if first_line_end == -1 else text[:first_line_end]
    return parse_selection_label(first_line)


def parse_selection_label(label_line):
    """extract fallback choices from a label line such as *SEL01|Choice A/Choice B"""
    pipe_index = label_line.find("|")
    if pipe_index == -1:
        return [], []

    labels_text = label_line[pipe_index + 1 :]
    if labels_text.strip() == "":
        return [], []

    texts = []
    text_positions = []
    current_start = pipe_index + 1

    for index in range(pipe_index + 1, len(label_line)):
        if label_line[index] in "/／":
            if current_start < index:
                texts.append(label_line[current_start:index])
                text_positions.append((current_start, index))
            current_start = index + 1

    if current_start < len(label_line):
        texts.append(label_line[current_start:])
        text_positions.append((current_start, len(label_line)))

    return texts, text_positions


possible_content_re_default = [r"^(?!_).*dakr.*\.ks", r"^(?!_)luna.*\.ks", r"est.*\.ks"]


def guess_file_type(script_file: ScriptFile, possible_content_re=possible_content_re_default) -> str:
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
