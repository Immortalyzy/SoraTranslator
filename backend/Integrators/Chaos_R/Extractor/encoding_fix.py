""" 
This script provides the encoding fix for the games of Chaos-R. 
The encoding of the text content of the games of Chaos-R is Shift-JIS. 
In order to run it directly without using Locale Emulator, we need to convert the encoding of the text content from Shift-JIS to UTF-8 (or UTF-16LF).
"""
import importlib.util
import os
import shutil
from constants import DEFAULT_ENCODING_OUTPUT, DEFAULT_GAME_RESOURCES_DIRECTORY
from constants import DEFAULT_XP3_UNPACKER


class EncodingFix:
    """
    EncodingFix class provides the encoding fix for the games of Chaos-R.
    """

    # the extensions of the files that need to be fixed
    extensions = [".asd", ".func", ".ks", ".txt", ".ini", ".csv", ".tjs"]

    def __init__(self):
        # Game Resources directory, no matter the original file directory the output will be put under RawText of this folder
        self.game_resources_directory = DEFAULT_GAME_RESOURCES_DIRECTORY
        self.encoding_output = DEFAULT_ENCODING_OUTPUT
        self.unpacker = DEFAULT_XP3_UNPACKER

        # encodings
        self.original_encoding = "shift_jisx0213"
        self.target_encoding = "utf_8"

        # directory
        self.directory = ""
        # xp3 file list
        self.xp3_file_list = []

        self.temp_unpack_directory = ""

    @classmethod
    def from_pythonfile(cls, python_file):
        """
        Create an EncodingFix object from a python file. This is the recommended way since you can select which files to upzip.
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
        instance.directory = module.DIRECTORY
        if hasattr(module, "FILE_LIST"):
            for file in module.FILE_LIST:
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
            instance.original_encoding = "shift_jisx0213"
        # get target encoding
        if hasattr(module, "TARGET_ENCODING"):
            instance.target_encoding = module.TARGET_ENCODING
        else:
            instance.target_encoding = "utf_8"

        # verify the existence of the directory
        if not os.path.exists(instance.directory):
            raise FileNotFoundError("The directory does not exist.")
        # verify game engine
        if module.GAME_ENGINE != "Kirikiri2":
            raise ValueError("The game engine is not Kirikiri2. ")

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

        return instance

    @staticmethod
    def fix_encoding(
        input_file,
        output_file,
        original_encoding="shift_jisx0213",
        target_encoding="utf_8",
    ):
        """
        Fix the encoding of the text content of the games of Chaos-R.
        """
        # read and change the encoding from Shift-JIS to UTF-8
        with open(input_file, "r", encoding=original_encoding) as f:
            content = f.read()
        # write the content back to the file
        with open(output_file, "w", encoding=target_encoding) as f:
            f.write(content)
        return

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

    def set_unpacker(self, unpacker):
        """Set the unpacker."""
        self.unpacker = unpacker
        return

    @staticmethod
    def unpack_xp3(xp3_unpacker, input_file):
        """Extract the .xp3 file, xp3_u"""
        # extract the .xp3 file
        os.system(f'{xp3_unpacker} "{input_file}"')
        return

    @staticmethod
    def repack_xp3(xp3_packer, input_directory):
        """repack a directory to a .xp3 file"""
        os.system(f'{xp3_packer} "{input_directory}"')
        return

    def create_temp_unpack_directory(self):
        """
        Create the temp_unpack_directory.
        """
        # create temp unpack directory
        self.temp_unpack_directory = os.path.join(self.directory, "temp_unpack")
        if not os.path.exists(self.temp_unpack_directory):
            os.makedirs(self.temp_unpack_directory)
        return

    def unpack_allfiles(self):
        """unpack all files in the file list"""
        # create temp unpack directory
        self.create_temp_unpack_directory()

        # unpack all files
        for file in self.xp3_file_list:
            # check if output directory exists, if not create it
            if not os.path.exists(self.encoding_output):
                os.makedirs(self.encoding_output)

            # extract the .xp3 file
            self.unpack_xp3(self.unpacker, file)

            # move the files to the temp_unpack_directory
            ## get file name without extension
            file_name = os.path.splitext(os.path.basename(file))[0]
            ## join the name with its directory
            file_name = os.path.join(self.directory, file_name)

            # !! this moves the entire directory with the name file_name
            shutil.move(file_name, self.temp_unpack_directory)

        # now all the files are unpacked and stored in the temp_unpack_directory
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

    def fix_allfiles(self):
        """fix all files in the temp_unpack_directory"""
        # get all files with the given extensions
        file_list = self.select_files(self.temp_unpack_directory, self.extensions)

        # fix the encoding of these files
        for file in file_list:
            # print status
            print(
                f"Fixing encoding of {file}, {file_list.index(file) + 1}/{len(file_list)}"
            )
            # create the output file path
            output_file = file + "new_encoding"
            # fix the encoding
            self.fix_encoding(file, output_file)
            # delete the original file
            os.remove(file)
            # rename the new file
            os.rename(output_file, file)

        return

    def re_packallfiles(self):
        """repack all files in the temp_unpack_directory"""

        # fix the encoding of these files
        for file in self.xp3_file_list:
            # get the name of the directory = the name of the file without extension
            directory_name = os.path.splitext(os.path.basename(file))[0]
            # join the name with its directory to get full directory name
            directory_name = os.path.join(self.temp_unpack_directory, directory_name)
            # pack the directory
            self.repack_xp3(self.unpacker, directory_name)
            # create file name with full path
            file_name = directory_name + ".xp3"


# 1, At first the script will extract all the script files with following extensions to a new folder named (scripts_utf8):

# 1.1 extract all files using .xp3 extractor xp3_upk.exe


# 2, Then the script will convert the encoding of these files from Shift-JIS to UTF-8 (or UTF-16LF).
