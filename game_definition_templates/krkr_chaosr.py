""" original files are big and should be kept in the original folder, here stores the path """

# name of the game
GAME_NAME = "神聖昂燐アルカナルージュ"

# main directory of the game
DIRECTORY = "U:/Toys/Games/Gal/chaosr/神聖昂燐アルカナルージュ"

# engine used by the game, could be different games with same engine,
GAME_ENGINE = "ChaosR"

# executable file
GAME_EXECUTABLE = "神聖昂燐アルカナルージュ.exe"

# this is regex pattern to match the files that contain the game texts
# all the files that contain text to be translated should be matched by this pattern
CONTENT_INDICATORS = [r"^(?!_).*arcana.*\.ks"]

# the .xp3 files that contain all types of scripts (including system scripts), this is used to extract the scripts and change the encoding
XP3_FILE_LIST = [
    "data.xp3",
    "k_bonus.xp3",
    "k_others.xp3",
    "k_scenario.xp3",
    "plugin.xp3",
]

# encoding specifics
ORIGINAL_ENCODING = "cp932"
TARGET_ENCODING = "utf_16"
