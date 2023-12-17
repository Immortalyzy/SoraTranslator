""" Game class for Chaos_R games. """

import importlib.util
import os
import shutil
from constants import DEFAULT_GAME_RESOURCES_DIRECTORY
from constants import DEFAULT_XP3_UNPACKER
from game import Game
from gamefile import GameFile


class ChaosRGame(Game):
    """Game class for Chaos_R games."""

    def __init__(self):
        super().__init__("Chaos_R")
        # Game Resources directory, no matter the original file directory the output will be put under RawText of this folder
        self.game_resources_directory = DEFAULT_GAME_RESOURCES_DIRECTORY
        self.unpacker = DEFAULT_XP3_UNPACKER
        # extensions of the script files
        self.script_extensions = [
            ".asd",
            ".func",
            ".ks",
            ".txt",
            ".ini",
            ".csv",
            ".tjs",
        ]

        # default values for Chaos_R
        self.original_encoding = "cp932"
        self.target_encoding = "utf_16"

        # directory
        self.directory = ""
        # xp3 file list
        self.xp3_file_list = []
        # script file list
        self.script_file_list = []
        # to_translate file list
        self.to_translate_file_list = []

        # temp unpack directory
        self.temp_unpack_directory = ""

        # configurations
        # patching mode includes:
        # 1. patch: create a patch.xp3
        # 2, replace: replace the original files with the translated files and repack the original .xp3 files
        self.patching_mode = "patching"

    @classmethod
    def from_pythonfile(cls, python_file):
        """
        Create an Game object from a python file. This is the recommended way since you can select which files to upzip.
        """
        instance = cls()

        # verify the existence of the python file
        if not os.path.exists(python_file):
            raise FileNotFoundError("The python file does not exist.")

        # load the variables in the python file
        spec = importlib.util.spec_from_file_location("module.name", python_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # get the variables
        if hasattr(module, "GAME_RESOURCES_DIRECTORY"):
            instance.game_resources_directory = module.GAME_RESOURCES_DIRECTORY

        # DIRECTORY is required
        instance.directory = module.DIRECTORY

        if hasattr(module, "XP3_FILE_LIST"):
            for file in module.XP3_FILE_LIST:
                # complete to full path
                file = os.path.join(instance.directory, file)

                # verify the existence of the file
                # todo: create just a warning instead of raising an error
                if not os.path.exists(file):
                    raise FileNotFoundError("The file does not exist.")
                else:
                    # add the file to file list
                    instance.xp3_file_list.append(file)
        else:
            # no FILE_LIST is provided, get the file list from the directory
            instance.xp3_file_list = instance.get_xp3file_list(instance.directory)

        # get original encoding
        if hasattr(module, "ORIGINAL_ENCODING"):
            instance.original_encoding = module.ORIGINAL_ENCODING
        else:
            instance.original_encoding = "cp932"

        # get target encoding
        if hasattr(module, "TARGET_ENCODING"):
            instance.target_encoding = module.TARGET_ENCODING
        else:
            instance.target_encoding = "utf_16"

        # verify the existence of the directory
        if not os.path.exists(instance.directory):
            raise FileNotFoundError("The directory does not exist.")
        # verify game engine
        if module.GAME_ENGINE != "Kirikiri2":
            raise ValueError("The game engine is not Kirikiri2. ")

        instance.post_init()
        return instance

    @classmethod
    def from_directory(cls, directory):
        """
        Create an EncodingFix object from a directory.
        """
        instance = cls()
        instance.directory = directory
        # verify the existence of the directory
        if not os.path.exists(instance.directory):
            raise FileNotFoundError("The directory does not exist.")

        instance.xp3_file_list = instance.get_xp3file_list(instance.directory)
        # verify the game engine by checking the existence of .xp3 files
        if len(instance.xp3_file_list) == 0:
            raise ValueError(".xp3 files not found. ")

        instance.post_init()
        return instance

    def post_init(self):
        """Post init."""
        self.temp_unpack_directory = self.directory + "\\temp_unpack"
        # create temp unpack directory
        self.create_temp_unpack_directory(clear=False)

    # ==== high level methods ===============================
    def prepare_raw_text(self):
        """
        Prepare the raw text for Chaos_R games. This method will put all script files into the GameResources/RawText folder.
        """
        pass

    def integrate_from_text(self, text):
        """Integrate the text into the game."""
        pass

    # ==== methods for packeging ==================================================================
    def unpack_allfiles(self):
        """unpack all files in the file list to temp_unpack_directory"""
        # unpack all files
        for file in self.xp3_file_list:
            # extract the .xp3 file
            success = self.unpack_xp3(self.unpacker, file)
            if not success:
                raise ValueError(f"Failed to unpack {file}")

            # move the files to the temp_unpack_directory
            ## get file name without extension
            file_name = os.path.splitext(os.path.basename(file))[0]
            ## join the name with its directory
            file_name = os.path.join(self.directory, file_name)
            ## !! this moves the entire directory with the name file_name
            shutil.move(file_name, self.temp_unpack_directory)

        # now all the files are unpacked and stored in the temp_unpack_directory
        return

    def repackallfiles(self):
        """repack all files in the temp_unpack_directory"""

        # fix the encoding of these files
        for file in self.xp3_file_list:
            # get the name of the directory = the name of the file without extension
            directory_name = os.path.splitext(os.path.basename(file))[0]
            # join the name with its directory to get full directory name
            directory_name = os.path.join(self.temp_unpack_directory, directory_name)
            # pack the directory
            self.repack_xp3(self.unpacker, directory_name)

    def pack_patchxp3(self):
        """instead of packing all files back, create a patch.xp3 file"""
        # todo: implement this
        pass

    def set_unpacker(self, unpacker):
        """Set the unpacker."""
        self.unpacker = unpacker
        return

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
        script_file_list = self.select_files(
            self.temp_unpack_directory, self.extensions
        )
        # create instances of GameFile for each file

        # save the script file list to a .csv file under the temp_unpack_directory
        # create the file path
        script_file_list_file = os.path.join(
            self.temp_unpack_directory, "script_file_list.csv"
        )

        # write the file list to the file
        with open(script_file_list_file, "w", encoding="utf_8") as f:
            for file in self.script_file_list:
                f.write(file + "\n")

        return

    def update_script_file_list(self):
        """update the script file list from the temp_unpack_directory"""

    # ==== utility methods =========================================================================
    @staticmethod
    def get_xp3file_list(directory):
        """
        Get the file list (.xp3 files only) of the directory.
        """
        xp3_file_list = []
        for root, _, files in os.walk(directory):
            for file in files:
                # get the file extension
                file_extension = os.path.splitext(file)[1]
                # if the file extension is .xp3, add it to the file list
                if file_extension == ".xp3":
                    # create the full file path
                    xp3_file_list.append(os.path.join(root, file))

        return xp3_file_list

    @staticmethod
    def unpack_xp3(xp3_unpacker, input_file):
        """Extract the .xp3 file, xp3_u"""
        # extract the .xp3 file
        return_code = os.system(f'{xp3_unpacker} "{input_file}"')
        return return_code == 0

    @staticmethod
    def repack_xp3(xp3_packer, input_directory):
        """repack a directory to a .xp3 file"""
        os.system(f'{xp3_packer} "{input_directory}"')
        return

    @staticmethod
    def select_files(directory, extensions):
        """return a list of files with the given extensions"""
        file_list = []
        for root, _, files in os.walk(directory):
            for file in files:
                # get the file extension
                file_extension = os.path.splitext(file)[1]
                # if the file extension is .xp3, add it to the file list
                if file_extension in extensions:
                    # create the full file path
                    file_list.append(os.path.join(root, file))

        return file_list
