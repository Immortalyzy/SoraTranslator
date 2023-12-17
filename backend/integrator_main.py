"""
The games of Chaos-R are developed using the KAG (Kirikiri Adventure Game) engine.
For now the games considered are stored without encryption and in Shift-JIS encoding.

Normally the game must be run with Locale Emulator, otherwise the program will crash.
So the first step should be convert all the scripts to UTF-8 encoding. 
This will be done with the encoding_fix.py script.




"""


# 1 fix the encoding of the scripts and move them to the RawText folder

# 2 Identify the files, pick files with text to be translated only, text that contains the settings should be dealt with later

# 3 Move the files to the "RawText" folder

# 4 Parse all the texts and create corresponding files in "Text" folder that is ready for translation


# ----- after translation -----


# 1 For each file, recreate the class instances and compare with the .csv files in the "Text" folder to check coherence

# 2 Retrive the translated text and replace the original text using the recreate_raw_line function in the Line class

# 2, Repack the files to a new xp3 file
