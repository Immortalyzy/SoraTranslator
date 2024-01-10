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
# check https://github.com/GoldbarGames/ONScripter-EN-Steam/tree/master/tools for more information
nsaarc_file = "nsaarc.exe"
nscmake_file = "nscmake.exe"
nsdec_file = "nsdec.exe"
# pack folder to .nsa
NSAARC = os.path.join(os.path.dirname(__file__), nsaarc_file)
# make a nscript/0.text to a nscript.dat
NSCMAKE = os.path.join(os.path.dirname(__file__), nscmake_file)
# convert a nscript.dat to result.txt
NSDEC = os.path.join(os.path.dirname(__file__), nsdec_file)

# official command list
# from https://kaisernet.org/onscripter/api/NScrAPI-framed.html
NS_COMMAND_LIST = os.path.join(
    os.path.dirname(__file__), "nscripter_official_comands.txt"
)


def get_ns_command_list():
    """return a list of official nscripter commands"""
    with open(NS_COMMAND_LIST, "r", encoding="utf_8_sig") as file:
        lines = file.readlines()
        official_commands = [line.strip() for line in lines]
    return official_commands


# ==== nsa realted ===================================================================
