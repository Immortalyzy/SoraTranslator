""" game file class, every instance is a script file of the game """

import datetime
import os
from logger import log_message
from constants import LogLevel
from block import Block
from textfile import TextFile


class ScriptFile:
    """The GameFile class defines a script file and info around it, the class provides a framework for integration actions defined in the game folders"""

    def __init__(self, file_path):
        # a list of all blocks in the file, will be filled when parsing
        self.blocks: list(Block) = []
        # these two are used to record the non-block content in the file
        self.non_block_string_between_blocks = []
        self.block_number_for_non_block_string = []

        # this avoids error when forgot to use from_originalfile
        self.original_file_path = file_path
        self.script_file_path = file_path

        # separate the file into multiple text files
        # each text file contain a reasonable amount of blocks for translation and editing
        self.textfiles = []
        self.blocks_count_in_textfile = []
        self.translated_script_file_path = ""

        self.read_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # file type
        self.file_type = "content"
        self.original_package = ""  # the package the file is in

        # set to true if ALL the text in the file is translated
        # !should be deprecated
        self.is_translated = False
        self.need_manual_fix = False
        self.translation_percentage = 0.0

        # if file type is content, then it should content following variables for eaiser integration
        # at the end of certain files there will be a "jump" action that indicates the name of next file
        self.next_script_file_name = ""

        # ordinary info, will add here as generally needed
        # translation info, will store the translation status (including how the translation was performed and which part caused problem)
        self.info = {"translation_info": "not translated yet"}

    @classmethod
    def from_originalfile(cls, file_path):
        """create a game file instance from a file path"""
        scriptfile = cls(file_path)
        scriptfile.script_file_path = file_path
        return scriptfile

    def to_json(self):
        """create a json object for usage in frontend"""
        data = {}
        # record the property information from file
        data["original_file_path"] = self.original_file_path
        data["script_file_path"] = self.script_file_path
        data["translated_script_file_path"] = self.translated_script_file_path
        data["read_date"] = self.read_date
        data["file_type"] = self.file_type
        data["original_package"] = self.original_package
        data["translation_percentage"] = self.translation_percentage
        data["translation_info"] = self.info["translation_info"]
        blocks_json = []
        for block in self.blocks:
            blocks_json.append(block.to_json())
        data["blocks"] = blocks_json
        return data

    def create_entry_in_scriptlistcsv(self):
        """create a entry in the scriptlist.csv"""
        entry = ""
        entry += self.script_file_path + "\t"
        if len(self.textfiles) == 1:
            entry += self.textfiles[0].text_file_path + "\t"
        else:
            entry += f"{len(self.textfiles):d} files" + "\t"
        entry += self.file_type + "\t"
        entry += str(int(self.is_translated)) + "\t"
        entry += str(int(self.need_manual_fix)) + "\t"
        entry += f"{self.translation_percentage:.1f}" + "\t"
        entry += self.original_package + "\t"

        entry += str(self.read_date) + "\n"
        return entry

    def parse(
        self,
        parse_file_function,
        parse_block_function,
        maximum_block_count=100,
        force_single=False,
    ):
        """parse the script file"""
        # parse the file and save the blocks
        parse_file_function(self)

        # parse all the blocks
        for block in self.blocks:
            block.parse(parse_block_function)

        # if the parser function didn't separate the file into textfiles
        # then separate the file into textfiles automatically
        if len(self.textfiles) == 0 and (not force_single):
            # separate the blocks
            subblocks = [
                self.blocks[i : i + maximum_block_count]
                for i in range(0, len(self.blocks), maximum_block_count)
            ]
            for i, subblock in enumerate(subblocks):
                textfile = TextFile.from_blocks(subblock)
                textfile.original_package = self.original_package
                textfile.script_file_path = self.script_file_path
                self.textfiles.append(textfile)
                self.blocks_count_in_textfile.append(len(subblock))

    def generate_textfiles(
        self,
        dest="",
        replace=False,
        update=False,
    ):
        """
        Generate a text file based on the script file using the provided parser file.

        Args:
            dest (str, optional): The destination folder of the text file. Defaults to "".
            replace (bool, optional): If the text file already exists, replace it. Defaults to False.
            update (bool, optional): If the text file already exists, update it. Defaults to False.

        Returns:
            bool: True if the text file was generated successfully, False otherwise.
        """
        for i, textfile in enumerate(self.textfiles):
            # Create the text filepath if not provided
            if dest == "":
                raise ValueError("In latest version you have to give a text file path")
            # generate the paths for the text file
            if i == 0:
                textfile.text_file_path = dest
            else:
                textfile.text_file_path = dest[:-4] + f"_sorasub{i:d}" + dest[-4:]
            # generate the text file
            textfile.generate_textfile(replace=replace, update=update)

        return 1

    def update_from_textfiles(self, strict_verfication=False) -> bool:
        """update the content (translation) of the script file from the text file"""
        for textfile in self.textfiles:
            textfile.update_from_textfile()

        # repalce the blocks with the updated blocks
        temp_blocks = []
        for textfile in self.textfiles:
            temp_blocks += textfile.blocks
        # check if the blocks are the same
        if len(temp_blocks) != len(self.blocks):
            print("block number not the same")
            return False
        if strict_verfication:
            for i, block in enumerate(temp_blocks):
                if block.block_name != self.blocks[i].block_name:
                    return False
        self.blocks = temp_blocks

        return True

    def generate_translated_rawfile(self, dest="", replace=False):
        """generate a translated file from memory"""
        # if no translated file path is provided, generate one
        if self.translated_script_file_path == "" and dest == "":
            raise ValueError(
                "In latest version you have to give a translated file path"
            )
        if dest != "":
            self.translated_script_file_path = dest

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
                log_message(
                    f"Replacing translated script file {self.translated_script_file_path}",
                    log_level=LogLevel.WARNING,
                )
                os.remove(self.translated_script_file_path)
            else:
                log_message(
                    f"Translated script file {self.translated_script_file_path} already exists, skip creation",
                    log_level=LogLevel.WARNING,
                )
                return 1

        # create the raw file
        with open(self.translated_script_file_path, "w", encoding="utf_16") as file:
            for block in self.blocks:
                lines_wroten += 1
                file.write("\n".join(block.block_content_translated) + "\n")

        log_message(
            f"Text file {self.translated_script_file_path} created, {lines_wroten} lines wroten"
        )
        return lines_wroten == 0

    def is_system_file(self):
        """return if is system file"""
        return self.file_type == "system"

    def is_content_file(self):
        """return if is content file"""
        return self.file_type == "content"

    def is_Hcontent(self):
        """return if is dangerous file"""
        return self.file_type == "Hcontent"

    def is_to_translateH(self):
        """return if is dangerous file"""
        return self.is_Hcontent() and not self.is_translated

    def is_to_translate(self):
        """return if is to translate file"""
        return (self.is_content_file() or self.is_Hcontent()) and not self.is_translated

    def from_property(self, property_name):
        """convert between a property of the script file and a csv line"""
        if property_name == "is_translated" or property_name == "need_manual_fix":
            result = True if getattr(self, property_name) else False
        elif property_name == "translation_percentage":
            result = f"{getattr(self, property_name):.2f}"
        elif property_name == "info":
            # generate a long info line containing all info
            print("not implemented yet")
        else:
            result = getattr(self, property_name)
        return property_name + "\t" + str(result)

    def to_property(self, csv_line):
        """convert between a property of the script file and a csv line"""
        data = csv_line.split("\t")
        property_name = data[0].strip()
        true_list = ["TRUE", "True", "true", "1", "Yes", "yes", "YES"]
        if property_name == "is_translated" or property_name == "need_manual_fix":
            result = True if data[1].strip() in true_list else False
            setattr(self, property_name, result)
        elif property_name == "translation_percentage":
            setattr(self, property_name, float(data[1].strip()))
        else:
            setattr(self, property_name, data[1].strip())


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
        file.write(
            "script_file_path\ttext_file_path\tfile_type\tis_translated\tneed_manual_fix\ttranslation_percentage\toriginal_package\tread_date\n"
        )


