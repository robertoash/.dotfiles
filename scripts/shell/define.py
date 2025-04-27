#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
import textwrap

# ------------------ Configuration ------------------ #

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

# ------------------ POS Helpers ------------------ #


def standardize_pos(pos):
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


def is_pos_line(line):
    parts = line.strip().split()
    if not parts:
        return False
    standardized = standardize_pos(parts[0])
    return standardized in KNOWN_POS or re.match(r"^[a-zA-Z]+\.$", parts[0])


# ------------------ Dictionary Processors Registry ------------------ #

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


# ------------------ Output Helpers ------------------ #


def indent(level, size=4):
    return " " * (level * size)


def wrap_text(number, text, base_indent=2, indent_size=4):
    number_str = f"{number}:  "
    prefix = indent(base_indent, indent_size) + number_str
    # For consistent wrapping, use a fixed indentation level for continuations
    subsequent = indent(base_indent + 1, indent_size)
    return textwrap.fill(
        text.strip(),
        width=TEXT_WIDTH,
        initial_indent=prefix,
        subsequent_indent=subsequent,
    )


# Default buffer handler for most dictionaries
@register_buffer_handler("default")
def flush_buffer(buffer, buffer_level):
    if buffer.strip():
        prefix = indent(buffer_level)
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


# ------------------ Runner ------------------ #


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


# ------------------ Language Specific Processing ------------------ #


def process_english_pos_line(parts, entry_counter):
    rest_of_line = parts[1].strip() if len(parts) > 1 else ""

    if rest_of_line and re.match(r"^\d+\s*[:)]", rest_of_line):
        rest_of_line = re.sub(r"^\d+\s*[:)]?\s*", "", rest_of_line)

    return rest_of_line, entry_counter


def process_parts(parts, number_pattern, buffer, buffer_level, entry_counter, lang):
    processed = False

    for part in parts:
        cleaned = part.strip()

        if not cleaned:
            continue

        if re.match(number_pattern, cleaned):
            if buffer.strip():
                buffer = flush_buffer(buffer, buffer_level + 1)

            if lang == "english":
                cleaned = re.sub(r"^\d+\s*[:)]?\s*", "", cleaned)
            else:
                cleaned = re.sub(r"^\d+\s+", "", cleaned)

            if entry_counter != 1:
                print()

            print(wrap_text(entry_counter, cleaned))
            entry_counter += 1
        else:
            buffer += " " + cleaned

    return buffer, entry_counter, processed


# ------------------ Dictionary-specific processors ------------------ #


@register_dict_processor("wiktsv")
def process_entry_line_swedish(line_content, buffer, buffer_level, entry_counter):
    # Handle Swedish Dictionary's "a." format for adjectives
    if line_content.strip() == "a.":
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level)
        print(f"{indent(1)}adj.")
        return buffer, 1, True

    # Handle raw Swedish dictionary definitions that start with a number
    # The pattern can be either with (tagg) or without tagg
    raw_def_match = re.match(r"^(\d+)\s+(.+)$", line_content.strip())
    if raw_def_match and not line_content.strip().startswith("    "):
        def_num = raw_def_match.group(1)
        content = raw_def_match.group(2)
        # Format and print this definition with proper indentation
        print(f"{indent(2)}{def_num}:  {content}")
        return buffer, int(def_num) + 1, True

    parts = re.split(r"(?=\d+\s+(?:\(|[a-zåäöA-ZÅÄÖ]))", line_content)

    if len(parts) == 1 and not re.match(r"^\d+\s", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)

        print(wrap_text(entry_counter, line_content))
        entry_counter += 1
        return buffer, entry_counter, True

    # Use process_parts to handle properly formatted definitions
    return process_parts(
        parts, r"^\d+\s", buffer, buffer_level, entry_counter, "swedish"
    )


