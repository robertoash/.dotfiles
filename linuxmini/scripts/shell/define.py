#!/usr/bin/env python3
# ================================================================================ #
# Define.py - A comprehensive dictionary lookup tool
# ================================================================================ #
# This script uses sdcv to look up word definitions in various dictionaries and
# formats the output for better readability. It supports multiple dictionaries
# including WordNet, Moby Thesaurus, Urban Dictionary, and Wiktionary.
# ================================================================================ #

import argparse
import re
import subprocess
import sys
import textwrap

# ================================================================================ #
# ================================ CONFIGURATION ================================== #
# ================================================================================ #

TEXT_WIDTH = 120

KNOWN_POS = {"n.", "vb.", "adj."}

# Dictionary registry - maps full names to short codes
KNOWN_LANGUAGES = {
    "WordNet": "wordnet",
    "wikt-sv-ALL-2024-10-05": "wiktsv",
    "Urban Dictionary P1 (En-En)": "urban",
    "Urban Dictionary P2 (En-En)": "urban",
    "Moby Thesaurus II": "mobythes",
}

# Order for displaying dictionaries
SORTING_ORDER = ["wordnet", "wiktsv", "urban", "mobythes"]

# ================================================================================ #
# ========================= DICTIONARY PROCESSOR REGISTRY ======================== #
# ================================================================================ #

# Dictionary processor registry - maps short codes to processor functions
DICT_PROCESSORS = {}
DICT_BUFFER_HANDLERS = {}


def register_dict_processor(dict_code):
    """Decorator to register dictionary processors"""

    def decorator(func):
        DICT_PROCESSORS[dict_code] = func
        return func

    return decorator


def register_buffer_handler(dict_code):
    """Decorator to register buffer handlers for specific dictionaries"""

    def decorator(func):
        DICT_BUFFER_HANDLERS[dict_code] = func
        return func

    return decorator


# ================================================================================ #
# ================================ SHARED UTILITIES ============================== #
# ================================================================================ #

# -------------- Part of Speech Utilities -------------- #


def shared_standardize_pos(pos):
    """Standardize various POS formats to a consistent format"""
    pos_map = {
        "n": "n.",
        "noun": "n.",
        "v": "vb.",
        "vb": "vb.",
        "verb": "vb.",
        "adj": "adj.",
        "adjective": "adj.",
        "a": "adj.",
    }
    return pos_map.get(pos.lower().rstrip("."), pos)


def shared_is_pos_line(line):
    """Check if a line is a Part of Speech marker"""
    parts = line.strip().split()
    if not parts:
        return False
    standardized = shared_standardize_pos(parts[0])
    return standardized in KNOWN_POS or re.match(r"^[a-zA-Z]+\.$", parts[0])


# -------------- Text Formatting Utilities -------------- #


def shared_indent(level, size=4):
    """Create indentation string based on level"""
    return " " * (level * size)


def shared_wrap_text(number, text, base_indent=2, indent_size=4):
    """Wrap text with consistent indentation and numbering"""
    number_str = f"{number}:  "
    prefix = shared_indent(base_indent, indent_size) + number_str
    # For consistent wrapping, use a fixed indentation level for continuations
    subsequent = shared_indent(base_indent + 1, indent_size)
    return textwrap.fill(
        text.strip(),
        width=TEXT_WIDTH,
        initial_indent=prefix,
        subsequent_indent=subsequent,
    )


# Default buffer handler for most dictionaries
@register_buffer_handler("default")
def shared_flush_buffer(buffer, buffer_level):
    """Default buffer formatting handler for all dictionaries"""
    if buffer.strip():
        prefix = shared_indent(buffer_level)
        subsequent = " " * len(prefix)
        print(
            textwrap.fill(
                buffer.strip(),
                width=TEXT_WIDTH,
                initial_indent=prefix,
                subsequent_indent=subsequent,
            )
        )
    return ""


