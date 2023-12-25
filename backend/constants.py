""" contants that are used in the backend """
from enum import Enum
import json

# Path specific
DEFAULT_GAME_RESOURCES_DIRECTORY = "D:/Work/SoraTranslator/GameResources/"
DEFAULT_ENCODING_OUTPUT = "D:/Work/SoraTranslator/GameResources/RawText/"
DEFAULT_GAME_RESOURCES_RAWTEXT_DIRECTORY = (
    "D:/Work/SoraTranslator/GameResources/RawText/"
)
DEFAULT_GAME_RESOURCES_TEXT_DIRECTORY = "D:/Work/SoraTranslator/GameResources/Text/"
DEFAULT_GAME_RESOURCES_TRANSLATED_FILES_DIRECTORY = (
    "D:/Work/SoraTranslator/GameResources/TranslatedFiles/"
)

DEFAULT_XP3_UNPACKER = "D:/Work/SoraTranslator/backend/Integrators/utils/xp3_upk.exe"


def create_game_resources_directory(game_resources_directory: str) -> ():
    """create the game resources directory, generating the subfolders"""
    # todo: implement this
    pass


# Log file
DEFAULT_LOG_FILE = "D:/Work/SoraTranslator/backend/log.txt"
DEFAULT_CONFIG_FILE = "D:/Work/SoraTranslator/config.json"

# GPT API
LINE_BREAKER = "||"
DEFAULT_INITIATION_PROMPT = [
    {
        "role": "system",
        "content": "You are a translator of fantasy stories. Plase translate from {} to {}. KEEP the surroundings \[ \] of sentences in the translated text and return the same number of blocks in the translated text.",
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
RAW_TEXT_DIRECTORY = "D:/Work/SoraTranslator/GameResources/RawText/"


### Configurations ============================================================
class Config:
    """configuraion class for the backend, saving default configurations"""

    # see above LogLevel class
    log_level = DEFAULT_LOG_LEVEL

    # gpt translation settings
    openai_api_key = "sk-xxx"
    # context number of blocks
    ## set to 1 for no context
    ## set to 0 for no limit (will use maximum number of blocks calculated based on maximum token allowed)
    gpt_context_block_count = 4
    gpt_max_tokens = 16000
    gpt_completion_max_tokens = 8000
    gpt_model = "gpt-3.5-turbo-16k"
    gpt_temperature = 0.3
    gpt_max_lines = 50
    gpt_second_try = False

    # success status
    record_failure_text = True

    # language settings
    original_language = "Japanese"
    target_language = "Chinese"
    if_translate_with_speaker = False

    def __init__(self):
        self.gpt_prompt = DEFAULT_INITIATION_PROMPT
        self.fixing_prompt = DEFAULT_FIXING_PROMPT

    @classmethod
    def from_json(cls, json_file):
        """load config from json"""
        # read all variables from json file if it exists
        instance = cls()
        with open(json_file, "r") as file:
            json_object = json.load(file)
        for key, value in json_object.items():
            setattr(instance, key, value)

        # post init
        instance.post_init()
        return instance

    def post_init(self):
        """do post init actions"""
        # set the default prompt based on the language configuration
        self.gpt_prompt = DEFAULT_INITIATION_PROMPT
        self.gpt_prompt[0]["content"] = self.gpt_prompt[0]["content"].format(
            self.original_language, self.target_language
        )
        pass

    def to_json(self, json_file, replace=True):
        """save config to json"""
        # todo:implement this


default_config = Config()
