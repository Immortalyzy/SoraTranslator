"""stores all translatros' info"""

from config import CONFIG
from .ChatGPT_API.chatgpt_api import GPT_Translator
from .GalTransl_API import GalTranslTranslator


def createTranslatorInstance(translator, config=CONFIG):
    """create a translator instance based on the translator name"""
    if translator == "gpt":
        return GPT_Translator(config)
    if translator == "galtransl":
        return GalTranslTranslator(config)
