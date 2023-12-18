""" contants that are used in the backend """
from enum import Enum

# Path specific
DEFAULT_GAME_RESOURCES_DIRECTORY = "D:/Work/SoraTranslator/GameResources/"
DEFAULT_ENCODING_OUTPUT = "D:/Work/SoraTranslator/GameResources/RawText/"
DEFAULT_GAME_RESOURCES_RAWTEXT_DIRECTORY = "D:/Work/SoraTranslator/GameResources/RawText/"
DEFAULT_TEXT_FOLDER = "D:/Work/SoraTranslator/GameResources/Text/"
DEFAULT_TRANSLATED_FILES_FOLDER = (
    "D:/Work/SoraTranslator/GameResources/TranslatedFiles/"
)

DEFAULT_XP3_UNPACKER = "D:/Work/SoraTranslator/backend/Integrators/utils/xp3_upk.exe"



# Log file
LOG_FILE = "D:/Work/SoraTranslator/backend/log.txt"
class LogLevel(Enum):
    """ log level """
    ERROR = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3
    VERBOSE = 4

DEFAULT_LOG_LEVEL = LogLevel.DEBUG
