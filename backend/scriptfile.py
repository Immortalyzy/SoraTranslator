""" game file class, every instance is a script file of the game """

import datetime
import os
import importlib.util


class ScriptFile:
    """The GameFile class defines a script file and info around it, the class provides a framework for integration actions defined in the game folders"""

    def __init__(self, file_path):

        self.original_file_path = file_path
        self.script_file_path = file_path # this avoids error when forgot to use from_originalfile
        self.text_file_path = ""  # the path of the text file in .csv

        self.read_date = datetime.datetime.now()

        # file type
        self.file_type = "content"
        self.original_package = ""  # the package the file is in

        # set to true if ALL the text in the file is translated
        self.is_translated = False

        # if file type is content, then it should content following variables for eaiser integration
        self.translated_script_file_path = ""
        # at the end of certain files there will be a "jump" action that indicates the name of next file
        self.next_script_file_name = ""

        # ordinary info, will add here as generally needed

    @classmethod
    def from_originalfile(cls, file_path):
        """create a game file instance from a file path"""
        game_file = cls(file_path)
        game_file.script_file_path = file_path
        return game_file

    @classmethod
    def from_textfile(cls, file_path):
        """create a game file instance from a file path"""
        game_file = cls(file_path)
        game_file.text_file_path = file_path
        return game_file

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

    def generate_textfile(self, parser_file):
        """generate the text file"""
        # load the functions from the parser file
        spec = importlib.util.spec_from_file_location("module.name", parser_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # todo: complete

    def is_system_file(self):
        """ return if is system file""" 
        return self.file_type == "system"
    def is_content_file(self):
        """ return if is content file""" 
        return self.file_type == "content"


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
