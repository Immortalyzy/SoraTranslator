""" define the Block class """
#!! csv sperator used is tab "\t"

from .logger import log_message
from .constants import LogLevel


class Block:
    """A block is a unit of text in a script file that controls the text that is shown at one time"""

    # basic info
    is_parsed = False

    # for translation
    is_translated = False  # will also be set to true if the block is empty
    speaker_original = ""
    speaker_translated = ""
    text_original = ""
    text_translated = ""
    block_name_line = ""

    # for integration
    speaker_line = 0
    speaker_start_end = (0, 0)
    text_line = 0
    text_start_end = (0, 0)

    # for translation record
    translation_date = ""
    translation_engine = "Undefined or manual"
    translation_status = "stop"

    def __init__(self, block_name, block_content):
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
        if len(csv_line) < 3:
            raise ValueError("CSV line length not correct")

        block_name = csv_line[0]
        # when reading from csv file, the block content will not be read
        block_content = ""
        block = cls(block_name, block_content)
        # a block read from csv file is always parsed
        block.is_parsed = True

        block.speaker_original = csv_line[1]
        block.text_original = csv_line[2]
        block.speaker_translated = csv_line[3]
        block.text_translated = csv_line[4]

        if csv_line[5] != "Yes" and csv_line[5] != "No":
            log_message(
                f'CSV line {csv_line} has incompatible is_translated entry record. (Accepted record is "Yes" or "No")',
                log_level=LogLevel.WARNING,
            )

        block.is_translated = csv_line[5] == "Yes"
        block.translation_date = csv_line[6]
        block.translation_engine = csv_line[7]
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

    def parse(self, parse_block_function):
        """parse the block"""
        (
            speaker,
            text,
            speaker_line,
            speak_start_end,
            text_line,
            text_start_end,
        ) = parse_block_function(self)
        self.speaker_original = speaker
        self.text_original = text
        self.speaker_line = speaker_line
        self.speaker_start_end = speak_start_end
        self.text_line = text_line
        self.text_start_end = text_start_end

        self.is_parsed = True
        if text == "":
            self.is_translated = True

    def generate_full_rawblock(self) -> str:
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
        # replace the speaker if not empty
        if self.speaker_original.strip() != "":
            temp_block_content[self.speaker_line] = (
                temp_block_content[self.speaker_line][: self.speaker_start_end[0]]
                + self.speaker_translated
                + temp_block_content[self.speaker_line][self.speaker_start_end[1] :]
            )

        # replacing the speaker will change the text positioni if they are on the same line
        if self.speaker_line == self.text_line:
            # shift the text position
            if self.speaker_original.strip() != "":
                self.text_start_end = (
                    self.text_start_end[0]
                    + (len(self.speaker_translated) - len(self.speaker_original)),
                    self.text_start_end[1]
                    + (len(self.speaker_translated) - len(self.speaker_original)),
                )

        # replace the text
        if self.text_original != "" and self.text_translated.strip() != "":
            temp_block_content[self.text_line] = (
                temp_block_content[self.text_line][: self.text_start_end[0]]
                + self.text_translated
                + temp_block_content[self.text_line][self.text_start_end[1] :]
            )

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

    def text_to_translate(self, add_speaker: bool = False):
        """return the text to translate"""
        text = ""
        if add_speaker:
            text += f"{self.speaker_original}: "
        text += self.text_original
        return text

    def __str__(self):
        return f"Block {self.block_name} with {len(self.block_content)} lines"