# -------------- Language Specific Processing -------------- #


def shared_process_english_pos_line(parts, entry_counter):
    """Process an English part-of-speech line to extract any definition"""
    rest_of_line = parts[1].strip() if len(parts) > 1 else ""

    # If this line contains a definition (starts with a number),
    # return it as-is to be processed by the regular definition handling
    if rest_of_line and re.match(r"^\d+\s*[:)]", rest_of_line):
        return rest_of_line, entry_counter

    return rest_of_line, entry_counter


def shared_process_parts(
    parts, number_pattern, buffer, buffer_level, entry_counter, lang
):
    """Process parts of a definition across multiple dictionaries"""
    processed = False

    for part in parts:
        cleaned = part.strip()

        if not cleaned:
            continue

        if re.match(number_pattern, cleaned):
            if buffer.strip():
                buffer = shared_flush_buffer(buffer, buffer_level + 1)

            if lang == "english":
                cleaned = re.sub(r"^\d+\s*[:)]?\s*", "", cleaned)
            else:
                cleaned = re.sub(r"^\d+\s+", "", cleaned)

            if entry_counter != 1:
                print()

            print(shared_wrap_text(entry_counter, cleaned))
            entry_counter += 1
        else:
            buffer += " " + cleaned

    return buffer, entry_counter, processed


# ================================================================================ #
# ================================ RUNNER UTILITIES ============================== #
# ================================================================================ #


def run_sdcv(query, requested_dicts=None):
    cmd = ["sdcv"]

    # If specific dictionaries are requested, add them to the command
    if requested_dicts:
        # Map short names back to full dictionary names for sdcv
        for dict_short in requested_dicts:
            for full_name, short_name in KNOWN_LANGUAGES.items():
                if short_name == dict_short:
                    cmd.extend(["--use-dict", full_name])

    cmd.extend(query)
    result = subprocess.run(cmd, capture_output=True, text=True)
    output_lines = result.stdout.splitlines()

    if output_lines and output_lines[0].startswith("Nothing similar"):
        return output_lines, False
    return output_lines, True


# ================================================================================ #
# =========================== DICTIONARY-SPECIFIC HANDLERS ======================= #
# ================================================================================ #

# -------------------------- Swedish Wiktionary Handlers ------------------------- #


@register_dict_processor("wiktsv")
def process_entry_line_wiktsv(line_content, buffer, buffer_level, entry_counter):
    # Handle Swedish Dictionary's "a." format for adjectives
    if line_content.strip() == "a.":
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level)
        print(f"{shared_indent(1)}adj.")
        return buffer, 1, True

    # Handle raw Swedish dictionary definitions that start with a number
    # The pattern can be either with (tagg) or without tagg
    raw_def_match = re.match(r"^(\d+)\s+(.+)$", line_content.strip())
    if raw_def_match and not line_content.strip().startswith("    "):
        def_num = raw_def_match.group(1)
        content = raw_def_match.group(2)
        # Format and print this definition with proper indentation
        print(f"{shared_indent(2)}{def_num}:  {content}")
        return buffer, int(def_num) + 1, True

    parts = re.split(r"(?=\d+\s+(?:\(|[a-zåäöA-ZÅÄÖ]))", line_content)

    if len(parts) == 1 and not re.match(r"^\d+\s", line_content):
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level + 1)

        print(shared_wrap_text(entry_counter, line_content))
        entry_counter += 1
        return buffer, entry_counter, True

    # Use process_parts to handle properly formatted definitions
    return shared_process_parts(
        parts, r"^\d+\s", buffer, buffer_level, entry_counter, "swedish"
    )


# ---------------------------- WordNet Dictionary Handlers ---------------------------- #


