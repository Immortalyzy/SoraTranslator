""" test file """

from pickle import dump, load
import shutil
import os
from ..Integrators.utils import utilities as util
from ..Integrators.Chaos_R.chaosr_game import ChaosRGame
from ..Integrators.Chaos_R.parser import parse_file, parse_block, guess_file_type
from ..scriptfile import ScriptFile
from ..block import Block

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

    # # for testing purpose, remove old temp directory
    # # ! created
    # game.create_temp_unpack_directory(clear=True)

    # # prepare raw files
    # # prepared
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
    game: ChaosRGame = load(
        open("D:\\Work\\SoraTranslator\\GameResources\\game.pkl", "rb")
    )

    for script_file in game.to_translate_file_list[:100]:
        script_file.update_from_textfile()

        # regenerate the script file, this will be save to translated_files folder
        script_file.generate_translated_rawfile(replace=True)

        # get the relative path
        relative_path = os.path.relpath(
            script_file.translated_script_file_path, game.translated_files_directory
        )
        desitnation_path = os.path.join(game.temp_unpack_directory, relative_path)

        # copy the file to the temp folder, overwrite if exists
        shutil.copyfile(script_file.translated_script_file_path, desitnation_path)


#    game.save_game("D:\\Work\\SoraTranslator\\GameResources\\game.pkl")


def test_repack() -> None:
    """!! real usage test"""
    # add type hint
    game: ChaosRGame = load(
        open("D:\\Work\\SoraTranslator\\GameResources\\game.pkl", "rb")
    )

    game.repack_all_files()
