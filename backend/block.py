""" define the Block class """

#!! csv sperator used is tab "\t"

from logger import log_message
from constants import LogLevel


def default_text_separater(text_translated_whole: str, texts_original: list[str]) -> list[str]:
    """
    Splits `text_translated_whole` into len(texts_original) parts.

    Special rule:
      - If every element of texts_original ends with '。' and the
        number of '。' in text_translated_whole matches len(texts_original),
        then split by those '。' exactly.

    Otherwise:
      - Use a proportional split approach.
      - If the corresponding original part ends in '。', attempt to
        align the translated split so that segment also ends with '。'.
    """
    # --- 1) Check for the special case --- # for NScripter games
    all_original_end_circle = all(part.endswith("。") for part in texts_original)
    num_segments = len(texts_original)

    # Count the '。' in the translated text
    translated_circles_positions = []
    for idx, ch in enumerate(text_translated_whole):
        if ch == "。":
            translated_circles_positions.append(idx)

    # Special case trigger
    if all_original_end_circle and len(translated_circles_positions) == num_segments:
        # We can split by these positions exactly.
        # Each segment i will go from the previous position (start_of_segment)
        # to translated_circles_positions[i] (inclusive of '。').

        segments = []
        start_index = 0
        for circle_pos in translated_circles_positions:
            # slice up to and including this '。'
            segments.append(text_translated_whole[start_index : circle_pos + 1])
            start_index = circle_pos + 1

        # If there is any leftover text after the last '。', we can either:
        # - append it to the final segment, or
        # - ignore it (depending on the requirement).
        # To ensure we don't lose content, we usually append it to the last segment.
        if start_index < len(text_translated_whole):
            segments[-1] += text_translated_whole[start_index:]

        return segments

    # --- 2) Proportional splitting approach ---
    # Compute total length of all original segments
    # (You might optionally ignore trailing '。' if you don't want them to count in proportion.)
    total_original_length = sum(len(part) for part in texts_original)
    if total_original_length == 0:
        # Edge case: if there's nothing in texts_original or they are all empty
        # just return the entire text as one segment or empty segments
        if num_segments <= 1:
            return [text_translated_whole]
        else:
            # Return repeated empty or something to match lengths.
            # Or distribute text if there's at least one non-empty segment requested.
            # Here we distribute text proportionally anyway.
            return [text_translated_whole] + [""] * (num_segments - 1)

    # We will build segments one by one
    segments = []
    translated_len = len(text_translated_whole)
    prev_cut = 0
    accumulated_length = 0

    for i, original_part in enumerate(texts_original, start=1):
        # For the i-th segment (1-based), figure out how far we should cut
        # in the translated text proportionally.
        accumulated_length += len(original_part)

        if i < num_segments:
            # Proportional boundary (naive)
            proportional_boundary = round((accumulated_length / total_original_length) * translated_len)

            # Adjust if the original ends with '。', try to make this segment end with '。' too
            if original_part.endswith("。"):
                # Search for the next '。' in text_translated_whole at or after proportional_boundary
                # so that we ensure the segment ends with '。'.
                next_circle_pos = text_translated_whole.find("。", proportional_boundary)
                if next_circle_pos != -1:
                    # shift boundary to include that '。'
                    proportional_boundary = next_circle_pos + 1

            current_segment = text_translated_whole[prev_cut:proportional_boundary]
            segments.append(current_segment)
            prev_cut = proportional_boundary
        else:
            # Last segment: just take all the remaining text
            current_segment = text_translated_whole[prev_cut:]
            segments.append(current_segment)

    return segments


def replace_substrings(original, positions, new_texts):
    """Replace substrings in a string at given positions with new texts"""
    if len(positions) != len(new_texts):
        raise ValueError("The lengths of positions and new_texts must be the same.")

    # join the original texts
    original = "".join(original)

    # Sorting the positions by start index
    positions = sorted(positions, key=lambda x: x[0])

    last_end = 0
    parts = []
    for i, (start, end) in enumerate(positions):
        # Append part of the string that doesn't change
        parts.append(original[last_end:start])
        # Append new text
        parts.append(new_texts[i])
        last_end = end

    # Append any remaining part of the string after the last replacement
    parts.append(original[last_end:])

    # total text
    total = "".join(parts)

    # split by line
    results = total.split("\n")

    # readd the \n
    for i in range(len(results) - 1):
        results[i] += "\n"

    return results


