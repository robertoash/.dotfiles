#!/usr/bin/env python3

import logging
import subprocess
import sys
import time

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.info("Script launched.")


def get_mullvad_status():
    return subprocess.check_output(["mullvad", "status"], text=True)


def main():

    # Get mullvad status

    mullvad_status = get_mullvad_status()

    if "Disconnected" in mullvad_status:
        subprocess.run(["mullvad", "connect"])
        # wait for the connection
        time.sleep(2)
        mullvad_status = get_mullvad_status()
        if "Disconnected" in mullvad_status:
            logging.error("Failed to connect to Mullvad.")
        else:
            subprocess.run(["notify-send", mullvad_status])
    else:
        subprocess.run(["mullvad", "disconnect"])
        # wait for the connection
        time.sleep(2)
        mullvad_status = get_mullvad_status()
        if "Disconnected" in mullvad_status:
            subprocess.run(["notify-send", mullvad_status])
        else:
            logging.error("Failed to disconnect from Mullvad.")


if __name__ == "__main__":
    main()
