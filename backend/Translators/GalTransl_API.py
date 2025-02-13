""" This file defines the API used to interact with GalTransl """

import sys
import os
import shutil
import subprocess
import yaml
from datetime import datetime
from openai import OpenAI
from project import Project
from textfile import TextFile
from block import Block
from config import Config, default_config
from constants import SuccessStatus as success
from constants import LogLevel
from logger import log_message
from . import utils
from . import utils_post
from .translator import Translator


def sync_config_to_yaml(config: Config, yaml_file: str):
    """sync the config to the yaml file"""
    # open the yaml file
    with open(yaml_file, "r", encoding="utf-8") as file:
        yaml_object = yaml.load(file, Loader=yaml.FullLoader)

    try:
        # proxy settings
        if config.proxy is not None:
            yaml_object["proxy"]["enableProxy"] = True
            yaml_object["proxy"]["proxies"][0]["address"] = config.proxy
        else:
            yaml_object["proxy"]["enableProxy"] = False

        # openai settings
        yaml_object["backendSpecific"]["GPT35"]["tokens"][0]["token"] = config.openai_api_key
        # delete the second token
        del yaml_object["backendSpecific"]["GPT35"]["tokens"][1]

        # same for GPT4 settings
        yaml_object["backendSpecific"]["GPT4"]["tokens"][0]["token"] = config.openai_api_key

    except Exception as e:
        log_message(f"Error: {e}", LogLevel.ERROR)
        print(f"Error: {e}")

    # save the yaml file
    with open(yaml_file, "w", encoding="utf-8") as file:
        yaml.dump(yaml_object, file, default_flow_style=False, sort_keys=False, allow_unicode=True)


class GalTranslAPI(Translator):
    """API to interact with GalTransl"""

    def __init__(self, config: Config = default_config, project: Project = None):
        super().__init__(config)

        # generate the roor path of GalTransl
        this_path = os.path.dirname(os.path.abspath(__file__))
        self.galtransl_path = os.path.join(this_path, "GalTransl")
        # add the GalTransl path to the system path
        sys.path.insert(0, self.galtransl_path)
        from GalTransl import CONFIG_FILENAME

        # create a project config .yaml file
        ## copy the default config to the project directory
        self.project = project

        # generate tempate config path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_yaml_config_path = os.path.join(script_dir, "GalTransl/sampleProject/config.inc.yaml")
        target_yaml_config_path = os.path.join(project.project_path, CONFIG_FILENAME)
        # copy the template config to the project directory
        shutil.copyfile(template_yaml_config_path, target_yaml_config_path)

        # sync the config file from config to the yaml file, the API key, etc.
        sync_config_to_yaml(config, target_yaml_config_path)
        self.yaml_config_path = target_yaml_config_path

        # create the GalTransl folders
        self.gt_input_folder = os.path.join(project.project_path, "gt_input")
        self.gi_output_folder = os.path.join(project.project_path, "gt_output")
        # mkdir the folders
        os.makedirs(self.gt_input_folder, exist_ok=True)
        os.makedirs(self.gi_output_folder, exist_ok=True)

    def translate_file_whole(self, text_file: TextFile) -> success:
        """Not implemented as GalTransl is intended for translating the whole project"""
        raise RuntimeError("Not implemented")

    def translate_block(self, block: Block, context: str = None):
        """Not implemented as GalTransl is intended for translating the whole project"""
        raise RuntimeError("Not implemented")

    def translate_project(self):
        """translate the project using GalTransl"""

        # generate the galtransl json files for translation

        # generate the galtransl dictionary for better translation

        # dynamically import GalTransl
        from GalTransl.__main__ import worker
        from GalTransl import (
            AUTHOR,
            CONFIG_FILENAME,
            CONTRIBUTORS,
            GALTRANSL_VERSION,
            PROGRAM_SPLASH,
        )

        # print tribute_message
        tribute_message = f"""echo {PROGRAM_SPLASH}
        echo Ver: {GALTRANSL_VERSION}
        echo Author: {AUTHOR}
        echo Contributors: {CONTRIBUTORS}
        echo This message will self-destruct in 5 seconds...
        timeout /t 5 >nul
        exit
        """
        subprocess.Popen(["cmd", "/K", tribute_message], shell=True)

        # call GalTransl
        original_path = os.getcwd()
        os.chdir(self.galtransl_path)
        try:
            worker(self.project.project_path, CONFIG_FILENAME, self.config.galtransl_translator, show_banner=False)
        except Exception as e:
            log_message(f"Error: {e}", LogLevel.ERROR)
            print(f"Error: {e}")
        finally:
            os.chdir(original_path)

        # rewrite the translated files (sync to textfile instances)

        # return the success status
