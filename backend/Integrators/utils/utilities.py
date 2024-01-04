""" information about utilities used by the integrators """

import os

# ==== xp3_upk =======================================================================
# get full path to the xp3 unpacker
xp3exe_file = "xp3_upk.exe"
XP3_UPK = os.path.join(os.path.dirname(__file__), xp3exe_file)

XP3_UPK_info = "xp3_upk.exe doesn't support pointing output directory. It will only unpack to the same directory as the .xp3 file."
# ==== xp3_upk =======================================================================

# ==== nsa realted ===================================================================
# get full path to the nsa tools
nsaarc_file = "nsaarc.exe"
nsamake_file = "nsamake.exe"
nscdec_file = "nscdec.exe"
NSAARC = os.path.join(os.path.dirname(__file__), nsaarc_file)
NSAMAKE = os.path.join(os.path.dirname(__file__), nsamake_file)
NSCDEC = os.path.join(os.path.dirname(__file__), nscdec_file)
# ==== nsa realted ===================================================================
