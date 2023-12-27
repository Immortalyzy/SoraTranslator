""" This script defines the preparation steps before translation """


# before translation, the translation should read a to_translate_file_list.csv file to get a list of [ScriptFile] for translation
from ..ScriptFile import ScriptFile
from ..block import Block


class Translator:
    """A general translator class that provides all necessary preparation steps, the class will also store information about the translation process for later use"""

    to_translate_file_list = []
    to_translate_file_list_file_path = ""

    def __init__(self, config):
        self.config = config

    def read_to_translate_file_list(self):
        """Read the to_translate_file_list.csv file and get a list of ScriptFile for translation"""
        pass

    def set_to_translate_file_list_path(self, path):
        """Set the path of to_translate_file_list.csv file"""
        self.to_translate_file_list_file_path = path