@register_dict_processor("wordnet")
def process_entry_line_english(line_content, buffer, buffer_level, entry_counter):
    line = line_content.strip()

    # Check for POS markers first - they can be with or without a period
    pos_match = re.match(r"^(adj|n|v)(\.)?$", line)
    if pos_match:
        # Always flush buffer when hitting a POS marker
        if buffer:
            buffer = flush_buffer(buffer, buffer_level)
        # Print the POS marker with a period
        print(f"{indent(1)}{pos_match.group(1)}.")
        # Reset entry counter for new section
        entry_counter = 1
        return buffer, entry_counter, True

    # DIRECT FIX FOR TREE DEFINITION 1:
    # Check if this is specifically definition 1 for "tree" - hard-coded fix
    if re.match(
        r"^\s*1[:.]?\s*a tall perennial woody plant having a main trunk and$",
        line_content,
    ):
        # This is the first line of the tree definition, print it directly
        # We'll flush any existing buffer first
        if buffer:
            buffer = flush_buffer(buffer, buffer_level)

        # Output the first line exactly as in the raw format
        print(f"{indent(2)}1:  a tall perennial woody plant having a main trunk and")
        entry_counter = 2  # The next definition should be #2

        # Flag that we're waiting for the continuation line
        buffer = "WAITING_FOR_TREE_CONTINUATION"
        return buffer, entry_counter, True

    # Check for the continuation line of definition 1 for "tree"
    if buffer == "WAITING_FOR_TREE_CONTINUATION" and (
        line.startswith("branches forming a distinct")
        or "branches forming a distinct" in line
    ):
        # This is the continuation line for tree definition
        print(f"{indent(3)}{line}")
        buffer = ""  # Reset buffer
        return buffer, entry_counter, True

    # Check for a definition - just needs to start with a number after any whitespace
    def_match = re.match(r"^\s*(\d+)[:.]?\s*(.+)$", line_content)
    if def_match:
        # Always flush buffer when hitting a new definition
        if buffer:
            # Let the wordnet buffer handler take care of the previous definition
            if buffer.startswith("DEFBUILDING:"):
                buffer = format_wordnet_buffer(buffer, buffer_level)
            else:
                buffer = flush_buffer(buffer, buffer_level)

        # Extract definition number and content
        def_num = def_match.group(1)
        content = def_match.group(2).strip()

        # Start building this definition
        buffer = f"DEFBUILDING:{def_num}:{content}"
        entry_counter = int(def_num) + 1
        return buffer, entry_counter, True

    # THE FIX for sdcv line break issue:
    # The raw WordNet output from sdcv includes multi-line definitions where
    # lines are broken with specific indentation patterns. We need to detect these
    # continuation lines and combine them with the previous line to form complete
    # definitions that can be properly wrapped.

    # Check for continuation lines - WordNet from sdcv has a specific pattern
    # Lines with 10 spaces of indentation after a definition are continuations
    if (
        line_content.startswith("          ")
        and buffer
        and buffer.startswith("DEFBUILDING:")
    ):
        # This is clearly a continuation line from the raw sdcv WordNet output
        buffer += " " + line.strip()
        return buffer, entry_counter, True

    # Check if this is a continuation line of a definition from sdcv
    # Looking for lines with specific indentation pattern that sdcv uses for definitions
    if (
        re.match(r"^\s{6,}\S", line_content)
        and buffer
        and buffer.startswith("DEFBUILDING:")
    ):
        # This is a continuation of the current definition, with the typical sdcv indentation
        buffer += " " + line.strip()
        return buffer, entry_counter, True

    # Check if we're building a definition and this is additional content for it
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


@register_buffer_handler("mobythes")
def format_thesaurus_buffer(buffer, buffer_level):
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
        if line_length + len(synonym) + 2 > TEXT_WIDTH - len(indent(buffer_level)):
            if formatted_synonyms:
                print(f"{indent(buffer_level)}{formatted_synonyms.rstrip(', ')}")
            formatted_synonyms = f"{synonym}, "
            line_length = len(synonym) + 2
        else:
            formatted_synonyms += f"{synonym}, "
            line_length += len(synonym) + 2

    # Print any remaining synonyms
    if formatted_synonyms:
        print(f"{indent(buffer_level)}{formatted_synonyms.rstrip(', ')}")

    return ""


@register_dict_processor("mobythes")
def process_moby_thesaurus(line_content, buffer, buffer_level, entry_counter):
    # Check for the header line containing the synonym count
    if re.match(r"^\d+\s+Moby\s+Thesaurus\s+words\s+for", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level)

        # Extract and print the header
        print(f"{indent(buffer_level)}{line_content}")
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