class Block:
    """A block is a unit of text in a script file that controls the text that is shown at one time"""

    def __init__(self, block_name, block_content):
        # basic info
        self.is_parsed = False
        self.block_type = "normal"  # normal, selection or other

        # for translation
        self.is_translated = False  # will also be set to true if the block is empty
        self.speaker_original = ""
        self.speaker_translated = ""
        self.texts_original = []  # not used
        self.text_original = ""
        self.text_translated = ""
        self.block_name_line = ""

        ## for integration
        # the line number of the speaker
        self.speaker_line = 0
        # tuple for the start and end position of the speaker
        self.speaker_start_end = (0, 0)
        # list of lines for every part of the text
        self.text_lines = [0]
        # list of tuples for the positions of every part of the text
        self.text_positions = [(0, 0)]

        # for translation record
        self.translation_date = ""
        self.translation_engine = "Undefined or manual"
        self.translation_status = "stop"
        self.block_name = block_name
        self.block_content = block_content
        # replace all \t with a space to avoid problems when generating csv
        self.block_content = [line.replace("\t", "  ") for line in self.block_content]
        self.block_content_translated = ""

    @classmethod
    def from_csv_line(cls, csv_line):
        """create a block instance from a csv line, note this can only be used for translation"""
        # check if csv_line is a list
        if not isinstance(csv_line, list):
            # if not, split it
            csv_line = csv_line.split("\t")
        # check csv line length
        if len(csv_line) < 5:
            raise ValueError("CSV line length not correct")

        block_name = csv_line[0].strip()
        # when reading from csv file, the block content will not be read
        block_content = ""
        block = cls(block_name, block_content)
        # a block read from csv file is always parsed
        block.is_parsed = True

        block.speaker_original = csv_line[1].strip()
        block.text_original = csv_line[2].strip()
        block.speaker_translated = csv_line[3].strip()
        block.text_translated = csv_line[4].strip()

        if len(csv_line) >= 8:
            if csv_line[5].strip() != "Yes" and csv_line[5].strip() != "No":
                log_message(
                    f'CSV line {csv_line} has incompatible is_translated entry record. (Accepted record is "Yes" or "No")',
                    log_level=LogLevel.WARNING,
                )

            block.is_translated = csv_line[5].strip() == "Yes"
            block.translation_date = csv_line[6].strip()
            block.translation_engine = csv_line[7].strip()
        return block

    def to_csv_line(self):
        """return a csv line"""
        csv_line = []
        csv_line.append(self.block_name)
        csv_line.append(self.speaker_original)
        csv_line.append(self.text_original)
        csv_line.append(self.speaker_translated)
        csv_line.append(self.text_translated)
        is_translated_text = "Yes" if self.is_translated else "No"
        csv_line.append(is_translated_text)
        csv_line.append(self.translation_date)
        csv_line.append(self.translation_engine)
        return "\t".join(csv_line)

    def to_json(self):
        """convert to a dict (json) for frontend"""
        data = {
            "name": self.block_name,
            "speaker_original": self.speaker_original,
            "text_original": self.text_original,
            "speaker_translated": self.speaker_translated,
            "text_translated": self.text_translated,
            "is_translated": self.is_translated,
            "translation_date": self.translation_date,
            "translation_engine": self.translation_engine,
        }
        return data

    def generate_full_rawblock(self, text_separater=default_text_separater) -> str:
        """generate the full translated content, to be replaced in the script file
        The function will return the text AND set the block_content_translated variable
        """
        # todo: implement
        # check translation status and check block_content

        if self.block_content == "":
            # raise RuntimeError("Cannot generate full translated content for a block that has no original content (read from csv, verify the code)")
            return 1

        # block content is a list of lines
        temp_block_content = self.block_content.copy()
        total_replacement_positions = []
        total_replacement_texts = []
        # combine the speaker and text for eaiser processing
        if self.speaker_original != "":
            ## generate the speaker total position
            ### count all length of lines before the speaker line
            speaker_total_position = 0
            for i in range(self.speaker_line):
                speaker_total_position += len(temp_block_content[i])
            ### add to the speaker position tuple
            total_speaker_start_end = (
                self.speaker_start_end[0] + speaker_total_position,
                self.speaker_start_end[1] + speaker_total_position,
            )
            ## add to total before adding the text
            total_replacement_positions.append(total_speaker_start_end)
            total_replacement_texts.append(self.speaker_translated)

        # replace the text
        if self.text_original != "" and self.text_translated.strip() != "":
            # separate the translated text
            translated_texts = text_separater(self.text_translated, self.texts_original)
            total_replacement_positions.extend(self.text_positions)
            total_replacement_texts.extend(translated_texts)
            # positions must be absolute positions in all content (not just the position in the line)
            temp_block_content = replace_substrings(
                original=temp_block_content,
                positions=total_replacement_positions,
                new_texts=total_replacement_texts,
            )
        # remove empty lines
        # temp_block_content = [line for line in temp_block_content if line.strip() != ""]
        # add an empty line at the end
        # temp_block_content.append("")

        # replace starting "  " with "\t"
        for i, line in enumerate(temp_block_content):
            if line.startswith("  "):
                temp_block_content[i] = "\t" + line[2:]

        # note the result
        self.block_content_translated = temp_block_content
        self.is_translated = True
        return self.block_content_translated

    def is_narration(self):
        """return if the block is narration"""
        return self.speaker_original == "" or self.speaker_original == "narration"

    def is_empty(self):
        """return if the block is empty"""
        return self.is_parsed and self.text_original.strip() == ""

    def is_text_separated(self):
        """return if the text is separated"""
        return len(self.texts_original) > 1

    def text_to_translate(self, add_speaker: bool = False):
        """return the text to translate"""
        text = ""
        if add_speaker:
            text += f"{self.speaker_original}: "
        text += self.text_original
        return text

    def __str__(self):
        return f"Block {self.block_name} with {len(self.block_content)} lines"
