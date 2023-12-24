""" pytest module to test translator """

from ..scriptfile import ScriptFile
from ..Translators.ChatGPT_API.chatgpt_api import GPT_Translator
from ..constants import Config, DEFAULT_CONFIG_FILE
from ..Integrators.Chaos_R.chaosr_game import ChaosRGame
from pickle import dump, load

test_file = (
    "D:\\Work\\SoraTranslator\\GameResources\\Text\\k_scenario\\01本編\\luna034H.csv"
)


def test_gpt_translator():
    """test gpt translator"""
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
    """!! this test has real usage, consumes tokens and must be run only once"""
    # load config
    config = Config.from_json(DEFAULT_CONFIG_FILE)
    translator = GPT_Translator(config)

    game: ChaosRGame = load(
        open("D:\\Work\\SoraTranslator\\GameResources\\game.pkl", "rb")
    )

    testing_translate_list = game.to_translate_file_list[:100]

    print("Testing GPT Translator")
    print("model name:", translator.model)

    translated_count = 0
    for script_file in testing_translate_list:
        # translate
        success = translator.translate_file_whole(script_file)

        # save translated file
        script_file.generate_textfile(replace=True)

        # update count
        translated_count += 1

        print(
            f"Translated {translated_count:d} files out of {len(testing_translate_list):d} files."
        )

    # save game
    game.update_script_filelist()
    game.update_to_translate_filelist()

    game.save_game("D:\\Work\\SoraTranslator\\GameResources\\game.pkl")

    return success
