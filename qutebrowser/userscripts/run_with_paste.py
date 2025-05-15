#!/usr/bin/env python3
import argparse
import os
import subprocess

PASTE_DELAY = 500  # In milliseconds to match cmd-later


def run(script, script_args):
    try:
        # Run the script with output capture
        result = subprocess.run(
            [script, *script_args],
            check=True,
            text=True,
            capture_output=True,  # This captures stdout and stderr
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        return None


def paste(result=None, paste_delay=PASTE_DELAY):
    try:
        # After script completes, send the paste command to qutebrowser
        with open(os.environ["QUTE_FIFO"], "w") as fifo:
            # Default to fake-key if no method provided or clipboard specified
            fifo.write(f"cmd-later {paste_delay} fake-key <Ctrl-v>\n")
            print("Pasted clipboard contents.")
    except Exception as e:
        print(f"Error pasting: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, help="The script to run")
    parser.add_argument(
        "--paste-delay",
        help="The delay in milliseconds to wait before pasting",
        default=PASTE_DELAY,
    )
    parser.add_argument("args", nargs="*", help="Arguments for the script")
    args = parser.parse_args()

    # Print debug info
    print(f"Running script: {args.script}")
    print(f"With args: {args.args}")

    result = run(args.script, args.args)
    paste(result, args.paste_delay)


if __name__ == "__main__":
    main()
