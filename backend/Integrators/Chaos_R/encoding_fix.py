""" 
This script provides the encoding fix functions for the games of Chaos-R. 
The encoding of the text content of the games of Chaos-R is Shift-JIS. 
In order to run it directly without using Locale Emulator, we need to convert the encoding of the text content from Shift-JIS to UTF-8 (or UTF-16LF).
"""
import importlib.util
import os
import shutil
from constants import DEFAULT_ENCODING_OUTPUT, DEFAULT_GAME_RESOURCES_DIRECTORY
from constants import DEFAULT_XP3_UNPACKER


"""
Extractor provides the functions to extract the text from the game, save it to GameResources/RawText and prepare it for further processing.
"""


def fix_encoding(
    input_file,
    output_file,
    original_encoding="cp932",
    target_encoding="utf_8",
):
    """
    Fix the encoding of the text content of the games of Chaos-R.
    """
    # read and change the encoding from Shift-JIS to UTF-8
    with open(input_file, "r", encoding=original_encoding) as f:
        content = f.read()

    # write the content back to the file
    with open(output_file, "w", encoding=target_encoding) as f:
        f.write(content)
    return


def fix_allfiles(chaosr_game):
    """fix all files of a game instance"""
    # get all files with the given extensions
    file_list = chaosr_game.select_files(
        chaosr_game.temp_unpack_directory, chaosr_game.script_extensions
    )

    # fix the encoding of these files
    for file in file_list:
        # print status
        print(
            f"Fixing encoding of {file}, {file_list.index(file) + 1}/{len(file_list)}"
        )
        # create the output file path
        output_file = file + "new_encoding"
        # fix the encoding
        fix_encoding(
            input_file=file,
            output_file=output_file,
            original_encoding=chaosr_game.original_encoding,
            target_encoding=chaosr_game.target_encoding,
        )
        # delete the original file
        os.remove(file)
        # rename the new file
        os.rename(output_file, file)

    return
