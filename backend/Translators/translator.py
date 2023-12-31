""" This script defines the preparation steps before translation """


# before translation, the translation should read a to_translate_file_list.csv file to get a list of [ScriptFile] for translation
from abc import ABC, abstractmethod
from scriptfile import ScriptFile
from block import Block
from constants import SuccessStatus as success
from constants import default_config


class Translator(ABC):
    """A general translator class that provides all necessary preparation steps, the class will also store information about the translation process for later use"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def translate_block(self, block: Block, context=None) -> success:
        """Read the to_translate_file_list.csv file and get a list of ScriptFile for translation"""
        pass

    @abstractmethod
    def translate_file_whole(self, script_file: ScriptFile) -> success:
        """Set the path of to_translate_file_list.csv file"""
        pass


def createTranslatorInstance(translator, config=default_config):
    """create a translator instance from a string"""
    result = None
    if translator == "gpt":
        result = GPT_Translator(config)
    return result
