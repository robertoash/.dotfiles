#!/usr/bin/env python3

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

import pytz

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Fetch and display Tibber price information."
)
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Configure logging
logging_utils.configure_logging()
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.ERROR)

# Your Tibber token must be set as an environment variable 'TIBBER_TOKEN'.
TIBBER_TOKEN = os.environ["TIBBER_TOKEN"]


def fetch_prices():

    price_leeway = 0.12  # Percentage of the price range to consider for margin

    command = [
        "curl",
        "-s",
        "-H",
        f"Authorization: Bearer {TIBBER_TOKEN}",
        "-H",
        "Content-Type: application/json",
        "-X",
        "POST",
        "-d",
        '{ "query": "{viewer {home(id: \\"c6a410ee-85a7-4a25-90a7-e328cdcf5aea\\") '
        "{currentSubscription {priceInfo {current {total startsAt} today {total startsAt} "
        'tomorrow {total startsAt}}}}}}" }',
        "https://api.tibber.com/v1-beta/gql",
    ]

    # Execute the command
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout

    # Parse the JSON output
    data = json.loads(output)

    # Extract the current price and all today's prices
    current_price_info = data["data"]["viewer"]["home"]["currentSubscription"][
        "priceInfo"
    ]["current"]
    today_prices = data["data"]["viewer"]["home"]["currentSubscription"]["priceInfo"][
        "today"
    ]
    tomorrow_prices = data["data"]["viewer"]["home"]["currentSubscription"][
        "priceInfo"
    ].get("tomorrow", [])

    # Find the current hour index
    current_time = datetime.now(pytz.timezone("Europe/Stockholm"))
    # Get timezone offset dynamically to handle DST
    tz_offset = current_time.strftime("%z")  # Format: +0200 or +0100
    tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"  # Convert to +02:00 or +01:00 format
    current_hour = current_time.strftime(f"%Y-%m-%dT%H:00:00.000{tz_offset}")

    # Append tomorrow's prices to today's prices if available
    combined_prices = today_prices + tomorrow_prices

    # Filter prices between 7am and 10pm for percentile calculation
    awake_hours = [
        hour for hour in today_prices if 7 <= int(hour["startsAt"][11:13]) <= 22
    ]
    awake_prices = [hour["total"] for hour in awake_hours]

    # Calculate the 25th and 75th percentiles
    def calculate_percentile(prices, percentile):
        prices.sort()
        index = (len(prices) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(prices):
            return prices[lower]
        else:
            return prices[lower] * (upper - index) + prices[upper] * (index - lower)

    percentile_25 = calculate_percentile(awake_prices, 25)
    percentile_75 = calculate_percentile(awake_prices, 75)

    # Calculate dynamic margin as a percentage of the price range
    price_range = max(awake_prices) - min(awake_prices)
    margin = price_leeway * price_range  # Adjust this percentage as needed

    # Ensure the index is found and valid; otherwise, set to a default
    current_hour_index = next(
        (i for i, hour in enumerate(today_prices) if hour["startsAt"] == current_hour),
        None,
    )

    if current_hour_index is None or current_hour_index + 3 >= len(combined_prices):
        return (
            None,
            None,
            None,
            None,
            None,
            "Error: Current hour's index is out of bounds or not found.",
        )

    # Calculate the average of the next three hours
    next_hours = combined_prices[current_hour_index + 1 : current_hour_index + 4]
    next_3_hr_avg = sum(hour["total"] for hour in next_hours) / len(next_hours)

    # Determine if the price will increase or decrease
    price_increases = next_3_hr_avg > current_price_info["total"]

    # Formatting the output
    current_price = current_price_info["total"]
    if current_price < (percentile_25 + margin):
        price_class = "price-green"  # Cheap
    elif current_price > percentile_75:
        price_class = "price-red"  # Expensive
    else:
        price_class = "price-yellow"  # Mid-range

    icon_class = "icon-green" if not price_increases else "icon-red"
    arrow_icon = "" if price_increases else ""

    return current_price, arrow_icon, price_class, icon_class, next_3_hr_avg, None


def main():
    text_output_file = "/tmp/tibber_price_text_output.json"
    icon_output_file = "/tmp/tibber_price_icon_output.json"
    last_text_output = None
    last_icon_output = None
    error_cooldown = 120  # 2 minutes cooldown after error

    logging.debug("Script started.")

    while True:
        current_time = datetime.now(pytz.timezone("Europe/Stockholm"))
        next_hour = (current_time + timedelta(hours=1)).replace(
            minute=1, second=0, microsecond=0
        )
        sleep_duration = (next_hour - current_time).total_seconds()

        current_price, arrow_icon, price_class, icon_class, next_3_hr_avg, error = (
            fetch_prices()
        )

        if error:
            logging.error(error)
            logging.info(
                f"Cooling down for {error_cooldown} seconds before retrying..."
            )
            time.sleep(error_cooldown)
            # Skip rest of loop and try again from start
            continue

        text_output = {
            "text": f"{current_price:.2f}kr",
            "tooltip": f"next 3 hour average: {next_3_hr_avg:.2f}",
            "class": price_class,
        }
        icon_output = {
            "text": f"{arrow_icon}",
            "tooltip": f"next 3 hour average: {next_3_hr_avg:.2f}",
            "class": icon_class,
        }

        if text_output != last_text_output:
            with open(text_output_file, "w") as f:
                json.dump(text_output, f)
            logging.debug(f"Output: {text_output}")
            last_text_output = text_output

        if icon_output != last_icon_output:
            with open(icon_output_file, "w") as f:
                json.dump(icon_output, f)
            logging.debug(f"Output: {icon_output}")
            last_icon_output = icon_output

        # Sleep until the start of the next hour
        time.sleep(sleep_duration)


if __name__ == "__main__":
    main()
