""" define the Block class """
#!! csv sperator used is tab "\t"

from logger import log_message
from constants import LogLevel


def default_text_separater(text_translated_whole, texts_original):
    """default text separater, by chatgpt"""
    # Calculate the total length of the original text
    total_length = sum(len(text) for text in texts_original)

    # Calculate the proportion of each part of the original text
    text_proportion = [len(text) / total_length for text in texts_original]

    # Split the translated text based on the ratio
    translated_texts = []
    start = 0
    for i, proportion in enumerate(text_proportion):
        if i == len(text_proportion) - 1:  # For the last segment
            end = len(text_translated_whole)
        else:
            end = start + int(proportion * len(text_translated_whole))
            # Ensure not to split in the middle of a word
            # while (
            #     end < len(text_translated_whole)
            #     and text_translated_whole[end].isalpha()
            # ):
            #     end += 1
        translated_texts.append(text_translated_whole[start:end])
        start = end

    # Return the list of separated translated text
    return translated_texts


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

    def parse(self, parse_block_function=None):
        """parse the block"""
        (
            speaker,
            text,
            speaker_line,
            speak_start_end,
            text_lines,
            text_positions,
            texts,
        ) = parse_block_function(self)
        self.speaker_original = speaker
        self.text_original = text
        self.texts_original = texts
        self.speaker_line = speaker_line
        self.speaker_start_end = speak_start_end
        self.text_lines = text_lines
        self.text_positions = text_positions

        self.is_parsed = True
        if text == "":
            self.is_translated = True

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
        temp_block_content = [line for line in temp_block_content if line.strip() != ""]
        # add an empty line at the end
        temp_block_content.append("")

        # note the result
        self.block_content_translated = temp_block_content
        self.is_translated = True
        return self.block_content_translated

    def is_narration(self):
        """return if the block is narration"""
        return self.speaker_original == "" or self.speaker_original == "narration"

    def is_empty(self):
        """return if the block is empty"""
        return self.is_parsed and self.text_original == ""

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
