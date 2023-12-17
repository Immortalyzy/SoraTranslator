""" debug encoding_fix.py  """

from ..Integrators.Chaos_R.chaosr_game import ChaosRGame
from ..Integrators.Chaos_R import encoding_fix as enc_fix
from ..Integrators.utils import utilities as util

def test_encoding_fix():
    """ test the encoding_fix.py module """
    # test the from_file_list method
    python_file = "D:\\Work\\SoraTranslator\\GameResources\\OriginalFiles\\file_path.py"

    # create a game instance
    game = ChaosRGame.from_pythonfile(python_file)

    xp3_unpacker = util.XP3_UPK
    game.create_temp_unpack_directory(clear=True)
    game.set_unpacker(xp3_unpacker)
    game.unpack_allfiles()

    # fix the encoding of all files
    enc_fix.fix_allfiles(game.script_file_list, replace=True)

    # repack the game
    game.repackallfiles()

    print("Done")
    return 0