@register_buffer_handler("wordnet")
def format_wordnet_buffer(buffer, buffer_level):
    """Format WordNet buffer content with consistent indentation"""
    if not buffer.strip():
        return ""

    # Check if this is a definition we're building
    if buffer.startswith("DEFBUILDING:"):
        parts = buffer.split(":", 2)
        if len(parts) >= 3:
            def_num = parts[1]
            content = parts[2].strip()

            # Create a consistent format for definition numbers
            num_str = f"{def_num}:  "  # Always 2 spaces after colon

            # Calculate proper indentation
            initial_indent = shared_indent(2) + num_str
            subsequent_indent = " " * len(initial_indent)

            # Clean up all whitespace issues including mid-definition newlines
            # Ensure all newlines and extra spaces are replaced with single spaces
            content = re.sub(r"\s+", " ", content).strip()

            # Format with textwrap for consistent wrapping
            wrapped_content = textwrap.fill(
                content,
                width=TEXT_WIDTH,
                initial_indent=initial_indent,
                subsequent_indent=subsequent_indent,
                break_on_hyphens=False,  # Don't break on hyphens
                break_long_words=False,  # Don't break long words
                tabsize=4,  # Consistent tab size
                expand_tabs=True,  # Expand tabs to spaces
                replace_whitespace=True,  # Replace all whitespace with spaces
            )

            print(wrapped_content)
            return ""

    # For other content (not definition starts)
    initial_indent = shared_indent(3)
    subsequent_indent = initial_indent
    content = buffer.strip()

    # Clean up all whitespace issues including mid-definition newlines
    content = re.sub(r"\s+", " ", content)

    # Format with textwrap for consistent wrapping
    wrapped_content = textwrap.fill(
        content,
        width=TEXT_WIDTH,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_on_hyphens=False,
        break_long_words=False,
        tabsize=4,
        expand_tabs=True,
        replace_whitespace=True,
    )

    print(wrapped_content)
    return ""


@register_dict_processor("wordnet")
def process_entry_line_wordnet(line_content, buffer, buffer_level, entry_counter):
    line = line_content.strip()

    # Check for POS markers first - they can be with or without a period
    pos_match = re.match(r"^(adj|n|v)(\.)?$", line)
    if pos_match:
        # Always flush buffer when hitting a POS marker
        if buffer:
            buffer = shared_flush_buffer(buffer, buffer_level)
        # Print the POS marker with a period
        print(f"{shared_indent(1)}{pos_match.group(1)}.")
        # Reset entry counter for new section
        entry_counter = 1
        return buffer, entry_counter, True

    # Check for a definition - just needs to start with a number after any whitespace
    def_match = re.match(r"^\s*(\d+)[:.]?\s*(.+)$", line_content)
    if def_match:
        # Always flush buffer when hitting a new definition
        if buffer:
            # Let the wordnet buffer handler take care of the previous definition
            if buffer.startswith("DEFBUILDING:"):
                buffer = format_wordnet_buffer(buffer, buffer_level)
            # Special case for definition #1 content buffer
            elif buffer.startswith("DEF1_CONTENT:"):
                content = buffer[13:].strip()
                num_str = "1:  "
                prefix = shared_indent(2) + num_str
                subsequent = " " * len(prefix)

                # Clean up content and ensure no mid-definition newlines
                content = re.sub(r"\s+", " ", content).strip()

                # Format with textwrap for consistent wrapping
                print(
                    textwrap.fill(
                        content,
                        width=TEXT_WIDTH,
                        initial_indent=prefix,
                        subsequent_indent=subsequent,
                        break_on_hyphens=False,
                        break_long_words=False,
                    )
                )
                buffer = ""
            else:
                buffer = shared_flush_buffer(buffer, buffer_level)

        # Extract definition number and content
        def_num = def_match.group(1)
        content = def_match.group(2).strip()

        # Unified handling for all definitions, with slight special case for #1
        if def_num == "1":
            # Store in special buffer to collect potential multi-line content for def #1
            buffer = f"DEF1_CONTENT:{content}"
        else:
            # All other definitions use the standard approach with DEFBUILDING marker
            buffer = f"DEFBUILDING:{def_num}:{content}"

        entry_counter = int(def_num) + 1
        return buffer, entry_counter, True

    # Special handling for definition #1 content collection
    if buffer and buffer.startswith("DEF1_CONTENT:"):
        prev_content = buffer[13:]  # Extract previous content

        # Check if this is a new definition (starts with a digit)
        if re.match(r"^\s*\d+", line):
            # Format the complete definition #1 before processing the new definition
            num_str = "1:  "
            prefix = shared_indent(2) + num_str
            subsequent = " " * len(prefix)

            # Clean up content
            content = re.sub(r"\s+", " ", prev_content).strip()

            # Format with textwrap
            print(
                textwrap.fill(
                    content,
                    width=TEXT_WIDTH,
                    initial_indent=prefix,
                    subsequent_indent=subsequent,
                    break_on_hyphens=False,
                    break_long_words=False,
                )
            )

            # Clear buffer and don't mark as processed
            buffer = ""
            return buffer, entry_counter, False

        # This is a continuation of definition #1, just append to the buffer
        buffer = f"DEF1_CONTENT:{prev_content} {line}"
        return buffer, entry_counter, True

    # Handle continuation lines for non-#1 definitions
    if re.match(r"^\s+", line_content) and buffer and buffer.startswith("DEFBUILDING:"):
        # This is a continuation line with indentation
        buffer += " " + line.strip()
        return buffer, entry_counter, True

    # Check for any continuation while we're building a definition
    if buffer and buffer.startswith("DEFBUILDING:"):
        # Add this line to the current definition being built
        buffer += " " + line.strip()
        return buffer, entry_counter, True

    # Not part of an existing definition and not a new definition
    if line:
        if buffer:
            buffer += " " + line.strip()
        else:
            buffer = line.strip()

    return buffer, entry_counter, True


