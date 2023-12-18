## Chaos-R Parser


### Explaination of the Chaos-R script format 

In Chaos-R games, all text that are displayed together in the game is stored in a single *block*. It starts with a \* symbol with a number after it without apparent end indicator. There will be multiple of lines in a block, recording the information of performation around this text (like the voice to play etc.). 

Some common macros:
- [fc]: This is used to stored functions of changing color for the "alread-read" text. 
- [pcms]: This is used to change the page, clear the text and stop the voice.

### Methods of extraction 
- Speaker (if any) : The speaker of a block is stored in the *[【speaker】]* format. *[]* is the same with all other macros used in the script but *【】* is unique to the speaker.
- Conent : The content is the text in the block that has nothing around them. It has usually a *[pcms]* macro after it. 
