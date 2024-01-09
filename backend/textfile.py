""" game file class, every instance is a script file of the game """

import datetime
import os
from logger import log_message
from constants import LogLevel
from block import Block

PROPERTY_LINE_LENGTH = 10


class TextFile:
    """A text file is a file that is ready to be translated, it contains the original text and the translated text.
    The core information of text files are stored in a csv file, the data in the class is sotred in Block instances.
    """

    def __init__(self, file_path):
        # a list of blocks in the file, will be filled when parsing
        self.blocks = []
        # these two are used to record the non-block content in the file
        self.non_block_string_between_blocks = []
        self.block_number_for_non_block_string = []

        # path information
        self.original_file_path = file_path
        self.script_file_path = (
            file_path  # this avoids error when forgot to use from_originalfile
        )
        self.text_file_path = ""  # the path of the text file in .csv
        self.translated_script_file_path = ""

        self.read_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # file type
        self.file_type = "content"
        self.original_package = ""  # the package the file is in

        # set to true if ALL the text in the file is translated
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

    @classmethod
    def from_textfile(cls, file_path):
        """create a game file instance from a file path"""
        scriptfile = cls(file_path)
        # the script file path is undefined if it is read from a text file, this is usually used for translators
        scriptfile.script_file_path = ""
        scriptfile.text_file_path = file_path
        # the file type is content if it is read from a text file
        scriptfile.file_type = "content"
        # the original package is the directory name of the file (only the last part)
        # scriptfile.original_package = os.path.basename(os.path.dirname(file_path))
        # check file existence
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file {file_path} does not exist")
        with open(file_path, "r", encoding="utf_16") as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if i < PROPERTY_LINE_LENGTH:
                    # record the property information from file
                    scriptfile.to_property(line)
                    # skip the first few lines
                    continue
                # cannot call stirp() here because the line may be empty
                scriptfile.blocks.append(Block.from_csv_line(line))
        print(f"Text file {file_path} loaded, {len(scriptfile.blocks)} blocks found")

        # verifications
        # if all the blocks are translated, then the file is translated
        # scriptfile.is_translated = all(
        #     block.is_translated for block in scriptfile.blocks
        # )
        # ! setting a file to translated should be done by the translator

        return scriptfile

    def to_json(self):
        """create a json object for usage in frontend"""
        data = {}
        # record the property information from file
        data["original_file_path"] = self.original_file_path
        data["script_file_path"] = self.script_file_path
        data["text_file_path"] = self.text_file_path
        data["translated_script_file_path"] = self.translated_script_file_path
        data["read_date"] = self.read_date
        data["file_type"] = self.file_type
        data["original_package"] = self.original_package
        data["is_translated"] = self.is_translated
        data["need_manual_fix"] = self.need_manual_fix
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
        entry += self.text_file_path + "\t"
        entry += self.file_type + "\t"
        entry += str(int(self.is_translated)) + "\t"
        entry += str(int(self.need_manual_fix)) + "\t"
        entry += f"{self.translation_percentage:.1f}" + "\t"
        entry += self.original_package + "\t"

        entry += str(self.read_date) + "\n"
        return entry

    def parse(self, parse_file_function, parse_block_function):
        """parse the script file"""
        # parse the file and save the blocks
        (
            self.blocks,
            self.non_block_string_between_blocks,
            self.block_number_for_non_block_string,
        ) = parse_file_function(self)

        # parse all the blocks
        for block in self.blocks:
            block.parse(parse_block_function)

    def generate_textfile(
        self,
        dest="",
        replace=False,
        update=False,
    ):
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
        if self.text_file_path == "" and dest == "":
            raise ValueError("In latest version you have to give a text file path")
        if dest != "":
            # if dest is a file path, then use it
            self.text_file_path = dest

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
                        log_message(
                            f"Text file {self.text_file_path} is not coherent with the script file, cannot update"
                        )
                        return 1  # error
                else:
                    log_message(
                        f"Skipping {self.text_file_path} as it already exists",
                        log_level=LogLevel.WARNING,
                    )
                    return 1  # error

        # create the text file
        ## save file information
        with open(self.text_file_path, "w", encoding="utf_16") as file:
            file.write(self.from_property("original_file_path") + "\n")
            file.write(self.from_property("script_file_path") + "\n")
            file.write(self.from_property("text_file_path") + "\n")
            file.write(self.from_property("translated_script_file_path") + "\n")

            file.write(self.from_property("read_date") + "\n")

            file.write(self.from_property("file_type") + "\n")
            file.write(self.from_property("original_package") + "\n")

            file.write(self.from_property("is_translated") + "\n")
            file.write(self.from_property("need_manual_fix") + "\n")
            file.write(self.from_property("translation_percentage") + "\n")
            lines_wroten += PROPERTY_LINE_LENGTH
            for block in self.blocks:
                lines_wroten += 1
                file.write(block.to_csv_line() + "\n")

        log_message(
            f"Text file {self.text_file_path} created, {lines_wroten} lines wroten"
        )
        return lines_wroten == 0

    def update_from_textfile(self) -> bool:
        """update the content (translation) of the script file from the text file"""
        # check if the file exists
        if not os.path.exists(self.text_file_path):
            log_message(
                f"Text file {self.text_file_path} does not exist, cannot update",
                log_level=LogLevel.ERROR,
            )
            return False
        with open(self.text_file_path, "r", encoding="utf_16") as file:
            lines = file.readlines()
        # implement verification (total lines, etc.)
        if len(lines) != len(self.blocks) + PROPERTY_LINE_LENGTH:
            log_message(
                f"Text file {self.text_file_path} is not coherent with the script file, cannot update",
                log_level=LogLevel.ERROR,
            )
            return False
        # record the translation information in the text file and write them to blocks
        for i, line in enumerate(lines):
            if i < PROPERTY_LINE_LENGTH:
                # record the property information from file
                self.to_property(line)
                # skip the first few lines
                continue
            block = Block.from_csv_line(line)
            # verify line information
            j = i - PROPERTY_LINE_LENGTH
            if block.text_original != self.blocks[j].text_original:
                log_message(
                    f"Line {j+1} in text file {self.text_file_path} does not match the script file, cannot update",
                    log_level=LogLevel.ERROR,
                )
                return False
            # update the block, cannot copy because there is no parsing information in "block"
            self.blocks[j].text_translated = block.text_translated
            self.blocks[j].speaker_translated = (
                block.speaker_translated
                if block.speaker_translated != ""
                else self.blocks[j].speaker_original
            )
            # update tanslation information
            self.blocks[j].is_translated = (
                True if block.text_translated != "" else False
            )
            if self.blocks[j].is_translated:
                self.blocks[j].translation_date = block.translation_date
                self.blocks[j].translation_engine = block.translation_engine

        return True

    def check_coherence_with_textfile(self, text_file_path=None):
        """check if the script file is coherent with the text file"""
        text_file_path = (
            self.text_file_path if text_file_path is None else text_file_path
        )
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

        # todo: add dest usage,
        # check if dest is a file path or a directory
        # if dest is a directory, then generate a file path based on the original file path

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
        script_file.text_file_path = line[1]
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
