""" This script defines the preparation steps before translation """


# before translation, the translation should read a to_translate_file_list.csv file to get a list of [ScriptFile] for translation
from ..ScriptFile import ScriptFile
from ..block import Block


class Translator:
    """A general translator class that provides all necessary preparation steps, the class will also store information about the translation process for later use"""

    to_translate_file_list = []

    def __init__(self, config):
        self.config = config
