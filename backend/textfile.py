"""game file class, every instance is a script file of the game"""

import datetime
import os
import json
from typing import List
from logging import getLogger

from block import Block, split_selection_text

logger = getLogger(__name__)
PROPERTY_LINE_LENGTH = 8


class TextFile:
    """A text file is a file that is ready to be translated, it contains the original text and the translated text.
    The core information of text files are stored in a csv file, the data in the class is sotred in Block instances.
    """

    def __init__(self):
        # a list of blocks in the file, will be filled when parsing
        self.blocks: List[Block] = []
        self.is_empty = False

        # list of string for the name of characters appearing in the file
        self.name_list_original = []
        self.name_list_translated = []
        self.name_list_count = []  # count of each name

        # sub name usually is the name of the part when parsing a big file
        # if empty, the sub text file generated will be assigned a name automatically
        self.subname = ""

        self.read_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_file_path = ""  # will be generated when generating text file
        self.script_file_path = ""  # will be changed if the instance is created during parsing a script file
        self.original_package = ""  # will be changed if the instance is created during parsing a script file

        # file type
        self.file_type = "content"

        # set to true if ALL the text in the file is translated
        self.is_translated = False
        self.need_manual_fix = False
        self.translation_percentage = 0.0

        # ordinary info, will add here as generally needed
        # translation info, will store the translation status (including how the translation was performed and which part caused problem)
        self.info = {"translation_info": "not translated yet"}

    @classmethod
    def from_blocks(cls, blocks: List[Block]):
        """create a game file instance from a file path"""
        textfile = cls()
        textfile.blocks = blocks
        textfile.is_empty = len(textfile.translation_rows()) == 0

        # generate the name list
        textfile.generate_name_list()

        return textfile

    def exportable_blocks(self) -> List[Block]:
        """return the subset of blocks that should be serialized for translation"""
        return [block for block in self.blocks if block.is_exportable()]

    def translation_rows(self) -> List[Block]:
        """return the rows exposed to translators, flattening selection choices"""
        rows = []
        for block in self.exportable_blocks():
            if block.is_selection() and block.selection_original:
                rows.extend(block.create_selection_row(i) for i in range(len(block.selection_original)))
            else:
                rows.append(block)
        return rows

    def generate_name_list(self):
        """count the speaker names in the text file"""
        # count the names appeared in the textfile
        names = []
        counts = []
        for block in self.blocks:
            if block.speaker_original == "":
                continue
            if block.speaker_original not in names:
                names.append(block.speaker_original)
                counts.append(1)
            else:
                counts[names.index(block.speaker_original)] += 1

        self.name_list_original = names
        self.name_list_count = counts
        # generate a list of empty strings with the same length as names
        self.name_list_translated = [""] * len(names)

    @classmethod
    def from_textfile(cls, file_path):
        """create a game file instance from a file path"""
        textfile = cls()
        textfile.text_file_path = file_path
        # the original package is the directory name of the file (only the last part)
        # textfile.original_package = os.path.basename(os.path.dirname(file_path))
        # check file existence
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file {file_path} does not exist")
        with open(file_path, "r", encoding="utf_8") as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if i < PROPERTY_LINE_LENGTH:
                    # record the property information from file
                    textfile.to_property(line)
                    # skip the first few lines
                    continue
                # cannot call stirp() here because the line may be empty
                block = Block.from_csv_line(line)
                if block.is_exportable():
                    textfile.blocks.append(block)
        # print(f"Text file {file_path} loaded, {len(textfile.blocks)} blocks found")

        # verifications
        # if all the blocks are translated, then the file is translated
        # textfile.is_translated = all(
        #     block.is_translated for block in textfile.blocks
        # )
        # ! setting a file to translated should be done by the translator

        textfile.generate_name_list()

        return textfile

    def to_json(self):
        """create a json object for usage in frontend"""
        data = {}
        # record the property information from file
        data["script_file_path"] = self.script_file_path
        data["text_file_path"] = self.text_file_path
        data["read_date"] = self.read_date
        data["file_type"] = self.file_type
        data["original_package"] = self.original_package
        data["is_translated"] = self.is_translated
        data["need_manual_fix"] = self.need_manual_fix
        data["translation_percentage"] = self.translation_percentage
        data["translation_info"] = self.info["translation_info"]
        blocks_json = []
        for block in self.translation_rows():
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

    def generate_galtransl_json(self, dest="", replace=False):
        """Create a json file for Galtransl"""
        if self.is_empty:
            logger.info(f"Skipping {self.text_file_path} as it is empty")
            return 1
        # Create the text filepath if not provided
        if dest == "":
            # use the same path as the text file, but with a json extension
            dest = self.text_file_path.append(".json")

        # start creating the json file
        data = [{"name": block.speaker_original, "message": block.text_original} for block in self.translation_rows()]

        # write the json file, replace if needed
        # check if the file exists
        if os.path.exists(dest):
            if replace:
                os.remove(dest)
            else:
                logger.warning(f"Skipping {dest} as it already exists")
                return 1
        with open(dest, "w", encoding="utf_8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        return 0

    def update_from_galtransl_json(self, json_file="") -> bool:
        """update the content (translation) of the textfile from a galtransl output json"""
        # check if the file is empty
        if self.is_empty:
            logger.info(f"Skipping {self.text_file_path} as it is empty")
            return True

        if json_file == "":
            json_file = self.text_file_path + ".json"

        # check if the file exists
        if not os.path.exists(json_file):
            logger.error(f"Text file {json_file} does not exist, cannot update")
            return False
        with open(json_file, "r", encoding="utf_8") as file:
            data = json.load(file)
        # implement verification (total lines, etc.)
        translation_rows = self.translation_rows()
        if len(data) == len(translation_rows):
            for i, entry in enumerate(data):
                if translation_rows[i].speaker_original == "" and entry["name"] != "":
                    logger.warning(
                        f"Entry {i+1} in json file {json_file} does not match the script file, result might be incorrect"
                    )
                self._apply_json_entry(translation_rows[i], entry)
            self.is_translated = True
            return True

        exportable_blocks = self.exportable_blocks()
        if len(data) != len(exportable_blocks):
            logger.error(f"Json output file {json_file} is not coherent with the script file, cannot update")
            return False

        for i, entry in enumerate(data):
            if exportable_blocks[i].speaker_original == "" and entry["name"] != "":
                logger.warning(
                    f"Entry {i+1} in json file {json_file} does not match the script file, result might be incorrect"
                )
            if exportable_blocks[i].is_selection():
                translated_selections = split_selection_text(entry["message"])
                if translated_selections and len(translated_selections) != len(exportable_blocks[i].selection_original):
                    logger.error(f"Selections not matched for block {exportable_blocks[i].block_name}")
                    return False
            self._apply_json_entry(exportable_blocks[i], entry)

        self.is_translated = True
        return True

    def update_name_translation(self, name_mapping: dict[str, str]) -> int:
        """
        Update speaker translated names using a global mapping.

        Rules:
        - Empty replacement means no replacement (skip).
        - Only rows with existing speaker_original are considered.
        """
        if not name_mapping:
            return 0

        updated_blocks = 0
        for block in self.blocks:
            speaker_original = block.speaker_original.strip()
            if speaker_original == "":
                continue
            if speaker_original not in name_mapping:
                continue

            translated_name = str(name_mapping[speaker_original]).strip()
            if translated_name == "":
                continue
            if block.speaker_translated == translated_name:
                continue
            block.speaker_translated = translated_name
            updated_blocks += 1

        self.generate_name_list()
        self.name_list_translated = [
            str(name_mapping.get(name, "")).strip() for name in self.name_list_original
        ]
        return updated_blocks

    def generate_textfile(
        self,
        dest="",
        replace=False,
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
        # check if the file is empty
        if self.is_empty:
            logger.info(f"Skipping {self.text_file_path} as it is empty")
            return 1

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
                logger.warning(f"Skipping {self.text_file_path} as it already exists")
                return 1  # error

        # create the text file
        ## save file information
        with open(self.text_file_path, "w", encoding="utf_8") as file:
            file.write(self.from_property("script_file_path") + "\n")
            file.write(self.from_property("text_file_path") + "\n")

            file.write(self.from_property("read_date") + "\n")

            file.write(self.from_property("file_type") + "\n")
            file.write(self.from_property("original_package") + "\n")

            file.write(self.from_property("is_translated") + "\n")
            file.write(self.from_property("need_manual_fix") + "\n")
            file.write(self.from_property("translation_percentage") + "\n")
            lines_wroten += PROPERTY_LINE_LENGTH
            for block in self.translation_rows():
                lines_wroten += 1
                file.write(block.to_csv_line() + "\n")

        logger.info(f"Text file {self.text_file_path} created, {lines_wroten} lines wroten")
        return lines_wroten == 0

    def update_from_textfile(self) -> bool:
        """update the content (translation) of the script file from the text file"""
        # check if the file is empty
        if self.is_empty:
            logger.info(f"Skipping {self.text_file_path} as it is empty")
            return True

        # check if the file exists
        if not os.path.exists(self.text_file_path):
            logger.error(f"Text file {self.text_file_path} does not exist, cannot update")
            return False
        with open(self.text_file_path, "r", encoding="utf_8") as file:
            lines = file.readlines()
        file_blocks = []
        # record the translation information in the text file and write them to blocks
        for i, line in enumerate(lines):
            if i < PROPERTY_LINE_LENGTH:
                # record the property information from file
                self.to_property(line)
                # skip the first few lines
                continue
            block = Block.from_csv_line(line)
            if block.is_exportable():
                file_blocks.append(block)

        translation_rows = self.translation_rows()
        if len(file_blocks) == len(translation_rows):
            for j, block in enumerate(file_blocks):
                if block.text_original.strip() != translation_rows[j].text_original.strip():
                    logger.error(
                        f"Line {j+1} in text file {self.text_file_path} does not match the script file, cannot update"
                    )
                self._apply_block_update(translation_rows[j], block)
            return True

        exportable_blocks = self.exportable_blocks()
        if len(file_blocks) != len(exportable_blocks):
            logger.error(f"Text file {self.text_file_path} is not coherent with the script file, cannot update")
            return False

        for j, block in enumerate(file_blocks):
            if block.text_original.strip() != exportable_blocks[j].text_original.strip():
                logger.error(
                    f"Line {j+1} in text file {self.text_file_path} does not match the script file, cannot update"
                )
                # WARING
                # return False
            if not self._is_valid_block_update(exportable_blocks[j], block):
                return False

        for j, block in enumerate(file_blocks):
            self._apply_block_update(exportable_blocks[j], block)

        return True

    @staticmethod
    def _is_valid_block_update(target_block: Block, source_block: Block) -> bool:
        """Validate a CSV row against the already-parsed in-memory block."""
        if not target_block.is_selection():
            return True

        translated_selections = split_selection_text(source_block.text_translated)
        if translated_selections and len(translated_selections) != len(target_block.selection_original):
            logger.error(f"Selections not matched for block {target_block.block_name}")
            return False

        return True

    @staticmethod
    def _normalized_selection_translations(block: Block) -> list[str]:
        """return a selection translation list sized to the original option count"""
        translations = list(block.selection_translated[: len(block.selection_original)])
        if len(translations) < len(block.selection_original):
            translations.extend([""] * (len(block.selection_original) - len(translations)))
        return translations

    @classmethod
    def _apply_json_entry(cls, target_block: Block, entry: dict[str, str]) -> None:
        """Apply one json translation entry to a parsed target block or synthetic row."""
        source_block = Block.from_csv_line(
            [
                target_block.block_name,
                target_block.speaker_original,
                target_block.text_original,
                entry["name"],
                entry["message"],
                "Yes" if entry["message"] else "No",
                "",
                "Undefined or manual",
            ]
        )
        cls._apply_block_update(target_block, source_block)

    @classmethod
    def _apply_block_update(cls, target_block: Block, source_block: Block) -> None:
        """Apply a CSV/json row update to either a real block or a synthetic selection row."""
        if target_block.is_selection_row():
            parent_block = target_block.selection_parent
            if parent_block is None or target_block.selection_index is None:
                return

            parent_block.selection_translated = cls._normalized_selection_translations(parent_block)
            parent_block.selection_translated[target_block.selection_index] = source_block.text_translated
            parent_block.text_translated = "/".join(parent_block.selection_translated)
            parent_block.is_translated = any(text.strip() for text in parent_block.selection_translated)
            if source_block.text_translated:
                parent_block.translation_date = source_block.translation_date
                parent_block.translation_engine = source_block.translation_engine
            return

        if target_block.is_selection():
            target_block.selection_translated = split_selection_text(source_block.text_translated)

        target_block.text_translated = source_block.text_translated
        target_block.speaker_translated = (
            source_block.speaker_translated if source_block.speaker_translated != "" else target_block.speaker_original
        )
        target_block.is_translated = True if source_block.text_translated != "" else False
        if target_block.is_translated:
            target_block.translation_date = source_block.translation_date
            target_block.translation_engine = source_block.translation_engine

    def check_coherence_with_textfile(self, text_file_path=None):
        """check if the script file is coherent with the text file"""
        text_file_path = self.text_file_path if text_file_path is None else text_file_path
        return True

    def is_Hcontent(self):
        """return if is dangerous file"""
        return self.file_type == "Hcontent"

    def is_to_translateH(self):
        """return if is dangerous file"""
        return self.is_Hcontent() and not self.is_translated

    def is_to_translate(self):
        """return if is to translate file"""
        return self.is_Hcontent() and not self.is_translated

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

    with open(listfilepath, "w", encoding="utf_8") as file:
        file.write(
            "script_file_path\t"
            "text_file_path\t"
            "file_type\t"
            "is_translated\t"
            "need_manual_fix\t"
            "translation_percentage\t"
            "original_package\t"
            "read_date\n"
        )
