""" this file defines the logging mechanism for the project """
from config import default_config


def log_message(message, log_level=default_config.log_level):
    """log the message to the log file"""
    # todo: implement real logging. the config file should contain log file path
    # config file position should be fixed
    if log_level.value <= default_config.log_level.value:
        print(message)
        # with open(LOG_FILE, "a") as f:
        #    f.write(message + "\n")
