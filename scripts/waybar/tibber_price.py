#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from datetime import datetime

import pytz


def fetch_prices():
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
    current_hour = current_time.strftime("%Y-%m-%dT%H:00:00.000+02:00")

    # Append tomorrow's prices to today's prices if available
    combined_prices = today_prices + tomorrow_prices

    # Filter prices between 7am and 10pm for percentile calculation
    awake_hours = [
        hour for hour in today_prices if 7 <= int(hour["startsAt"][11:13]) <= 22
    ]
    awake_prices = [hour["total"] for hour in awake_hours]

    # Calculate the 25th percentile
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
            "Error: Current hour's index is out of bounds or not found.",
        )

    # Calculate the average of the next three hours
    next_hours = combined_prices[current_hour_index + 1 : current_hour_index + 4]
    next_3_hr_avg = sum(hour["total"] for hour in next_hours) / len(next_hours)

    # Determine if the price will increase or decrease
    price_increases = next_3_hr_avg > current_price_info["total"]

    # Formatting the output
    current_price = current_price_info["total"]
    price_class = "price-green" if current_price < percentile_25 else "price-red"
    icon_class = "icon-green" if not price_increases else "icon-red"
    arrow_icon = "" if price_increases else ""

    return current_price, arrow_icon, price_class, icon_class, next_3_hr_avg, None


def main():
    part = sys.argv[1]
    current_price, arrow_icon, price_class, icon_class, next_3_hr_avg, error = (
        fetch_prices()
    )

    if error:
        print(error)
        return

    if part == "--text":
        print(
            json.dumps(
                {
                    "text": f"{current_price:.2f}kr",
                    "tooltip": f"next 3 hour average: {next_3_hr_avg:.2f}",
                    "class": price_class,
                }
            )
        )
    elif part == "--icon":
        print(
            json.dumps(
                {
                    "text": f"{arrow_icon}",
                    "tooltip": f"next 3 hour average: {next_3_hr_avg:.2f}",
                    "class": icon_class,
                }
            )
        )


if __name__ == "__main__":
    main()
