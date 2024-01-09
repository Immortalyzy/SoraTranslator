""" contants that are used in the backend """
from enum import Enum

# Path specific
DEFAULT_GAME_RESOURCES_DIRECTORY = "D:/Work/SoraTranslator/SoraTranslator/"
DEFAULT_ENCODING_OUTPUT = "D:/Work/SoraTranslator/SoraTranslator/RawText/"
DEFAULT_GAME_RESOURCES_RAWTEXT_DIRECTORY = (
    "D:/Work/SoraTranslator/SoraTranslator/RawText/"
)
DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY = "D:/Work/SoraTranslator/SoraTranslator/Text/"
DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY = (
    "D:/Work/SoraTranslator/SoraTranslator/TranslatedFiles/"
)

DEFAULT_XP3_UNPACKER = "D:/Work/SoraTranslator/backend/Integrators/utils/xp3_upk.exe"

# Log file
DEFAULT_LOG_FILE = "../backend_log.txt"
DEFAULT_CONFIG_FILE = "../config.json"

# GPT API
LINE_BREAKER = "||"
DEFAULT_INITIATION_PROMPT = [
    {
        "role": "system",
        "content": "You are a translator that translates a part of a fantasy story with conversations and narration while trying to keep the original text format. "
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


class LogLevel(Enum):
    """log level"""

    ERROR = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3
    VERBOSE = 4


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


DEFAULT_LOG_LEVEL = LogLevel.DEBUG


# log config, after project.py is implemented, this should be moved to project.py
RAW_TEXT_DIRECTORY = "D:/Work/SoraTranslator/SoraTranslator/RawText/"
