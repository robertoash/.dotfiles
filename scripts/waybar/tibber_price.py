#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime

import pytz

# Your Tibber token must be set as an environment variable 'TIBBER_TOKEN'.
TIBBER_TOKEN = os.environ["TIBBER_TOKEN"]

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
current_price_info = data["data"]["viewer"]["home"]["currentSubscription"]["priceInfo"][
    "current"
]
today_prices = data["data"]["viewer"]["home"]["currentSubscription"]["priceInfo"][
    "today"
]

# Find the current hour index
current_time = datetime.now(pytz.timezone("Europe/Stockholm"))
current_hour = current_time.strftime(
    "%Y-%m-%dT%H:00:00.000+02:00"
)  # Adjust timezone format if necessary

current_hour_index = next(
    (i for i, hour in enumerate(today_prices) if hour["startsAt"] == current_hour), None
)

# Ensure the index is found and valid; otherwise, set to a default
if current_hour_index is None or current_hour_index + 3 >= len(today_prices):
    print("Error: Current hour's index is out of bounds or not found.")
else:
    # Calculate the average of the next three hours
    next_hours = today_prices[current_hour_index + 1 : current_hour_index + 4]
    next_3_hr_avg = sum(hour["total"] for hour in next_hours) / len(next_hours)

    # Determine if the price will increase or decrease
    price_increases = next_3_hr_avg > current_price_info["total"]

    # Formatting the output
    current_price = current_price_info["total"]
    if price_increases:
        print(
            f'{{"text": "{current_price:.2f}kr ", "tooltip": "next 3 hour average: {next_3_hr_avg:.2f}", "class": "tibber-increase"}}'
        )
    else:
        print(
            f'{{"text": "{current_price:.2f}kr ", "tooltip": "next 3 hour average: {next_3_hr_avg:.2f}", "class": "tibber-decrease"}}'
        )
