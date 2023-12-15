# SoraTranslator
## Automated Translation for Galgames

SoraTranslator is a robust tool designed to extract, translate, and reinsert text in Galgames (Japanese visual novels). This tool primarily automates the translation process for these games, leveraging the capabilities of ChatGPT's API for efficient language conversion.

### Project Overview

SoraTranslator operates by integrating with specific Galgames, focusing on the extraction, translation, and reintegration of game text. It's structured to handle various aspects of this process, from accessing original game resources to generating translated files ready for gameplay.

#### Project Structure

The project is organized as follows:

```
SoraTranslator/
├── Integrators/
│   ├── GameName/
│       ├── Extractor/
│       ├── Parser/
├── Translators/
├── GameResources/
│   ├── OriginalFiles/
│   ├── Texts/
│   ├── TranslatedFiles/
```

Each directory is designed to handle a different stage of the translation process:

- **Integrators**: Contains tools for extracting and parsing game text.
- **Translators**: Dedicated to the translation process.
- **GameResources**: Stores the original game files, extracted text, translated text, and the final translated game files.

---

#### How to Use

To utilize SoraTranslator for different games, particularly from various companies, custom integrators must be written to handle the specific file formats and structures of each game.
The extraction could be empty if you already have the text extracted from the game.
The parser, no matter how it works, should output the text in a uniform format, with the following structure:

```
"narration": "Text to be translated"
"speaker1": "Words to be translated"
"speaker2": "Words to be translated"
...
```

#### Workflow

1. **Extraction**: The integrator accesses the `OriginalFiles` directory, extracting and parsing game text into a readable format in the `Texts` folder.
2. **Translation**: Utilizing the Translator module, the text in `Texts` is then translated, with the results stored in the same file.
3. **Reintegration**: Finally, the integrator takes the translated text in `Texts` and repackages it into the game's format, saving these files in the `TranslatedFiles` directory for use in the game.
