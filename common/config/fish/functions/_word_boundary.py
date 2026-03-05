#!/usr/bin/env python3
"""Word boundary deletion logic for fish shell keybindings.

Called by fish functions to compute backward/forward word deletion.
Handles delimiters: / space " ' ` ( ) [ ] { } -

Usage: _word_boundary.py <direction> <before_cursor> [<after_cursor>]
  direction: "back", "forward", or "accept"
  Outputs: <cursor_pos>\n<new_commandline>
"""

import sys

DELIMITERS = set(' /\'"`()[]{}−')
# Use actual hyphen-minus (0x2D), not unicode minus
DELIMITERS = set(" /\"'`()[]{}") | {"-"}


def is_delim(ch):
    return ch in DELIMITERS


def delete_backward(before, after=""):
    """Delete backward from end of `before`. Returns (keep, full_new_line)."""
    if not before:
        return "", after

    # Phase A: last char is a non-delimiter → delete word back to nearest delimiter
    if not is_delim(before[-1]):
        i = len(before) - 1
        while i > 0 and not is_delim(before[i - 1]):
            i -= 1
        keep = before[:i]
        return keep, keep + after

    # Phase B: last char IS a delimiter
    # Step 1: delete run of same trailing delimiter char
    trail_char = before[-1]
    i = len(before) - 1
    while i > 0 and before[i - 1] == trail_char:
        i -= 1
    stripped = before[:i]

    # Step 2: if nothing left, we're done
    if not stripped:
        return "", after

    # Step 3: if stripped ends with a space, just delete the delimiter run (space is a separator)
    if trail_char == " ":
        return stripped, stripped + after

    # Step 4: if stripped ends with a non-delimiter, also delete that word
    if not is_delim(stripped[-1]):
        j = len(stripped) - 1
        while j > 0 and not is_delim(stripped[j - 1]):
            j -= 1
        keep = stripped[:j]
        return keep, keep + after

    # Step 5: stripped ends with a different delimiter → stop here
    return stripped, stripped + after


def delete_forward(before, after=""):
    """Delete forward from start of `after`. Returns (keep_after, full_new_line)."""
    if not after:
        return before, before

    # Phase A: first char is non-delimiter → delete word to next delimiter
    if not is_delim(after[0]):
        i = 0
        while i < len(after) and not is_delim(after[i]):
            i += 1
        keep_after = after[i:]
        return keep_after, before + keep_after

    # Phase B: first char is delimiter → delete run of same char only
    lead_char = after[0]
    i = 0
    while i < len(after) and after[i] == lead_char:
        i += 1
    keep_after = after[i:]
    return keep_after, before + keep_after


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: _word_boundary.py <back|forward|accept> <before> [after]", file=sys.stderr)
        sys.exit(1)

    direction = sys.argv[1]
    before = sys.argv[2] if len(sys.argv) > 2 else ""
    after = sys.argv[3] if len(sys.argv) > 3 else ""

    if direction == "back":
        keep, new_line = delete_backward(before, after)
        print(len(keep))
        print(new_line, end="")
    elif direction == "forward":
        keep_after, new_line = delete_forward(before, after)
        print(len(before))
        print(new_line, end="")
    elif direction == "accept":
        # How many chars to accept from the start of `after` (same boundary as forward delete)
        keep_after, _ = delete_forward("", after)
        print(len(after) - len(keep_after))
    else:
        print(f"Unknown direction: {direction}", file=sys.stderr)
        sys.exit(1)
