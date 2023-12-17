""" test file """

from ..Integrators.utils import utilities as util
from ..Integrators.Chaos_R.chaosr_game import ChaosRGame


def test_integration():
    """test the encoding_fix.py module"""
    # test the from_file_list method
    python_file = "D:\\Work\\SoraTranslator\\GameResources\\OriginalFiles\\file_path.py"

    # create a game instance
    game = ChaosRGame.from_pythonfile(python_file)

    xp3_unpacker = util.XP3_UPK
    game.set_unpacker(xp3_unpacker)

    # for testing purpose, remove old temp directory
    game.create_temp_unpack_directory(clear=True)

    # prepare raw files
    game.prepare_raw_text()

    print(f"game: {game} has {len(game.script_file_list):d} script files prepared.")

    print("Done")
    return 0