# ---------------------------- Moby Thesaurus Handlers ---------------------------- #


@register_buffer_handler("mobythes")
def format_mobythes_buffer(buffer, buffer_level):
    """Format a buffer of comma-separated synonyms with proper wrapping"""
    if not buffer.strip():
        return ""

    # Format the synonym list with nice wrapping
    synonyms = buffer.strip().split(", ")
    print()
    formatted_synonyms = ""
    line_length = 0

    for synonym in synonyms:
        synonym = synonym.strip()
        # If adding this synonym would make the line too long, print and reset
        if line_length + len(synonym) + 2 > TEXT_WIDTH - len(
            shared_indent(buffer_level)
        ):
            if formatted_synonyms:
                print(f"{shared_indent(buffer_level)}{formatted_synonyms.rstrip(', ')}")
            formatted_synonyms = f"{synonym}, "
            line_length = len(synonym) + 2
        else:
            formatted_synonyms += f"{synonym}, "
            line_length += len(synonym) + 2

    # Print any remaining synonyms
    if formatted_synonyms:
        print(f"{shared_indent(buffer_level)}{formatted_synonyms.rstrip(', ')}")

    return ""


@register_dict_processor("mobythes")
def process_entry_line_mobythes(line_content, buffer, buffer_level, entry_counter):
    # Check for the header line containing the synonym count
    if re.match(r"^\d+\s+Moby\s+Thesaurus\s+words\s+for", line_content):
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level)

        # Extract and print the header
        print(f"{shared_indent(buffer_level)}{line_content}")
        return buffer, entry_counter, True

    # Process list of synonyms
    if ":" in line_content and entry_counter == 1:
        # This is the first line after the header that contains the colon
        parts = line_content.split(":", 1)
        if len(parts) > 1:
            # Start collecting synonyms
            synonyms = parts[1].strip()
            buffer += synonyms
        return buffer, entry_counter, True

    # Process continuation lines of synonyms
    buffer += " " + line_content

    # Return with processed=False to let the main function handle buffer
    # when end of entry is detected
    return buffer, entry_counter, False


