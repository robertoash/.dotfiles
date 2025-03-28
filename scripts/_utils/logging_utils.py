# Description: Utility functions for logging configuration.

import inspect
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler


def configure_logging():
    base_scripts_dir = "~/.config/scripts"
    base_log_dir = "~/.config/scripts/_logs"
    log_limit = 30  # Number of log files to keep (one daily)

    # Expand the base directories
    base_scripts_dir_exp = os.path.expanduser(base_scripts_dir)
    base_log_dir_exp = os.path.expanduser(base_log_dir)

    # Determine the calling script directory and name
    caller_frame = inspect.stack()[1]
    caller_path = os.path.abspath(caller_frame.filename)
    caller_dir = os.path.dirname(caller_path)
    caller_filename_no_ext = os.path.splitext(os.path.basename(caller_path))[0]

    # Calculate the target log directory
    relative_log_dir = os.path.relpath(caller_dir, base_scripts_dir_exp)
    log_dir = os.path.join(base_log_dir_exp, relative_log_dir)

    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Set the log file path
    log_file = os.path.join(log_dir, f"{caller_filename_no_ext}.log")

    # Configure the logging module with TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=log_limit
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Add console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add our handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Test logging
    logger.info(f"Logging configured for {caller_filename_no_ext}")
    logger.info(f"Log file: {log_file}")
