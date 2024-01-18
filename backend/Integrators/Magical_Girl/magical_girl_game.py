""" This file defines the functions for dealing with the games from Magical-girl
    Last active game: 漆黒のルナリア ～淫らな館にとらわれる犬耳ロリータ～ on 2012
    Game engine: NScripter
    Text is stored in nscript.dat which defines a lot of things, including the text.
    The prepare_translation function should do the following things:
        1, extract the nscript.dat file,
        2, parse the nscript.dat file, separate the text into parts and save the text to text files
        3, update the script_file_list and to_translate_file_list
    Parameters to prepare:
        1, start line of the main script
"""

import importlib.util
import os
import shutil
from constants import LogLevel
from config import default_config
from game import Game
from scriptfile import ScriptFile, update_script_filelist
from logger import log_message
from ..utils.encoding_fix import fix_allfiles
from .parser import parse_file, parse_block
from ..utils.utilities import NSDEC, NSCMAKE


class MagicalGirlGame(Game):
    """Game class for Chaos_R games."""

    def __init__(self, paths, name="Chaos_R", config=default_config):
        super().__init__(paths=paths, name=name, config=config)
        self.unpacker = NSDEC
        self.packer = NSCMAKE

        # original script file is nscript.dat
        self.original_script_file = ""
        self.script_file = ""

        # encoding fix for Chaos_R
        self.original_encoding = "cp932"
        self.target_encoding = "gbk"

        # temp file info storage
        self.temp_unpack_directory = ""

        # possible first block
        self.first_block = "*n0101"

    @classmethod
    def from_pythonfile(cls, paths, python_file, config=default_config):
        """
        Create an Game object from a python file. This is the recommended way since you can select which files to upzip.
        """
        # verify the existence of the python file
        if not os.path.exists(python_file):
            raise FileNotFoundError("The python file does not exist.")

        # load the variables in the python file
        spec = importlib.util.spec_from_file_location("module.name", python_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "GAME_NAME"):
            name = module.GAME_NAME
        else:
            name = "Chaos_R"

        instance = cls(paths=paths, name=name, config=config)

        # DIRECTORY is required
        instance.directory = module.DIRECTORY

        # script file is required
        instance.original_script_file = os.path.join(
            instance.directory, module.SCRIPT_FILE
        )

        # get original encoding
        if hasattr(module, "ORIGINAL_ENCODING"):
            instance.original_encoding = module.ORIGINAL_ENCODING
        else:
            instance.original_encoding = "cp932"

        # get target encoding
        if hasattr(module, "TARGET_ENCODING"):
            instance.target_encoding = module.TARGET_ENCODING
        else:
            instance.target_encoding = "gbk"

        # get first block
        if hasattr(module, "FIRST_BLOCK"):
            instance.first_block = module.FIRST_BLOCK

        # verify the existence of the directory
        if not os.path.exists(instance.directory):
            raise FileNotFoundError("The directory does not exist.")

        if not os.path.exists(instance.original_script_file):
            raise FileNotFoundError("The script file does not exist.")

        instance.post_init()
        return instance

    def post_init(self):
        """Post init."""
        self.temp_unpack_directory = os.path.join(self.directory, "SoraTranslatorTemp")
        # create temp unpack directory
        self.create_temp_unpack_directory(clear=False)
        # initiate script file list file path
        self.scriptfile_list_file = os.path.join(
            self.temp_unpack_directory, "script_file_list.csv"
        )
        self.to_translate_file_list_file = os.path.join(
            self.temp_unpack_directory, "to_translate_file_list.csv"
        )

    # ==== high level methods ===============================
    def prepare_raw_text(self, replace=False):
        """
        Prepare the raw text for Chaos_R games. This method will put all script files into the SoraTranslator/RawText folder.
        """
        # unpack files, put them in the temp_unpack_directory
        # self.unpack_allfiles(replace=False)

        # copy the raw text to the RawText directory
        # creation of the self.script_file instance
        self.copy_raw_text(replace=replace)

        # fix encoding
        self.fix_encoding()

    def prepare_translation(self, replace=False):
        """
        This function will generate all the files that are required by the translation process.
        """
        # guess file types (chaos-R only)
        self.prepare_raw_text(replace=replace)
        # chaos-R game permits the auto detection of file types
        self.update_script_filelist()

        # update parent class variables
        self.script_file_list.append(self.script_file)
        self.to_translate_file_list.append(self.script_file)
        self.dangerous_file_list.append(self.script_file)
        self.update_to_translate_filelist()

        log_message(
            f"Indentified {len(self.to_translate_file_list)} files to translate. ",
            log_level=LogLevel.INFO,
        )

        # generate text files for all to_translate files
        for script_file in self.to_translate_file_list:
            # parsing
            script_file.parse(
                parse_file_function=parse_file,
                parse_block_function=parse_block,
                start_indicator=self.first_block,
            )
            # generate text file
            # generate the destination path for the text file
            # get the base name of the file without the extension
            file_name = os.path.basename(script_file.script_file_path)
            file_name = os.path.splitext(file_name)[0]
            # remove file extension from original package
            relative_path = os.path.relpath(
                script_file.script_file_path, self.rawtext_directory
            )
            text_path = os.path.join(self.text_directory, relative_path)
            text_path = os.path.splitext(text_path)[0] + ".csv"

            script_file.generate_textfiles(dest=text_path, replace=replace)
        self.update_script_filelist()
        return True

    def copy_raw_text(self, replace=False):
        """copy the raw text from the temp_unpack_directory to the RawText directory
        after running this function, the script_file_path of the ScriptFile instances will be updated to the new location
        """
        # now the scriptfile is "result.txt" in the temp_unpack_directory after unpacking
        current_path = os.path.join(self.temp_unpack_directory, "result.txt")
        full_desitnation_path = os.path.join(self.rawtext_directory, "result.txt")

        # check if the file already exists
        if os.path.exists(full_desitnation_path):
            if replace:
                os.remove(full_desitnation_path)
            else:
                print(f"Skipping {full_desitnation_path} since it already exists.")
                self.script_file = ScriptFile.from_originalfile(full_desitnation_path)
                self.script_file.script_file_path = full_desitnation_path
                self.script_file.original_package = "nscript.dat"
                return
        shutil.copy2(current_path, full_desitnation_path)
        # update the script file information
        self.script_file = ScriptFile.from_originalfile(full_desitnation_path)
        self.script_file.script_file_path = full_desitnation_path
        self.script_file.original_package = "nscript.dat"
        log_message(
            f"{self.script_file.script_file_path} raw text is copied to {self.rawtext_directory}.",
            log_level=LogLevel.INFO,
        )

    def integrate(self):
        """Integrate the text into the game."""
        for script_file in self.to_translate_file_list:
            script_file.update_from_textfiles()

            # generate file destination path
            relative_path = os.path.relpath(
                script_file.script_file_path, self.rawtext_directory
            )
            translated_path = os.path.join(
                self.translated_files_directory, relative_path
            )

            script_file.generate_translated_rawfile(
                dest=translated_path, replace=True, encoding=self.target_encoding
            )

            # get the relative path
            relative_path = os.path.relpath(
                script_file.translated_script_file_path, self.translated_files_directory
            )
            desitnation_path = os.path.join(self.temp_unpack_directory, relative_path)

            # copy the file to the temp folder, overwrite if exists
            shutil.copyfile(script_file.translated_script_file_path, desitnation_path)
        self.repack_all_files()
        return f"For security reasons, please replace the original files with the .xp3 files in {self.temp_unpack_directory}."

    # ==== methods for packeging ==================================================================
    def unpack_allfiles(self, replace=False):
        """unpack all files in the file list to temp_unpack_directory"""
        # unpack all files
        result_file_basename = "result.txt"
        result_file_fullpath = os.path.join(self.directory, result_file_basename)

        # extract the nscript.dat file
        success = self.unpack(
            self.unpacker, self.original_script_file, result_file_fullpath
        )
        if not success:
            raise ValueError("Failed to unpack the nscript file.")

        # check if target directory exists to avoid overwriting
        after_file_name = os.path.join(self.temp_unpack_directory, result_file_basename)
        if os.path.exists(after_file_name):
            if replace:
                # delete the file
                log_message(f"Deleting {after_file_name} since it already exists.")
                os.remove(after_file_name)
            else:
                print(f"Skipping {after_file_name} since it already exists.")
        # move the file to the temp_unpack_directory
        shutil.move(result_file_fullpath, self.temp_unpack_directory)

        # now all the files are unpacked and stored in the temp_unpack_directory
        return

    def repack_all_files(self):
        """repack all files in the temp_unpack_directory, results files will be put under that directory"""
        # create input directory
        temp_nscript_dir = os.path.join(self.temp_unpack_directory, "nscript")

        # copy translated result file to the input directory
        translated_result_file = os.path.join(
            self.translated_files_directory, "result.txt"
        )
        shutil.copyfile(translated_result_file, temp_nscript_dir)
        temp_0_file = os.path.join(temp_nscript_dir, "result.txt")
        # rename to 0.txt
        os.rename(temp_0_file, os.path.join(temp_nscript_dir, "0.txt"))

        # output file name
        basename = "nscript.dat"
        full_path = os.path.join(self.temp_unpack_directory, basename)

        # repack all files
        self.repack(
            self.packer,
            temp_nscript_dir,
            output_file=full_path,
        )
        return

    def replace_translated_rawfiles(self):
        """this method will copy the translated raw files to the SoratranslatorTemp directory"""
        # read the to_translate_file_list

    def pack_patchxp3(self):
        """instead of packing all files back, create a patch.xp3 file"""
        # collect all files in the SoraTranslator/TranslatedFiles directory
        # todo: implement this
        pass

    def set_unpacker(self, unpacker):
        """Set the unpacker."""
        self.unpacker = unpacker
        return

    def fix_encoding(self):
        """fix the encoding of the script files for the game, can only be called after unpacking the collection of the script files"""
        fix_allfiles(
            [self.script_file],
            replace=True,
            original_encoding=self.original_encoding,
            target_encoding=self.target_encoding,
        )

    # ==== methods for script files management ====================================================
    def create_temp_unpack_directory(self, clear=False):
        """
        Create the temp_unpack_directory.
        """
        # if exists delete it
        if os.path.exists(self.temp_unpack_directory) and clear:
            shutil.rmtree(self.temp_unpack_directory)
        # create empty directory
        if not os.path.exists(self.temp_unpack_directory):
            os.makedirs(self.temp_unpack_directory)

        # generate a readme.txt if there is none
        readme_file = os.path.join(self.temp_unpack_directory, "readme.txt")
        if not os.path.exists(readme_file):
            with open(readme_file, "w", encoding="utf_8") as f:
                f.write(
                    "This directory is used to store unpacked files by SoraTranslator. "
                )
                f.write(
                    "Do not delete this directory unless you are fully certain the translation has finished."
                )
        return

    def update_script_filelist(self):
        """update the script file list to the local from memory"""
        # ! warning: this function is loaded only when scriptfile.py is loaded,
        # ! possiblity of not having this function in memory when this function is called
        update_script_filelist(self.scriptfile_list_file, self.script_file_list)

    def update_to_translate_filelist(self):
        """update the to_translate_file_list to the local from memory"""
        update_script_filelist(
            self.to_translate_file_list_file, self.to_translate_file_list
        )

    # ==== utility methods =========================================================================
    @staticmethod
    def unpack(nsa_unpacker, input_file, output_file=""):
        """Extract the .xp3 file, xp3_u"""
        # extract the .xp3 file
        command = f'{nsa_unpacker} "{input_file}"'
        if output_file != "":
            command += f' "{output_file}"'
        return_code = os.system(command=command)
        return return_code == 0

    @staticmethod
    def repack(nsa_packer, input_directory, output_file):
        """repack a directory to a .xp3 file"""
        os.system(f'{nsa_packer} "{input_directory}" -o "{output_file}"')
        return
