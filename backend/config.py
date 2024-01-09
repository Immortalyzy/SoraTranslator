""" configurations """
import json
import os
from constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_INITIATION_PROMPT,
    DEFAULT_FIXING_PROMPT,
    DEFAULT_XP3_UNPACKER,
)


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
    gpt_model = "gpt-3.5-turbo-1106"
    gpt_temperature = 0.3
    gpt_max_lines = 50
    gpt_second_try = False
    gpt_speration_method = "[]"
    gpt_enclosing_joiner = "|"

    # success status
    record_failure_text = True

    # language settings
    original_language = "Japanese"
    target_language = "Chinese"
    if_translate_with_speaker = False

    # set xp3 unpacker
    xp3_unpacker = DEFAULT_XP3_UNPACKER

    def __init__(self):
        self.gpt_prompt = DEFAULT_INITIATION_PROMPT
        self.fixing_prompt = DEFAULT_FIXING_PROMPT

    @classmethod
    def from_json_file(cls, json_file):
        """load config from json"""
        # read all variables from json file if it exists
        instance = cls()
        with open(json_file, "r") as file:
            json_object = json.load(file)
        return instance.from_json_obj(json_object)

    def from_json_obj(self, json_object):
        """load config from json"""
        # read all variables from json file if it exists
        for key, value in json_object.items():
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


default_config = Config()
