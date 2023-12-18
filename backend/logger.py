""" this file defines the logging mechanism for the project """
from .constants import LOG_FILE, DEFAULT_LOG_LEVEL, LogLevel

# TODO: when the config module is ready, read the log level from config
config_log_level = DEFAULT_LOG_LEVEL


def log_message(message, log_level=LogLevel.ERROR):
    """ log the message to the log file """
    if log_level.value <= config_log_level.value:
        print(message)
        #with open(LOG_FILE, "a") as f:
        #    f.write(message + "\n")
