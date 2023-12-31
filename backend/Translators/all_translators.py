""" stores all translatros' info """
from constants import default_config
from .ChatGPT_API.chatgpt_api import GPT_Translator


def createTranslatorInstance(translator, config=default_config):
    """create a translator instance based on the translator name"""
    if translator == "gpt":
        return GPT_Translator(config)