# ---------------------------- Urban Dictionary Handlers ---------------------------- #


@register_dict_processor("urban")
def process_entry_line_urban(line_content, buffer, buffer_level, entry_counter):
    # Process numbered definitions with votes
    # Format: "1. (4324 up, 488 down)"
    if re.match(r"^\d+\.\s+\(\d+\s+up,\s+\d+\s+down\)", line_content):
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level + 1)

        # Extract definition number and votes
        match = re.match(r"^(\d+)\..*\((\d+)\s+up,\s+(\d+)\s+down\)", line_content)
        if match:
            definition_num = match.group(1)
            votes_up = match.group(2)
            votes_down = match.group(3)
            print(
                f"\n{shared_indent(buffer_level)}{definition_num}:  [↑{votes_up} ↓{votes_down}]"
            )

        # Reset entry counter for each new definition
        entry_counter = 1
        return buffer, entry_counter, True

    # Process numbered items (could be sub-definitions or examples)
    if re.match(r"^\d+\.\s+", line_content) and not re.match(
        r"^\d+\.\s+\(", line_content
    ):
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level + 1)

        # Extract text, removing the original numbering
        match = re.match(r"^\d+\.\s+(.*)", line_content)
        if match:
            text = match.group(1).strip()

            # Replace internal numbering with bullet points
            # For example: "1. example" becomes "- example"
            text = re.sub(r"^\d+\.\s+", "- ", text)

            # Print with bullet point instead of number
            prefix = shared_indent(buffer_level + 1)
            subsequent = " " * len(prefix)
            print(
                textwrap.fill(
                    f"- {text}",
                    width=TEXT_WIDTH,
                    initial_indent=prefix,
                    subsequent_indent=subsequent,
                )
            )
            return buffer, entry_counter, True

    # Process non-numbered lines - treat as part of the definition
    if (
        line_content
        and not re.match(r"^\d+\.", line_content)
        and not line_content.startswith(("See", "More"))
    ):
        # Use the textwrap.fill function for consistent formatting
        prefix = shared_indent(buffer_level + 1)
        subsequent = " " * len(prefix)
        print(
            textwrap.fill(
                f"- {line_content}",
                width=TEXT_WIDTH,
                initial_indent=prefix,
                subsequent_indent=subsequent,
            )
        )
        return buffer, entry_counter, True

    # Process "See" references
    if line_content.startswith("See "):
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level + 1)
        # Increase indentation by one level for "See also:" lines
        prefix = shared_indent(buffer_level + 1)
        subsequent = " " * len(prefix)
        print(
            textwrap.fill(
                f"See also: {line_content[4:]}",
                width=TEXT_WIDTH,
                initial_indent=prefix,
                subsequent_indent=subsequent,
            )
        )
        return buffer, entry_counter, True

    # Process "More online" links
    if line_content.startswith("More online:"):
        if buffer.strip():
            buffer = shared_flush_buffer(buffer, buffer_level + 1)
        print(f"\n{shared_indent(buffer_level)}{line_content}")
        return buffer, entry_counter, True

    # Accumulate definition text in buffer (this should rarely be reached for Urban Dictionary)
    buffer += " " + line_content
    return buffer, entry_counter, False


# ================================================================================ #
# =========================== PARSING AND TOKENIZATION =========================== #
# ================================================================================ #


def tag_line(line, prev_tag):
    line = line.rstrip()

    # First rule has no dependency on prev_tag
    if line.startswith("-->"):
        lang_name = line[3:].strip()
        if lang_name in KNOWN_LANGUAGES:
            return "#language"

    # The non-header line at the start of output is search feedback
    if not prev_tag and not line.startswith("-->"):
        return "#search_feedback"

    # Search term related depends on prev_tag - can't remove this
    if re.fullmatch(r"[a-zA-Z\-]+", line) or (
        line.startswith("-->") and not line[3:].strip() in KNOWN_LANGUAGES
    ):
        if prev_tag in ("#language", "#search_term_related", "#entry_line"):
            return "#search_term_related"

    # Part-of-speech line detection has no dependency on prev_tag
    if shared_is_pos_line(line):
        return "#pos"

    # Default case
    return "#entry_line"


