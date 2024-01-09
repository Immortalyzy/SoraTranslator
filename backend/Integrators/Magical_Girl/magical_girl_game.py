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
from .encoding_fix import fix_allfiles
from .parser import parse_file, parse_block
from ..utils import NSDEC, NSCMAKE


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
        instance.original_script_file = module.SCRIPT_FILE

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

        # verify the existence of the directory
        if not os.path.exists(instance.directory):
            raise FileNotFoundError("The directory does not exist.")

        if not os.path.exists(instance.script_file):
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
        # unpack files
        self.unpack_allfiles(replace=False)

        # read script files
        self.read_script_files()

        # fix encoding
        self.fix_encoding()

        # copy raw text
        self.copy_raw_text(replace=replace)

    def prepare_translation(self, replace=False):
        """
        This function will generate all the files that are required by the translation process.
        """
        # guess file types (chaos-R only)
        self.prepare_raw_text(replace=replace)
        # chaos-R game permits the auto detection of file types
        self.update_script_filelist()

        # update to_translate_file_list
        for script_file in self.script_file_list:
            if script_file.is_to_translate():
                self.to_translate_file_list.append(script_file)
        self.update_to_translate_filelist()

        for script_file in self.to_translate_file_list:
            if script_file.is_Hcontent():
                self.dangerous_file_list.append(script_file)

        log_message(
            f"Indentified {len(self.to_translate_file_list)} files to translate. ",
            log_level=LogLevel.INFO,
        )

        # generate text files for all to_translate files
        for script_file in self.to_translate_file_list:
            # parsing
            script_file.parse(
                parse_file_function=parse_file, parse_block_function=parse_block
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

        # copy script files to the RawText folder (KEEPING the directory structure)
        for scriptfile in self.script_file_list:
            # duplicate directory structure of temp_unpack_directory in the RawText directory
            # get the relative path of the script file
            relative_path = os.path.relpath(
                scriptfile.script_file_path, self.temp_unpack_directory
            )

            full_desitnation_path = os.path.join(self.rawtext_directory, relative_path)
            destination_directory = os.path.dirname(full_desitnation_path)
            # create the directory if it does not exist
            if not os.path.exists(destination_directory):
                os.makedirs(destination_directory, exist_ok=True)

            # check if the file already exists
            if os.path.exists(full_desitnation_path):
                if replace:
                    os.remove(full_desitnation_path)
                else:
                    print(
                        f"Skipping {scriptfile.script_file_path} since it already exists."
                    )
                    scriptfile.script_file_path = full_desitnation_path
                    continue
            shutil.copy2(scriptfile.script_file_path, full_desitnation_path)
            # update the script file information
            scriptfile.script_file_path = full_desitnation_path
        log_message(
            f"{len(self.script_file_list):d} raw text files are copied to {self.rawtext_directory}.",
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

            script_file.generate_translated_rawfile(dest=translated_path, replace=True)

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
        # extract the nscript.dat file
        success = self.unpack(self.unpacker, self.original_script_file)
        if not success:
            raise ValueError("Failed to unpack the nscript file.")

        result_file_basename = "result.txt"
        result_file_fullpath = os.path.join(self.directory, result_file_basename)

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

        # repack all files
        self.repack(self.packer, self.temp_unpack_directory)
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
            self.script_file_list,
            replace=True,
            original_encoding=self.original_encoding,
            target_encoding=self.target_encoding,
        )
        self.is_encoding_fixed = True

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

    def read_script_files(self):
        """select script files from the temp_unpack_directory"""
        # get all files with the given extensions
        for xp3_file in self.xp3_file_list:
            base_xp3_file_name = os.path.splitext(os.path.basename(xp3_file))[0]
            path_of_unpacked_xp3 = os.path.join(
                self.temp_unpack_directory, base_xp3_file_name
            )
            script_filepath_list_xp3 = self.select_files(
                path_of_unpacked_xp3, self.script_extensions
            )
            # create instances of ScriptFile for each file, note the original package
            for filepath in script_filepath_list_xp3:
                scriptfile = ScriptFile.from_originalfile(filepath)
                scriptfile.original_package = base_xp3_file_name
                self.script_file_list.append(scriptfile)
        # todo: set the paths for various files of the script file to avoid problems

        # save the script file list to a .csv file under the temp_unpack_directory
        update_script_filelist(self.scriptfile_list_file, self.script_file_list)
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
    def unpack(nsa_unpacker, input_file):
        """Extract the .xp3 file, xp3_u"""
        # extract the .xp3 file
        return_code = os.system(f'{nsa_unpacker} "{input_file}"')
        return return_code == 0

    @staticmethod
    def repack(nsa_packer, input_directory, output_file):
        """repack a directory to a .xp3 file"""
        os.system(f'{nsa_packer} "{input_directory}" -o "{output_file}"')
        return
