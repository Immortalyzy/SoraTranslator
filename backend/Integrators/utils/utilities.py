""" information about utilities used by the integrators """

import os

# ==== xp3_upk =======================================================================
# get full path to the xp3 unpacker
file = "xp3_upk.exe"
XP3_UPK = os.path.join(os.path.dirname(__file__), file)

XP3_UPK_info = "xp3_upk.exe doesn't support pointing output directory. It will only unpack to the same directory as the .xp3 file."
# ==== xp3_upk =======================================================================