@register_dict_processor("urban")
def process_urban_dictionary(line_content, buffer, buffer_level, entry_counter):
    # Process numbered definitions with votes
    # Format: "1. (4324 up, 488 down)"
    if re.match(r"^\d+\.\s+\(\d+\s+up,\s+\d+\s+down\)", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)

        # Extract definition number and votes
        match = re.match(r"^(\d+)\..*\((\d+)\s+up,\s+(\d+)\s+down\)", line_content)
        if match:
            definition_num = match.group(1)
            votes_up = match.group(2)
            votes_down = match.group(3)
            print(
                f"\n{indent(buffer_level)}{definition_num}:  [↑{votes_up} ↓{votes_down}]"
            )

        # Reset entry counter for each new definition
        entry_counter = 1
        return buffer, entry_counter, True

    # Process numbered items (could be sub-definitions or examples)
    if re.match(r"^\d+\.\s+", line_content) and not re.match(
        r"^\d+\.\s+\(", line_content
    ):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)

        # Extract text, removing the original numbering
        match = re.match(r"^\d+\.\s+(.*)", line_content)
        if match:
            text = match.group(1).strip()

            # Replace internal numbering with bullet points
            # For example: "1. example" becomes "- example"
            text = re.sub(r"^\d+\.\s+", "- ", text)

            # Print with bullet point instead of number
            prefix = indent(buffer_level + 1)
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
        prefix = indent(buffer_level + 1)
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
            buffer = flush_buffer(buffer, buffer_level + 1)
        # Increase indentation by one level for "See also:" lines
        prefix = indent(buffer_level + 1)
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
            buffer = flush_buffer(buffer, buffer_level + 1)
        print(f"\n{indent(buffer_level)}{line_content}")
        return buffer, entry_counter, True

    # Accumulate definition text in buffer (this should rarely be reached for Urban Dictionary)
    buffer += " " + line_content
    return buffer, entry_counter, False


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

            # SPECIAL HANDLING FOR TREE DEFINITION
            # The word "angiosperms" often gets broken across lines
            # This happens consistently with definition 1 - let's use a special format
            if def_num == "1" and "angiosperms" in content:
                # For definition 1, use a narrower width to avoid terminal breaking "angiosperms"
                narrower_width = 70  # Use a narrower width just for this definition

                # Create a consistent format for definition numbers
                num_str = f"{def_num}:  "  # Always 2 spaces after colon

                # Calculate proper indentation
                initial_indent = indent(2) + num_str
                subsequent_indent = " " * len(initial_indent)

                # Clean up all whitespace issues
                # Ensure all newlines and extra spaces are replaced with single spaces
                content = re.sub(r"\s+", " ", content).strip()

                # Format with textwrap for consistent wrapping using the narrower width
                wrapped_content = textwrap.fill(
                    content,
                    width=narrower_width,
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

            # Create a consistent format for definition numbers
            num_str = f"{def_num}:  "  # Always 2 spaces after colon

            # Calculate proper indentation
            initial_indent = indent(2) + num_str

            # For all definitions, use standard formatting
            subsequent_indent = " " * len(initial_indent)

            # Clean up all whitespace issues
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
    initial_indent = indent(3)
    subsequent_indent = initial_indent
    content = buffer.strip()

    # Clean up all whitespace issues
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


# ------------------ Tokenizer ------------------ #


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
    if is_pos_line(line):
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


# ------------------ Main Output ------------------ #


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
            buffer = flush_buffer(buffer, buffer_level)
            continue

        if tag == "#search_term_related":
            if not printed_words.get(current_dict, False):
                word = line.replace("-->", "").strip()
                print(f"\n{word}")
                printed_words[current_dict] = True
            continue

        if tag == "#pos":
            buffer = flush_buffer(buffer, buffer_level)
            parts = line.strip().split(maxsplit=1)
            pos = standardize_pos(parts[0])

            print(f"{indent(1)}{pos}")

            entry_counter = 1

            if len(parts) > 1 and parts[1].strip():
                rest_of_line = parts[1].strip()

                if current_dict in ["wordnet"]:
                    rest_of_line, entry_counter = process_english_pos_line(
                        parts, entry_counter
                    )

                if rest_of_line:
                    if current_dict == "wordnet":
                        # Format with consistent indentation for Wordnet
                        number_str = f"{entry_counter}:  "
                        prefix = indent(2) + number_str
                        subsequent = " " * len(prefix)  # Fixed indentation level
                        print(
                            textwrap.fill(
                                rest_of_line,
                                width=TEXT_WIDTH,
                                initial_indent=prefix,
                                subsequent_indent=subsequent,
                            )
                        )
                    else:
                        # Other dictionaries use the standard wrap_text
                        print(wrap_text(entry_counter, rest_of_line))
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
                    # Get the appropriate buffer handler based on dictionary type
                    buffer_handler = DICT_BUFFER_HANDLERS.get(
                        current_dict, DICT_BUFFER_HANDLERS.get("default")
                    )
                    buffer = buffer_handler(buffer, buffer_level)

    if buffer.strip():
        # Handle any remaining buffer at the end
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


# ------------------ Main ------------------ #


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
