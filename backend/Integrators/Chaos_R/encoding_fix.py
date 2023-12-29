"""
This script provides the encoding fix functions for the games of Chaos-R.
The encoding of the text content of the games of Chaos-R is Shift-JIS.
In order to run it directly without using Locale Emulator, we need to convert the encoding of the text content from Shift-JIS to UTF-8 (or UTF-16LF).
"""
import os
import shutil


def fix_encoding(
    input_file_path,
    output_file_path,
    original_encoding="cp932",
    target_encoding="utf_16",
):
    """
    Fix the encoding of the text content of the games of Chaos-R.
    """
    # read and change the encoding from Shift-JIS to UTF-8
    try:
        with open(input_file_path, "r", encoding=original_encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"UnicodeDecodeError: {input_file_path}")
        try:
            open(input_file_path, "r", encoding=target_encoding)
            print(f"Already converted: {input_file_path}")
            shutil.copyfile(input_file_path, output_file_path)
            return True
        except UnicodeDecodeError:
            return False

    # write the content back to the file
    with open(output_file_path, "w", encoding=target_encoding) as f:
        f.write(content)
    return


def fix_allfiles(
    scriptfile_list, replace=False, original_encoding="cp932", target_encoding="utf_8"
):
    """fix all files of a game instance"""
    # get all files with the given extensions

    # fix the encoding of these files
    for scriptfile in scriptfile_list:
        file = scriptfile.script_file_path
        # print status
        print(
            f"Fixing encoding of {scriptfile.script_file_path}, {scriptfile_list.index(scriptfile) + 1}/{len(scriptfile_list)}"
        )
        # create the output file path
        output_file = file + "new_encoding"
        # fix the encoding
        fix_encoding(
            input_file_path=file,
            output_file_path=output_file,
            original_encoding=original_encoding,
            target_encoding=target_encoding,
        )
        if replace:
            # delete the original file
            os.remove(file)
            # rename the new file
            os.rename(output_file, file)

    return
