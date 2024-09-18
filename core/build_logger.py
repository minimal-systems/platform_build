import logging
import time
import os
import threading

# ANSI escape sequences for colors
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_RESET = "\033[0m"

class LogcatFormatter(logging.Formatter):
    LEVEL_MAP = {
        logging.DEBUG: 'D',
        logging.INFO: 'I',
        logging.WARNING: 'W',
        logging.ERROR: 'E',
        logging.CRITICAL: 'F'
    }

    def format(self, record):
        log_level = self.LEVEL_MAP.get(record.levelno, 'I')
        timestamp = time.strftime('%m-%d %H:%M:%S', time.localtime(record.created))
        pid = os.getpid()
        # Format thread ID as a short hexadecimal value
        tid = f"{threading.get_ident() & 0xFFFF:04X}"
        tag = record.name

        color = {
            'D': COLOR_BLUE,
            'I': COLOR_GREEN,
            'W': COLOR_YELLOW,
            'E': COLOR_RED,
            'F': COLOR_RED
        }.get(log_level, COLOR_RESET)

        message = super().format(record)
        return f"{timestamp} {pid} {tid} {log_level} {tag}: {color}{message}{COLOR_RESET}"

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = LogcatFormatter('%(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)

# Logging utility functions with log_tag support
def pr_debug(message, log_tag=None):
    if log_tag:
        logger.debug(f"{log_tag}: {message}")
    else:
        logger.debug(message)

def pr_info(message, log_tag=None):
    if log_tag:
        logger.info(f"{log_tag}: {message}")
    else:
        logger.info(message)

def pr_warning(message, log_tag=None):
    if log_tag:
        logger.warning(f"{log_tag}: {message}")
    else:
        logger.warning(message)

def pr_error(message, log_tag=None):
    if log_tag:
        logger.error(f"{log_tag}: {message}")
    else:
        logger.error(message)

def pr_critical(message, log_tag=None):
    if log_tag:
        logger.critical(f"{log_tag}: {message}")
    else:
        logger.critical(message)