def parse_sdcv(lines):
    parsed = []
    prev_tag = None
    current_dict = None

    for line in lines:
        tag = tag_line(line, prev_tag)

        # Track current dictionary
        if tag == "#language":
            dict_name = line[3:].strip()
            current_dict = KNOWN_LANGUAGES.get(dict_name)

        # Special handling for Urban Dictionary - don't treat its lines as POS
        if tag == "#pos" and current_dict == "urban":
            tag = "#entry_line"

        parsed.append((tag, line.rstrip()))
        prev_tag = tag

    return parsed


# ================================================================================ #
# ============================= OUTPUT PROCESSING ================================ #
# ================================================================================ #


def process_parsed(parsed):
    current_dict = None
    printed_words = {}
    buffer = ""
    buffer_level = 2
    entry_counter = 1

    for idx, (tag, line) in enumerate(parsed):
        next_tag = parsed[idx + 1][0] if idx + 1 < len(parsed) else None

        if tag == "#search_feedback":
            print(line)
            continue

        if tag == "#language":
            current_dict = KNOWN_LANGUAGES[line[3:].strip()]
            print(f"\n{current_dict.upper()}:")
            printed_words[current_dict] = False
            buffer = shared_flush_buffer(buffer, buffer_level)
            continue

        if tag == "#search_term_related":
            if not printed_words.get(current_dict, False):
                word = line.replace("-->", "").strip()
                print(f"\n{word}")
                printed_words[current_dict] = True
            continue

        if tag == "#pos":
            buffer = shared_flush_buffer(buffer, buffer_level)
            parts = line.strip().split(maxsplit=1)
            pos = shared_standardize_pos(parts[0])

            print(f"{shared_indent(1)}{pos}")

            entry_counter = 1

            if len(parts) > 1 and parts[1].strip():
                rest_of_line = parts[1].strip()

                if current_dict in ["wordnet"]:
                    rest_of_line, entry_counter = shared_process_english_pos_line(
                        parts, entry_counter
                    )

                if rest_of_line:
                    # Check if this is a definition (starts with a number)
                    if (
                        re.match(r"^\d+\s*[:)]", rest_of_line)
                        and current_dict == "wordnet"
                    ):
                        # Use the wordnet processor to handle this definition
                        # This ensures consistent handling with other definitions
                        buffer, entry_counter, _ = process_entry_line_wordnet(
                            rest_of_line, buffer, buffer_level, entry_counter
                        )
                    else:
                        # If it's not a definition, just print it directly
                        print(shared_wrap_text(entry_counter, rest_of_line))
                        entry_counter += 1
            continue

        if tag == "#entry_line":
            line_content = line.strip()

            if not line_content:
                pass
            else:
                # Use the registered processor for the current dictionary if available
                processor = DICT_PROCESSORS.get(current_dict)
                processed = False

                if processor:
                    buffer, entry_counter, processed = processor(
                        line_content, buffer, buffer_level, entry_counter
                    )

                if not processed:
                    # Default processing for dictionaries without a specific processor
                    buffer += " " + line_content

            if (
                next_tag
                in ("#pos", "#search_term_related", "#language", "#search_feedback")
                or next_tag is None
            ):
                if buffer.strip():
                    # Handle buffer based on type
                    if buffer.startswith("DEF1_CONTENT:"):
                        # Process definition #1 content
                        content = buffer[13:].strip()
                        num_str = "1:  "
                        prefix = shared_indent(2) + num_str
                        subsequent = " " * len(prefix)

                        # Clean up content
                        content = re.sub(r"\s+", " ", content).strip()

                        # Format with textwrap
                        print(
                            textwrap.fill(
                                content,
                                width=TEXT_WIDTH,
                                initial_indent=prefix,
                                subsequent_indent=subsequent,
                                break_on_hyphens=False,
                                break_long_words=False,
                            )
                        )
                        buffer = ""
                    else:
                        # Use appropriate handler for other buffer types
                        buffer_handler = DICT_BUFFER_HANDLERS.get(
                            current_dict, DICT_BUFFER_HANDLERS.get("default")
                        )
                        buffer = buffer_handler(buffer, buffer_level)

    # Handle any remaining buffer at the end
    if buffer.strip():
        if buffer.startswith("DEF1_CONTENT:"):
            # Process definition #1 content
            content = buffer[13:].strip()
            num_str = "1:  "
            prefix = shared_indent(2) + num_str
            subsequent = " " * len(prefix)

            # Clean up content
            content = re.sub(r"\s+", " ", content).strip()

            # Format with textwrap
            print(
                textwrap.fill(
                    content,
                    width=TEXT_WIDTH,
                    initial_indent=prefix,
                    subsequent_indent=subsequent,
                    break_on_hyphens=False,
                    break_long_words=False,
                )
            )
        else:
            # Use appropriate handler for other buffer types
            buffer_handler = DICT_BUFFER_HANDLERS.get(
                current_dict, DICT_BUFFER_HANDLERS.get("default")
            )
            buffer = buffer_handler(buffer, buffer_level)


