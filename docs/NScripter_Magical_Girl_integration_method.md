## Magical☆Girl Game Integration Method

### Introduction
- **Official Website**: [Magical☆Girl](http://www.magical-girl.jp/)
- **Game Engine**: Nscripter

### Integration Method

1. **Extraction**:
    - Use the built-in method of SoraTranslator.
    - Place the game definition file in the game folder.
    - Ensure the `FIRST_BLOCK` entry is present in the file. If extraction fails, open the raw text, locate the first block, and update the `FIRST_BLOCK` entry accordingly. Rerun the initiation process.

2. **Translation**:
    - Follow the standard translation process in SoraTranslator.
    - Note: NScripter does not support English characters or half-width numbers in the translated text.

3. **Integration**:
    - Click the integration button in SoraTranslator.
    - SoraTranslator will create an `nscript` folder under `game_folder/SoraTranslatorTemp`.
    - A directory chooser will appear; select this folder.
    - Save the `nscript.dat` file when prompted. Replace the original `nscript.dat` file in the game folder with this new file.

4. **Game Executable Encoding Change**:
    - This step is complex and requires using Ollydbg.
    - Set a breakpoint for the `CreateFontA` function to locate the font settings.
    - Change the value `0x80` to `0x86` for all relevant cases (character names, text, choices, etc.).
    - Save the changes and run the game.
    - For a detailed guide, refer to this [video tutorial](https://www.bilibili.com/video/BV1fy4y157im/) (in Chinese).
