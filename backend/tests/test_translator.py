""" pytest module to test translator """

from scriptfile import ScriptFile
from Translators.ChatGPT_API.chatgpt_api import GPT_Translator
from constants import Config, DEFAULT_CONFIG_FILE
from Integrators.Chaos_R.chaosr_game import ChaosRGame
from pickle import dump, load

test_file = (
    "D:\\Work\\SoraTranslator\\SoraTranslator\\Text\\k_scenario\\01本編\\luna034H.csv"
)


def test_generation_after_translation():
    """test generation after translation"""
    test_file_ = "U:/Toys/Games/Gal/chaosr/神聖昂燐ダクリュオン_ver1.0.1/SoraTranslator/Text/k_scenario/A_00_dakr020.csv"
    script_file = ScriptFile.from_textfile(test_file_)
    script_file.generate_textfile(replace=True)


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
    # test different temperature
    config.gpt_temperature = 0.25
    config.gpt_model = "gpt-3.5-turbo-16k"
    config.gpt_max_lines = 40
    config.gpt_speration_method = "[]"
    config.gpt_enclosing_joiner = "|"
    translator = GPT_Translator(config)

    game: ChaosRGame = load(
        open("D:\\Work\\SoraTranslator\\SoraTranslator\\game.pkl", "rb")
    )

    translated_count = 337
    total_translation = len(game.to_translate_file_list)
    now_translate = min(500, total_translation)
    retanslate_list = []
    testing_translate_list = []
    for script_file in game.to_translate_file_list:
        for name_end in retanslate_list:
            if script_file.text_file_path.endswith(name_end):
                testing_translate_list.append(script_file)
    # testing_translate_list.extend(
    #     game.to_translate_file_list[translated_count:now_translate]
    # )

    print("Testing GPT Translator")
    print("model name:", translator.model)

    this_translated_count = 0
    for script_file in testing_translate_list:
        # translate
        success = translator.translate_file_whole(script_file)

        # save translated file
        script_file.generate_textfile(replace=True)

        # update count
        this_translated_count += 1

        print(
            f"Translated {this_translated_count:d} files out of {len(testing_translate_list):d} files."
        )
        # save game
        game.update_to_translate_filelist()
        game.save_game("D:\\Work\\SoraTranslator\\SoraTranslator\\game.pkl")
        game.update_script_filelist()

    return success