def update_script_filelist(listfilepath, filelist, replace=True):
    """update the script file list"""
    if not os.path.exists(listfilepath):
        print("script file list does not exist, creating a new one")
        initiate_script_filelist(listfilepath)
    if replace:
        # remove the old file
        if os.path.exists(listfilepath):
            os.remove(listfilepath)
    for gamefile in filelist:
        with open(listfilepath, "a", encoding="utf_16") as file:
            file.write(gamefile.create_entry_in_scriptlistcsv())


def from_script_filelist(listfilepath: str) -> list:
    """create a list of script files from a script file list"""
    script_file_list = []
    with open(listfilepath, "r", encoding="utf_16") as file:
        lines = file.readlines()
    for line in lines:
        if line.startswith("script_file_path"):
            continue
        line = line.strip()
        if line == "":
            continue
        line = line.split("\t")
        script_file = ScriptFile.from_originalfile(line[0])
        script_file.file_type = line[2]
        script_file.is_translated = bool(int(line[3]))
        script_file.need_manual_fix = bool(int(line[4]))
        script_file.translation_percentage = float(line[5])
        script_file.original_package = line[6]
        script_file.read_date = datetime.datetime.strptime(
            line[7], "%Y-%m-%d %H:%M:%S.%f"
        )
        script_file_list.append(script_file)
    return script_file_list
