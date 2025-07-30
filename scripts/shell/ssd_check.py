#!/usr/bin/env python3
"""
SSD Temperature Monitor
Monitors SSD temperature and warns when it's too hot, then waits for cooldown.
"""

import subprocess
import time
import sys
import re
import argparse
from datetime import datetime


def get_ssd_info(device):
    """Get SSD temperature and min/max values using smartctl"""
    try:
        result = subprocess.run(
            ["sudo", "smartctl", "-a", device],
            capture_output=True,
            text=True,
            check=True,
        )

        # Look for Temperature_Celsius or Airflow_Temperature line
        for line in result.stdout.split("\n"):
            if "Temperature_Celsius" in line or "Airflow_Temperature" in line:
                # Parse format: "194 Temperature_Celsius ... - 31 (Min/Max 21/70)"

                # Extract current temperature
                current_temp = None
                words = line.split()
                for i, word in enumerate(words):
                    if "(" in word and i > 0:
                        # Previous word should be the temperature
                        prev_word = words[i - 1]
                        if prev_word.isdigit():
                            current_temp = int(prev_word)
                            break

                # Fallback for current temp
                if current_temp is None:
                    match = re.search(r"-\s*(\d+)\s*\(", line)
                    if match:
                        current_temp = int(match.group(1))

                # Extract min/max from (Min/Max 21/70) format
                min_temp = None
                max_temp = None
                minmax_match = re.search(r"\(Min/Max\s+(\d+)/(\d+)\)", line)
                if minmax_match:
                    min_temp = int(minmax_match.group(1))
                    max_temp = int(minmax_match.group(2))

                if current_temp is not None:
                    return current_temp, min_temp, max_temp

        print("❌ Could not find temperature information in smartctl output")
        return None, None, None

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running smartctl: {e}")
        print("Make sure you have smartmontools installed and sudo access")
        return None, None, None
    except FileNotFoundError:
        print("❌ smartctl not found. Install smartmontools package:")
        print("   sudo apt install smartmontools  # Ubuntu/Debian")
        print("   sudo pacman -S smartmontools    # Arch")
        return None, None, None


def get_ssd_temperature(device):
    """Get just the current SSD temperature"""
    current_temp, _, _ = get_ssd_info(device)
    return current_temp


def format_timestamp():
    """Get formatted timestamp"""
    return datetime.now().strftime("%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor SSD temperature and wait for cooldown"
    )
    parser.add_argument(
        "-d",
        "--device",
        default="/dev/sdb",
        help="SSD device to monitor (default: /dev/sdb)",
    )
    parser.add_argument(
        "--min", type=int, default=30, help="Minimum safe temperature (default: 30°C)"
    )
    parser.add_argument(
        "--max", type=int, default=55, help="Maximum safe temperature (default: 55°C)"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=5,
        help="Check interval in seconds (default: 5)",
    )

    args = parser.parse_args()

    # Get SSD info including actual min/max temperatures
    current_temp, ssd_min_temp, ssd_max_temp = get_ssd_info(args.device)
    if current_temp is None:
        sys.exit(1)

    # Use SSD's actual max temp as warning threshold, or user-provided value
    if ssd_max_temp is not None and not any(
        arg.startswith("--max") for arg in sys.argv[1:]
    ):
        # Use a safety margin: warn at 90% of the SSD's max temp
        warning_temp = int(ssd_max_temp * 0.9)
        print(f"📊 SSD historical range: {ssd_min_temp}°C - {ssd_max_temp}°C")
        print(f"⚠️  Warning threshold: {warning_temp}°C (90% of max)")
    else:
        warning_temp = args.max
        if ssd_max_temp:
            print(f"📊 SSD historical range: {ssd_min_temp}°C - {ssd_max_temp}°C")
        print(f"⚠️  Warning threshold: {warning_temp}°C (user-defined)")

    cooldown_target = (args.min + warning_temp) // 2

    print(f"🔍 SSD Temperature Monitor for {args.device}")
    print(f"🎯 Cooldown target: {cooldown_target}°C")
    print("-" * 50)

    print(f"[{format_timestamp()}] Current temperature: {current_temp}°C")

    # If temperature is within safe range, exit
    if current_temp <= warning_temp:
        print(
            f"✅ SSD temperature is within safe range ({current_temp}°C ≤ {warning_temp}°C)"
        )
        return

    # Temperature is too high - start monitoring
    print(
        f"🚨 WARNING: SSD temperature is too high! ({current_temp}°C > {warning_temp}°C)"
    )
    print(f"🔄 Monitoring temperature every {args.interval} seconds...")
    print(f"⏳ Waiting for temperature to drop to {cooldown_target}°C...")
    print()

    try:
        while True:
            time.sleep(args.interval)

            current_temp = get_ssd_temperature(args.device)
            if current_temp is None:
                print("❌ Failed to read temperature, exiting...")
                sys.exit(1)

            # Show current temperature with visual indicator
            if current_temp > warning_temp:
                indicator = "🔥"
            elif current_temp > cooldown_target:
                indicator = "🌡️"
            else:
                indicator = "❄️"

            print(f"[{format_timestamp()}] {indicator} Temperature: {current_temp}°C")

            # Check if we've reached the cooldown target
            if current_temp <= cooldown_target:
                print()
                print(f"✅ SSD is cool again! Temperature: {current_temp}°C")
                print("🎉 Safe to resume operations")
                break

    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
        current_temp = get_ssd_temperature(args.device)
        if current_temp:
            print(f"📊 Final temperature: {current_temp}°C")


if __name__ == "__main__":
    main()
