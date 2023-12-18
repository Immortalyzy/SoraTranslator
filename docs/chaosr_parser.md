## Chaos-R Parser


### Explaination of the Chaos-R script format 

In Chaos-R games, all text that are displayed together in the game is stored in a single *block*. It starts with a \* symbol with a number after it without apparent end indicator. There will be multiple of lines in a block, recording the information of performation around this text (like the voice to play etc.). 

Some common macros:
- [fc]: This is used to stored functions of changing color for the "alread-read" text. 
- [pcms]: This is used to change the page, clear the text and stop the voice.

### Methods of extraction 
- Speaker (if any) : The speaker of a block is stored in the *[【speaker】]* format. *[]* is the same with all other macros used in the script but *【】* is unique to the speaker.
- Content : The content is the text in the block that has nothing around them. It has usually a *[pcms]* macro after it. 

### Methods of integration
For the replacement of the translated text, it is simple. When extracting the speaker and content, the start-end places will be recorded. The original text will first be deleted and then the translated text will be inserted.
Note that since we are not certain about the case of others games, we'll for now assume that the main text will possibly be in stored in multiple lines. The positions of the text will include the start and end line number. (Multi-line conditions are not considered here so a mere check will be written but full mechanism will not be implemented.)

This method of extraction will omit the text outside any blocks. In the case of Chaos-R, it is only the text at the beginning of the script file. But for general purpose, the ScriptFile class should have a list storing all the text BEFORE any blocks. 

