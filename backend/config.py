""" configurations """

import json
import os
from constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_INITIATION_PROMPT,
    DEFAULT_FIXING_PROMPT,
    DEFAULT_XP3_UNPACKER,
)
from constants import LogLevel


### Configurations ============================================================
class Config:
    """configuraion class for the backend, saving default configurations"""

    def __init__(self):
        self.proxy = None  # if you need to use a proxy, set it here, format: "socks5://127.0.0.1:10818"
        self.translator = "galtransl"  # use galtransl as the default translator

        # SoraTranslator settings
        self.gpt_prompt = DEFAULT_INITIATION_PROMPT
        self.fixing_prompt = DEFAULT_FIXING_PROMPT
        # see above LogLevel class
        self.log_level_int = DEFAULT_LOG_LEVEL.value

        # gpt translation settings
        self.openai_api_key = "sk-xxx"
        # context number of blocks
        ## set to 1 for no context
        ## set to 0 for no limit (will use maximum number of blocks calculated based on maximum token allowed)
        self.gpt_context_block_count = 4
        self.gpt_max_tokens = 16000
        self.gpt_completion_max_tokens = 8000
        self.gpt_model = "gpt-3.5-turbo-1106"
        self.gpt_temperature = 0.3
        self.gpt_max_lines = 50
        self.gpt_second_try = False
        self.gpt_speration_method = "[]"
        self.gpt_enclosing_joiner = "|"

        # galtransl settings
        self.galtransl_translation_model = "gpt35-1106"

        # success status
        self.translate_line_by_line_in_failure = True
        self.translate_aaaa_by_single_request = True
        self.record_failure_text = True

        # language settings
        self.original_language = "Japanese"
        self.target_language = "Chinese"
        self.if_translate_with_speaker = False

        # set xp3 unpacker
        self.xp3_unpacker = DEFAULT_XP3_UNPACKER

    @classmethod
    def from_json_file(cls, json_file):
        """load config from json"""
        # read all variables from json file if it exists
        instance = cls()
        # test if the file exists
        if not os.path.exists(json_file):
            # save the default config to the file
            print(f"Warning: {json_file} does not exist, creating a new one")
            instance.to_json_file(json_file)
            return instance
        else:
            with open(json_file, "r") as file:
                json_object = json.load(file)
        return instance.from_json_obj(json_object)

    def from_json_obj(self, json_object):
        """load config from json"""
        # read all variables from json file if it exists
        for key, value in json_object.items():
            # check if the variable exists
            if not hasattr(self, key):
                print(f"Warning: {key} is not a valid config variable")
                continue
            setattr(self, key, value)

        # post init
        self.post_init()
        return self

    def to_json_obj(self):
        """save config to json"""
        # save all variables to json object
        json_object = {}
        for key, value in self.__dict__.items():
            json_object[key] = value
        return json_object

    def to_json_file(self, json_file, replace=True):
        """save config to json"""
        if replace:
            with open(json_file, "w") as file:
                json.dump(self.to_json_obj(), file, indent=4)
        else:
            if os.path.exists(json_file):
                return

    def post_init(self):
        """do post init actions"""
        # set the default prompt based on the language configuration
        self.gpt_prompt = DEFAULT_INITIATION_PROMPT
        self.gpt_prompt[0]["content"] = self.gpt_prompt[0]["content"].format(
            self.original_language, self.target_language
        )
        pass

    def log_level(self):
        """return the log level"""
        return LogLevel(self.log_level_int)


default_config = Config()
