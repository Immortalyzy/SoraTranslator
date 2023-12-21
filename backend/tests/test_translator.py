""" pytest module to test translator """

from ..scriptfile import ScriptFile
from ..Translators.ChatGPT_API.chatgpt_api import GPT_Translator
from ..constants import Config, DEFAULT_CONFIG_FILE

test_file = "D:\\Work\\SoraTranslator\\GameResources\\Text\\k_scenario\\01本編\\dakr001.csv"

def test_gpt_translator():
    """ test gpt translator """
    # load config
    config = Config.from_json(DEFAULT_CONFIG_FILE)
    translator = GPT_Translator(config)

    print("Testing GPT Translator")
    print("model name:", translator.model)
    print("api key:", translator.client.api_key)

    # load script file
    script_file = ScriptFile.from_textfile(test_file)

    # translate
    success = translator.translate_file_whole(script_file)

    # save translated file
    script_file.generate_textfile(replace=True)

    return success

def test_translate_all_files():
    """ !! this test has real usage, consumes tokens and must be run only once """
    # load config
    config = Config.from_json(DEFAULT_CONFIG_FILE)
    translator = GPT_Translator(config)

    print("Testing GPT Translator")
    print("model name:", translator.model)
    print("api key:", translator.client.api_key)

    # load script file
    script_file = ScriptFile.from_textfile(test_file)

    # translate
    success = translator.translate_file_whole(script_file)

    # save translated file
    script_file.generate_textfile(replace=True)

    return success
