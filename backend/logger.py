"""this file defines the logging mechanism for the project"""

# logger_config.py
import logging
import logging.config
import colorlog
import os

LOG_FILE = "app.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # Colorized output for console
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
        # Standard formatter for log files
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "colorlog.StreamHandler",
            "level": "DEBUG",
            "formatter": "colored",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": LOG_FILE,
            "encoding": "utf8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}


def setup_logger():
    """Initialize colorized logging for the entire app."""
    logging.config.dictConfig(LOGGING_CONFIG)
