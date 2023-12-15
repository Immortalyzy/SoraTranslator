""" 
This script provides the encoding fix for the games of Chaos-R. 
The encoding of the text content of the games of Chaos-R is Shift-JIS. 
In order to run it directly without using Locale Emulator, we need to convert the encoding of the text content from Shift-JIS to UTF-8 (or UTF-16LF).

This script will at first extract all the script files with following extensions to a new folder named (scripts_utf8):
.asd
.func
.ks
.txt
.ini
.csv

Then the script will convert the encoding of these files from Shift-JIS to UTF-8 (or UTF-16LF).
"""
