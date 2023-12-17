""" debug encoding_fix.py  """
import Integrators.Chaos_R.encoding_fix as enc_fix
import Integrators.Chaos_R.chaosr_game as chaosr_game
import Integrators.utils.utilities as util

# test the from_file_list method
python_file = "D:\\Work\\SoraTranslator\\GameResources\\OriginalFiles\\file_path.py"

# create a game instance
game = chaosr_game.ChaosRGame.from_pythonfile(python_file)

xp3_unpacker = util.XP3_UPK
game.set_unpacker(xp3_unpacker)
game.unpack_allfiles()

# fix the encoding of all files
enc_fix.fix_allfiles(game)

# repack the game
game.repackallfiles()

print("Done")
