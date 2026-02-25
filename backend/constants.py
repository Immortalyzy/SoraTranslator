"""contants that are used in the backend"""

from enum import Enum
import os

# Get the directory of this constants.py file
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
_DEFAULT_GAME_RESOURCES_ROOT = os.path.join(_PROJECT_ROOT, "SoraTranslator")

# Path specific
DEFAULT_GAME_RESOURCES_DIRECTORY = _DEFAULT_GAME_RESOURCES_ROOT + os.sep
DEFAULT_ENCODING_OUTPUT = os.path.join(_DEFAULT_GAME_RESOURCES_ROOT, "RawText") + os.sep
DEFAULT_GAME_RESOURCES_RAWTEXT_DIRECTORY = os.path.join(_DEFAULT_GAME_RESOURCES_ROOT, "RawText") + os.sep
DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY = os.path.join(_DEFAULT_GAME_RESOURCES_ROOT, "Text") + os.sep
DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY = os.path.join(_DEFAULT_GAME_RESOURCES_ROOT, "TranslatedFiles") + os.sep
DEFAULT_XP3_UNPACKER = os.path.join(_CURRENT_DIR, "Integrators/utils/xp3_upk.exe")

# Log and config files
DEFAULT_LOG_FILE = os.path.join(_PROJECT_ROOT, "backend_log.txt")
DEFAULT_CONFIG_TEMPLATE_FILE = os.path.join(_PROJECT_ROOT, "config.template.json")
DEFAULT_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "config.json")
DEFAULT_USER_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "config.user.json")
DEFAULT_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")

# GPT API
LINE_BREAKER = "||"
DEFAULT_INITIATION_PROMPT = [
    {
        "role": "system",
        "content": "You are a translator that translates a part of a fantasy story with conversations and narration while trying to keep the original text format. "
        + "Unless specific intructed, assume all characters are female.  "
        + "Plase translate from {} to {}. "
        + " Please KEEP the surrounding symbols [ and ] of sentences in the translated text."
        + " Each [ ] indicates a block and try to return the same number of blocks in the translated text.",
    },
]
DEFAULT_FIXING_PROMPT = [
    {
        "role": "user",
        "content": "The number of the line breakers doesn't match in your translation (there are {:.0f} while there should be {:.0f}). "
        + "Please check your translation and try again.",
    }
]


class SuccessStatus(Enum):
    """success status"""

    # if 100% translated
    SUCCESS = 0
    # if >=80% translated
    ALMOST_SUCCESS = 1
    # if >=50% <80% translated
    PARTIAL_SUCCESS = 2
    # if < 50% translated
    ERROR = 3

    @staticmethod
    def status_from_ratio(ratio):
        """get the status from the ratio"""
        if ratio >= 0.999:
            return SuccessStatus.SUCCESS
        elif ratio >= 0.8:
            return SuccessStatus.ALMOST_SUCCESS
        elif ratio >= 0.5:
            return SuccessStatus.PARTIAL_SUCCESS
        else:
            return SuccessStatus.ERROR
