#!/usr/bin/env python3

import argparse
import os
import pty
import re
import subprocess
import sys

COLUMN_GAP = 4  # Number of spaces between columns
DEFAULT_PATTERN = [
    0,
    1,
    2,
    4,
    3,
    5,
    6,
    8,
    7,
    9,
]  # Default pattern for block arrangement


def strip_ansi_codes(text):
    """Remove ANSI color codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_escape.sub("", text)


def get_visible_length(text):
    """Get the visible length of text, accounting for box-drawing characters."""
    # Remove ANSI codes first
    text = strip_ansi_codes(text)
    # Count box-drawing characters as 1 unit
    return len(text.replace("▀", " ").replace("▀", " "))


def parse_pattern(pattern_str):
    """Parse pattern string into list of integers."""
    try:
        return [int(x) for x in pattern_str]
    except ValueError:
        print("❌ Error: Pattern must contain only digits", file=sys.stderr)
        sys.exit(1)


def run_pastel(args, pattern):
    try:
        # Create a pseudo-terminal
        master, slave = pty.openpty()
        # Set terminal type
        os.environ["TERM"] = "xterm-256color"

        # Run pastel in the pseudo-terminal
        process = subprocess.Popen(
            ["pastel"] + args, stdout=slave, stderr=slave, text=True, close_fds=True
        )

        # Close slave fd, we'll read from master
        os.close(slave)

        # Read output from the master fd
        output = ""
        while True:
            try:
                chunk = os.read(master, 1024).decode()
                if not chunk:
                    break
                output += chunk
            except OSError:
                break

        # Wait for process to complete
        process.wait()
        os.close(master)

        # Process the output
        lines = output.splitlines()
        if len(lines) < 2:  # Need at least 2 lines to have meaningful blocks
            print(output, end="")
            return

        # Print first line (preserve padding)
        print(lines[0])

        # Collect blocks
        blocks = []
        current_block = []

        # Process middle lines
        for i in range(1, len(lines) - 1):
            line = lines[i]
            if not line.strip() and any(
                lines[j].strip() for j in range(i + 1, len(lines) - 1)
            ):
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                # Strip whitespace from non-empty lines
                current_block.append(line.strip() if line.strip() else line)

        # Add the last block if exists
        if current_block:
            blocks.append(current_block)

        # Find the maximum height of any block
        max_height = max(len(block) for block in blocks)

        # Calculate number of rows (2 blocks per row)
        rows = (len(blocks) + 1) // 2

        # Calculate maximum width for left and right blocks (including padding)
        left_max_width = 0
        right_max_width = 0
        for r in range(rows):
            # Get indices from pattern
            left_idx = pattern[r * 2] if r * 2 < len(pattern) else None
            right_idx = pattern[r * 2 + 1] if r * 2 + 1 < len(pattern) else None

            # Calculate max width for left blocks
            if left_idx is not None and left_idx < len(blocks):
                left_block = blocks[left_idx]
                block_max_width = max(get_visible_length(line) for line in left_block)
                left_max_width = max(left_max_width, block_max_width)

            # Calculate max width for right blocks
            if right_idx is not None and right_idx < len(blocks):
                right_block = blocks[right_idx]
                block_max_width = max(get_visible_length(line) for line in right_block)
                right_max_width = max(right_max_width, block_max_width)

        # Add padding to left_max_width
        left_max_width += COLUMN_GAP

        # Arrange blocks in the specified pattern
        for r in range(rows):
            # Get indices from pattern
            left_idx = pattern[r * 2] if r * 2 < len(pattern) else None
            right_idx = pattern[r * 2 + 1] if r * 2 + 1 < len(pattern) else None

            # Get the blocks for this row
            left_block = (
                blocks[left_idx]
                if left_idx is not None and left_idx < len(blocks)
                else []
            )
            right_block = (
                blocks[right_idx]
                if right_idx is not None and right_idx < len(blocks)
                else []
            )

            # Pad blocks to same height
            left_block = left_block + [""] * (max_height - len(left_block))
            right_block = right_block + [""] * (max_height - len(right_block))

            # Print the blocks side by side
            for left_line, right_line in zip(left_block, right_block):
                # Calculate padding needed based on visible text length for both blocks
                left_visible_length = get_visible_length(left_line)
                left_padding = left_max_width - left_visible_length

                right_visible_length = get_visible_length(right_line)
                right_padding = right_max_width - right_visible_length

                # Only add right padding if there's more content after this block
                if r * 2 + 2 < len(pattern):  # If there are more blocks after this row
                    print(
                        f"{left_line}{' ' * left_padding}{right_line}{' ' * right_padding}"
                    )
                else:
                    print(f"{left_line}{' ' * left_padding}{right_line}")
            print()  # Add spacing between rows

        # Print last line (preserve padding)
        if lines:
            print(lines[-1])

    except Exception as e:
        print(f"❌ Error:\n{str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Display pastel output in a grid layout"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Pattern for block arrangement (e.g., '0132457689')",
        default="".join(map(str, DEFAULT_PATTERN)),
    )
    parser.add_argument("pastel_args", nargs="+", help="Arguments to pass to pastel")

    args = parser.parse_args()
    pattern = parse_pattern(args.pattern)
    run_pastel(args.pastel_args, pattern)
