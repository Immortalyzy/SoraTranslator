""" test file """

from ..Integrators.utils import utilities as util
from ..Integrators.Chaos_R.chaosr_game import ChaosRGame
from ..Integrators.Chaos_R.parser import parse_file, parse_block, guess_file_type
from ..scriptfile import ScriptFile
from ..block import Block
from pickle import dump, load

test_file = (
    "D:\\Work\\SoraTranslator\\GameResources\\RawText\\k_scenario\\01本編\\dakr001.ks"
)


def test_all():
    """test the encoding_fix.py module"""
    # test the from_file_list method
    python_file = "D:\\Work\\SoraTranslator\\GameResources\\OriginalFiles\\file_path.py"

    # create a game instance
    game = ChaosRGame.from_pythonfile(python_file)

    xp3_unpacker = util.XP3_UPK
    game.set_unpacker(xp3_unpacker)

    # for testing purpose, remove old temp directory
    # ! created
    # game.create_temp_unpack_directory(clear=True)

    # prepare raw files
    #! prepared
    # game.prepare_raw_text()

    # read script files
    game.read_script_files()
    # update new script file path
    game.copy_raw_text(replace=False)

    # prepare translation
    game.prepare_translation(replace=True)

    # repack all files
    # game.repack_all_files()

    game.save_game("D:\\Work\\SoraTranslator\\GameResources\\game.pkl")

    print(f"game: {game} has {len(game.script_file_list):d} script files prepared.")

    print("Done")
    return 0


def test_integration():
    """test the function of putting files back to its places"""
    game = load(open("D:\\Work\\SoraTranslator\\GameResources\\game.pkl", "rb"))

    for script_file in game.to_translate_file_list:
        script_file.update_from_textfile()

    script_file.update_from_textfile()

    # regenerate the script file
    script_file.generate_translated_rawfile(replace=True)


def test_prepare_all_text_files():
    """test the function of preparing all the text files"""
    python_file = "D:\\Work\\SoraTranslator\\GameResources\\OriginalFiles\\file_path.py"

    # create a game instance
    game = ChaosRGame.from_pythonfile(python_file)

    xp3_unpacker = util.XP3_UPK
    game.set_unpacker(xp3_unpacker)

    # for testing purpose, remove old temp directory
    game.create_temp_unpack_directory(clear=False)

    # read script files
    game.read_script_files()

    # prepare raw files
    game.copy_raw_text(
        replace=False
    )  # todo: debug usage, just update scriptfile path to the new one

    print(f"game: {game} has {len(game.script_file_list):d} script files prepared.")

    # guess all the files types
    for script_file in game.script_file_list:
        script_file.file_type = guess_file_type(script_file)
    game.update_script_filelist()

    # count the number of files to be translated
    num_files_to_translate = 0
    to_translate_file_list = []
    for script_file in game.script_file_list:
        if script_file.is_to_translate():
            to_translate_file_list.append(script_file)
            num_files_to_translate += 1

    # generate text files for all the files to be translated
    for script_file in to_translate_file_list:
        # parse the file
        script_file.parse(
            parse_file_function=parse_file, parse_block_function=parse_block
        )
        script_file.generate_textfile(replace=False)
