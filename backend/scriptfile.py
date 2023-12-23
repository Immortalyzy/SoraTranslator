""" game file class, every instance is a script file of the game """

import datetime
import os
from .logger import log_message
from .constants import DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY, RAW_TEXT_DIRECTORY, DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY
from .constants import LogLevel
from .block import Block


class ScriptFile:
    """The GameFile class defines a script file and info around it, the class provides a framework for integration actions defined in the game folders"""

    # a list of blocks in the file, will be filled when parsing
    blocks = []
    # these two are used to record the non-block content in the file
    non_block_string_between_blocks = []
    block_number_for_non_block_string = []

    def __init__(self, file_path):

        self.original_file_path = file_path
        self.script_file_path = file_path # this avoids error when forgot to use from_originalfile
        self.text_file_path = ""  # the path of the text file in .csv
        self.translated_script_file_path = ""

        self.read_date = datetime.datetime.now()

        # file type
        self.file_type = "content"
        self.original_package = ""  # the package the file is in

        # set to true if ALL the text in the file is translated
        self.is_translated = False

        # if file type is content, then it should content following variables for eaiser integration
        # at the end of certain files there will be a "jump" action that indicates the name of next file
        self.next_script_file_name = ""

        # ordinary info, will add here as generally needed

    @classmethod
    def from_originalfile(cls, file_path):
        """create a game file instance from a file path"""
        scriptfile = cls(file_path)
        scriptfile.script_file_path = file_path
        return scriptfile

    @classmethod
    def from_textfile(cls, file_path):
        """create a game file instance from a file path"""
        scriptfile = cls(file_path)
        # the script file path is undefined if it is read from a text file, this is usually used for translators
        scriptfile.script_file_path = "undefined"
        scriptfile.text_file_path = file_path
        # the file type is content if it is read from a text file
        scriptfile.file_type = "content"
        # the original package is the directory name of the file (only the last part)
        scriptfile.original_package = os.path.basename(os.path.dirname(file_path))
        # check file existence
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file {file_path} does not exist")
        with open(file_path, "r", encoding="utf_16") as file:
            lines = file.readlines()
        for line in lines:
            scriptfile.blocks.append(Block.from_csv_line(line))

        # verifications
        # if all the blocks are translated, then the file is translated
        scriptfile.is_translated = all(block.is_translated for block in scriptfile.blocks)

        return scriptfile

    def create_entry_in_scriptlistcsv(self):
        """create a entry in the scriptlist.csv"""
        entry = ""
        entry += self.script_file_path + ", "
        entry += self.text_file_path + ", "
        entry += self.file_type + ", "
        entry += str(int(self.is_translated)) + ", "
        entry += self.original_package + ", "


        entry += str(self.read_date) + "\n"
        return entry

    def parse(self, parse_file_function, parse_block_function):
        """ parse the script file """
        # parse the file and save the blocks
        self.blocks, self.non_block_string_between_blocks, self.block_number_for_non_block_string = parse_file_function(self)

        # parse all the blocks
        for block in self.blocks:
            block.parse(parse_block_function)

    def generate_textfile(self, text_file_path="", replace=False, update=False):
        """
        Generate a text file based on the script file using the provided parser file.

        Args:
            parser_file (str): The path to the parser python (.py) file.
            text_file_path (str, optional): The path to the text file. If not provided, a default path will be generated based on the script file path. Defaults to "".
            replace (bool, optional): Whether to replace an existing text file if it already exists. Defaults to False.
            update (bool, optional): Whether to update an existing text file if it already exists. Defaults to False.

        Returns:
            bool: True if the text file was generated successfully, False otherwise.
        """

        # Create the text filepath if not provided
        if text_file_path.strip() == "" and self.text_file_path.strip() == "":
            # get the base name of the file without the extension
            file_name = os.path.basename(self.script_file_path)
            file_name = os.path.splitext(file_name)[0]
            # remove file extension from original package
            relative_path = os.path.relpath(self.script_file_path, RAW_TEXT_DIRECTORY)
            text_file_path = os.path.join(DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY, relative_path)
            # change the extension to .csv
            text_file_path = os.path.splitext(text_file_path)[0] + ".csv"
            self.text_file_path = text_file_path

        # get the directory of the text file
        destination_directory = os.path.dirname(self.text_file_path)
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory, exist_ok=True)

        lines_wroten = 0
        # check if the file exists
        if os.path.exists(self.text_file_path):
            if replace:
                os.remove(self.text_file_path)
            else:
                if update:
                    if self.check_coherence_with_textfile():
                        self.update_from_textfile()
                    else:
                        log_message(f"Text file {self.text_file_path} is not coherent with the script file, cannot update")
                        return 1 # error
                else:
                    return 1 # error


        # create the text file
        with open(self.text_file_path, "w", encoding="utf_16") as file:
            for block in self.blocks:
                lines_wroten += 1
                file.write(block.to_csv_line() + "\n")

        log_message(f"Text file {self.text_file_path} created, {lines_wroten} lines wroten")
        return lines_wroten == 0

    def update_from_textfile(self) -> bool:
        """ update the content (translation) of the script file from the text file """
        # check if the file exists
        if not os.path.exists(self.text_file_path):
            log_message(f"Text file {self.text_file_path} does not exist, cannot update", log_level=LogLevel.ERROR)
            return False
        with open(self.text_file_path, "r", encoding="utf_16") as file:
            lines = file.readlines()
        # implement verification (total lines, etc.)
        if len(lines) != len(self.blocks):
            log_message(f"Text file {self.text_file_path} is not coherent with the script file, cannot update", log_level=LogLevel.ERROR)
            return False
        # record the translation information in the text file and write them to blocks
        for i, line in enumerate(lines):
            block = Block.from_csv_line(line)
            # verify line information
            if block.text_original != self.blocks[i].text_original:
                log_message(f"Line {i+1} in text file {self.text_file_path} does not match the script file, cannot update", log_level=LogLevel.ERROR)
                return False
            self.blocks[i].text_translated = block.text_translated
            self.blocks[i].speaker_translated = block.speaker_translated if block.speaker_translated != "" else self.blocks[i].speaker_original

        return True


    def check_coherence_with_textfile(self, text_file_path = None):
        """ check if the script file is coherent with the text file """
        text_file_path = self.text_file_path if text_file_path is None else text_file_path
        return True

    def generate_translated_rawfile(self, replace=False):
        """ generate a translated file from memory """
        # if no translated file path is provided, generate one
        if self.translated_script_file_path == "":
            # get the base name of the file without the extension
            file_name = os.path.basename(self.script_file_path)
            file_name = os.path.splitext(file_name)[0]
            # remove file extension from original package
            relative_path = os.path.relpath(self.script_file_path, RAW_TEXT_DIRECTORY)
            translated_script_file_path = os.path.join(DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY, relative_path)
            self.translated_script_file_path = translated_script_file_path

        # recreate the rawtext structure, inserting non-block content
        # todo: implement non-block string
        for block in self.blocks:
            block.generate_full_rawblock()
            # write to file

        # get the directory of the text file
        destination_directory = os.path.dirname(self.translated_script_file_path)
        if not os.path.exists(destination_directory):
            os.makedirs(destination_directory, exist_ok=True)

        lines_wroten = 0
        # check if the file exists
        if os.path.exists(self.translated_script_file_path):
            if replace:
                os.remove(self.translated_script_file_path)
            else:
                log_message(f"Translated script file {self.translated_script_file_path} already exists, skip creation", log_level=LogLevel.WARNING)
                return 1

        # create the text file
        with open(self.translated_script_file_path, "w", encoding="utf_16") as file:
            for block in self.blocks:
                lines_wroten += 1
                file.write("\n".join(block.block_content_translated) + "\n")

        log_message(f"Text file {self.translated_script_file_path} created, {lines_wroten} lines wroten")
        return lines_wroten == 0




    def is_system_file(self):
        """ return if is system file"""
        return self.file_type == "system"
    def is_content_file(self):
        """ return if is content file"""
        return self.file_type == "content"
    def is_to_translate(self):
        """ return if is to translate file"""
        return self.is_content_file() and not self.is_translated


def initiate_script_filelist(listfilepath, replace=False):
    """initiate the script file list"""
    # check if the file exists
    if os.path.exists(listfilepath):
        if replace:
            os.remove(listfilepath)
        else:
            print("script file list already exists, skip initiation")
            return

    with open(listfilepath, "w", encoding="utf_16") as file:
        file.write("script_file_path, text_file_path, file_type, is_translated, original_package, read_date\n")

def update_script_filelist(listfilepath, filelist):
    """update the script file list"""
    if not os.path.exists(listfilepath):
        print("script file list does not exist, creating a new one")
        initiate_script_filelist(listfilepath)
    for gamefile in filelist:
        with open(listfilepath, "a", encoding="utf_16") as file:
            file.write(gamefile.create_entry_in_scriptlistcsv())
