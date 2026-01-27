#!/usr/bin/env python3

import json
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


def parse_speedtest_output(json_str):
    data = json.loads(json_str)
    ping = data["ping"]
    download = float(data["download"]) / 1000000
    upload = float(data["upload"]) / 1000000
    return ping, download, upload


def main():
    output_file = "/tmp/speedtest_output.json"
    interval = 900  # Interval in seconds (15 minutes)

    while True:
        # Call the speedtest++ command and get the output
        result = subprocess.run(
            ["speedtest++", "--output", "json"], capture_output=True, text=True
        )
        if result.returncode == 0:
            json_output = result.stdout
            logging.info("Speedtest++ command completed successfully.")
            logging.debug(f"Speedtest++ output: {json_output}")
            # Parse and write the desired output to a file
            ping, download, upload = parse_speedtest_output(json_output)
            text_string = f"{ping} 󰱠 {download:.2f} 󰛴 {upload:.2f} 󰛶"
            logging.info(f"Parsed output: {text_string}")
            with open(output_file, "w") as f:
                json.dump({"text": f"{text_string}", "tooltip": f"{text_string}"}, f)
        else:
            logging.error(
                f"Speedtest++ command failed with return code {result.returncode}."
            )
            logging.error(f"Error output: {result.stderr}")

        # Wait for the specified interval before running the test again
        time.sleep(interval)


if __name__ == "__main__":
    main()
