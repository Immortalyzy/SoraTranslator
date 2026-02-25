"""configurations"""

from copy import deepcopy
import json
import os
from logging import getLogger

from dotenv import load_dotenv

from constants import (
    DEFAULT_CONFIG_FILE,
    DEFAULT_CONFIG_TEMPLATE_FILE,
    DEFAULT_ENV_FILE,
    DEFAULT_FIXING_PROMPT,
    DEFAULT_INITIATION_PROMPT,
    DEFAULT_USER_CONFIG_FILE,
    DEFAULT_XP3_UNPACKER,
)

logger = getLogger(name=__name__)


class Config:
    """Configuration class for backend runtime and user settings."""

    SENSITIVE_FIELDS = {"openai_api_key", "token"}
    SENSITIVE_PREFIXES = ("sk-", "xai-", "AIza", "hf_")

    ENV_OVERRIDES = {
        "OPENAI_API_KEY": "openai_api_key",
        "SORA_TRANSLATOR": "translator",
        "SORA_ENDPOINT_NAME": "endpoint_name",
        "SORA_MODEL_NAME": "model_name",
        "SORA_ENDPOINT": "endpoint",
        "SORA_TOKEN": "token",
        "SORA_PROXY": "proxy",
    }

    def __init__(self):
        # proxy format example: "socks5://127.0.0.1:10818"
        self.proxy = None
        self.translator = "galtransl"  # use galtransl as the default translator

        # SoraTranslator settings
        self.gpt_prompt = deepcopy(DEFAULT_INITIATION_PROMPT)
        self.fixing_prompt = deepcopy(DEFAULT_FIXING_PROMPT)

        # gpt translation settings
        self.openai_api_key = "ENV:OPENAI_API_KEY"
        # context number of blocks
        ## set to 1 for no context
        ## set to 0 for no limit (will use maximum number of blocks calculated based on maximum token allowed)
        self.gpt_context_block_count = 4
        self.gpt_max_tokens = 16000
        self.gpt_completion_max_tokens = 8000
        self.gpt_model = "gpt-4o-mini"
        self.gpt_temperature = 0.3
        self.gpt_max_lines = 50
        self.gpt_second_try = False
        self.gpt_speration_method = "[]"
        self.gpt_enclosing_joiner = "|"

        # model settings
        self.endpoint_name = "OpenAI"
        self.model_name = "gpt-4o-mini"
        self.endpoint = "https://api.openai.com/v1/"
        self.token = "ENV:OPENAI_API_KEY"

        # galtransl settings
        self.galtransl_translation_method = "ForGal-json"

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

    @staticmethod
    def _is_plaintext_secret(key, value):
        if key not in Config.SENSITIVE_FIELDS or not isinstance(value, str):
            return False
        if value.startswith("ENV:"):
            return False
        return value.startswith(Config.SENSITIVE_PREFIXES)

    @staticmethod
    def _resolve_env_token(value):
        if isinstance(value, str) and value.startswith("ENV:"):
            env_name = value.split(":", 1)[1]
            return os.getenv(env_name, "")
        return value

    @staticmethod
    def _load_json_dict(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except FileNotFoundError:
            return None
        if not isinstance(payload, dict):
            logger.warning("Warning: %s should contain a JSON object; ignored.", json_file)
            return None
        return payload

    @classmethod
    def load_runtime(
        cls,
        config_files=None,
        env_file=DEFAULT_ENV_FILE,
        resolve_env_tokens=True,
    ):
        """Load runtime config with precedence: defaults -> files -> environment."""
        load_dotenv(env_file, override=False)

        if config_files is None:
            config_files = [DEFAULT_CONFIG_TEMPLATE_FILE, DEFAULT_CONFIG_FILE, DEFAULT_USER_CONFIG_FILE]

        instance = cls()
        for cfg_path in config_files:
            json_obj = cls._load_json_dict(cfg_path)
            if not json_obj:
                continue

            for key, value in json_obj.items():
                if not hasattr(instance, key):
                    logger.warning("Warning: unknown config key '%s' in %s; ignored.", key, cfg_path)
                    continue

                if cls._is_plaintext_secret(key, value):
                    logger.warning(
                        "Legacy plaintext secret detected in %s for key '%s'. Migrate to ENV:<KEY> token.",
                        cfg_path,
                        key,
                    )

                resolved_value = cls._resolve_env_token(value) if resolve_env_tokens else value
                setattr(instance, key, resolved_value)

        for env_name, attr in cls.ENV_OVERRIDES.items():
            env_value = os.getenv(env_name)
            if env_value:
                setattr(instance, attr, env_value)

        instance.post_init()
        return instance

    @classmethod
    def from_json_file(cls, json_file):
        """Load config from one JSON file and apply defaults for missing fields."""
        instance = cls()
        if not os.path.exists(json_file):
            print(f"Warning: {json_file} does not exist, creating a new one")
            instance.to_json_file(json_file)
            return instance

        json_object = cls._load_json_dict(json_file) or {}
        return instance.from_json_obj(json_object)

    def update_from_json_file(self, json_file):
        """Update existing attributes from a JSON file and return self."""
        data = self._load_json_dict(json_file)
        if data is None:
            logger.warning("Warning: %s does not exist; no updates applied.", json_file)
            return self

        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning("Warning: unknown config key '%s' in %s; ignored.", key, json_file)

        logger.debug("Updated config file %s, current configurations: %s", json_file, self.to_json_obj())
        return self

    def from_json_obj(self, json_object):
        """Load config values from an object into current instance."""
        for key, value in json_object.items():
            if not hasattr(self, key):
                logger.warning("Warning: %s is not a valid config variable", key)
                continue
            setattr(self, key, value)

        self.post_init()
        return self

    def to_json_obj(self):
        """Export config as a JSON-compatible object."""
        return dict(self.__dict__)

    def to_json_file(self, json_file, replace=True):
        """Save config to JSON file."""
        if not replace and os.path.exists(json_file):
            return

        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(self.to_json_obj(), file, indent=4, ensure_ascii=False)

    def post_init(self):
        """Post-init actions after values are loaded."""
        # Set the default prompt based on the language configuration.
        self.gpt_prompt = deepcopy(DEFAULT_INITIATION_PROMPT)
        self.gpt_prompt[0]["content"] = self.gpt_prompt[0]["content"].format(
            self.original_language, self.target_language
        )


CONFIG = Config()