def process_search_results(search_term, search_results):
    if not search_results:
        print(f"No definitions found for '{search_term}'")
        return

    # Group parsed results by dictionary source
    dictionaries = {}
    for source, parsed in search_results.items():
        if source == "sdcv":
            # Extract dictionaries from the parsed results
            current_dict = None
            for tag, line in parsed:
                if tag == "#language":
                    current_dict = KNOWN_LANGUAGES[line[3:].strip()]
                    dictionaries[current_dict] = []
                if current_dict and tag != "#search_feedback":
                    dictionaries.setdefault(current_dict, []).append((tag, line))

    # Sort dictionaries according to SORTING_ORDER
    sorted_dicts = []
    for dict_id in SORTING_ORDER:
        if dict_id in dictionaries:
            sorted_dicts.append(dictionaries[dict_id])

    # Add any remaining dictionaries that weren't in SORTING_ORDER
    for dict_id, entries in dictionaries.items():
        if dict_id not in SORTING_ORDER:
            sorted_dicts.append(entries)

    # Process each dictionary's parsed content in the sorted order
    for dict_entries in sorted_dicts:
        if dict_entries:
            process_parsed(dict_entries)


# ================================================================================ #
# ================================== MAIN FUNCTION =============================== #
# ================================================================================ #


def main():
    parser = argparse.ArgumentParser(
        description="Look up word definitions in various dictionaries"
    )
    parser.add_argument("word", nargs="?", help="The word to look up")
    parser.add_argument(
        "--dict",
        dest="dictionaries",
        help="Comma-separated list of dictionaries to use (e.g., urban,oald)",
    )
    args = parser.parse_args()

    if args.word:
        search_term = args.word
    else:
        if args.dictionaries:
            print("Error: Word argument is required when using --dict")
            sys.exit(1)
        print("Usage: define.py [--dict=DICT1,DICT2,...] <word>")
        parser.print_help()
        sys.exit(1)

    # If dictionaries are specified, prepare them for filtering
    requested_dicts = None
    if args.dictionaries:
        requested_dicts = [d.strip() for d in args.dictionaries.split(",")]

    # Run sdcv with specified dictionaries if any
    sdcv_lines, sdcv_found = run_sdcv([search_term], requested_dicts)
    search_results = {}

    if sdcv_found:
        # Parse the SDCV results
        parsed_results = parse_sdcv(sdcv_lines)
        search_results["sdcv"] = parsed_results

    process_search_results(search_term, search_results)


if __name__ == "__main__":
    main()
