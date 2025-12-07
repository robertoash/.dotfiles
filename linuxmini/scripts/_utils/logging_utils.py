# Description: Utility functions for logging configuration.

import inspect
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def configure_logging(quiet=False):
    base_scripts_dir = "/home/rash/.config/scripts"
    
    # Use different log directories for root and user to avoid permission conflicts
    if os.geteuid() == 0:  # Running as root
        base_log_dir = "/home/rash/.config/scripts/_logs/root"
    else:  # Running as regular user
        base_log_dir = "/home/rash/.config/scripts/_logs"
    log_limit = 30  # Number of log files to keep (one daily)

    # Expand the base directories
    base_scripts_dir_exp = Path(base_scripts_dir)
    base_log_dir_exp = Path(base_log_dir)

    # Determine the calling script directory and name
    caller_frame = inspect.stack()[1]
    caller_path = Path(caller_frame.filename).resolve()
    caller_dir = caller_path.parent
    caller_filename_no_ext = caller_path.stem

    # Calculate the target log directory
    # Handle both direct paths and symlinked paths from ~/.dotfiles
    try:
        relative_log_dir = caller_dir.relative_to(base_scripts_dir_exp)
    except ValueError:
        # If script is symlinked from ~/.dotfiles, use a fallback structure
        # Extract the last two path components (e.g., "waybar" from "~/.dotfiles/.../waybar")
        relative_log_dir = Path(caller_dir.parts[-1]) if caller_dir.parts else Path(".")
    log_dir = base_log_dir_exp / relative_log_dir

    # Ensure the log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set the log file path
    log_file = log_dir / f"{caller_filename_no_ext}.log"

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

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handler
    logger.addHandler(file_handler)

    # Add console handler only if not in quiet mode
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)-7s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

    # Test logging
    logger.info(f"Logging configured for {caller_filename_no_ext}")
    logger.info(f"Log file: {log_file}")
