#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
import textwrap

# ------------------ Configuration ------------------ #

TEXT_WIDTH = 120

KNOWN_POS = {"n.", "vb.", "adj."}
KNOWN_LANGUAGES = {
    "WordNet": "wordnet",
    "wikt-sv-ALL-2024-10-05": "wiktsv",
    "Oxford Advanced Learner's Dictionary 8th Ed.": "oald",
    "Urban Dictionary P1 (En-En)": "urban",
    "Urban Dictionary P2 (En-En)": "urban",
}

SORTING_ORDER = ["wordnet", "wiktsv", "oald", "urban"]

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


# ------------------ Tokenizer ------------------ #


def tag_line(line, prev_tag):
    line = line.rstrip()

    if not prev_tag and not line.startswith("-->"):
        return "#search_feedback"
    if line.startswith("-->"):
        lang_name = line[3:].strip()
        if lang_name in KNOWN_LANGUAGES:
            return "#language"
    if re.fullmatch(r"[a-zA-Z\-]+", line) or (
        line.startswith("-->") and not line[3:].strip() in KNOWN_LANGUAGES
    ):
        if prev_tag in ("#language", "#search_term_related", "#entry_line"):
            return "#search_term_related"
    if is_pos_line(line):
        return "#pos"
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


# ------------------ Output Helpers ------------------ #


def indent(level, size=4):
    return " " * (level * size)


def wrap_text(number, text, base_indent=2, indent_size=4):
    number_str = f"{number}:  "
    prefix = indent(base_indent, indent_size) + number_str
    subsequent = " " * (len(prefix))
    return textwrap.fill(
        text.strip(),
        width=TEXT_WIDTH,
        initial_indent=prefix,
        subsequent_indent=subsequent,
    )


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


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_escape.sub("", text)


# ------------------ Language Specific Processing ------------------ #


def process_english_pos_line(parts, entry_counter):
    rest_of_line = parts[1].strip() if len(parts) > 1 else ""

    if rest_of_line and re.match(r"^\d+\s*[:)]", rest_of_line):
        rest_of_line = re.sub(r"^\d+\s*[:)]?\s*", "", rest_of_line)

    return rest_of_line, entry_counter


def process_entry_line_swedish(line_content, buffer, buffer_level, entry_counter):
    parts = re.split(r"(?=\d+\s+(?:\(|[a-zåäöA-ZÅÄÖ]))", line_content)

    if len(parts) == 1 and not re.match(r"^\d+\s", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)

        print(wrap_text(entry_counter, line_content))
        entry_counter += 1
        return buffer, entry_counter, True

    return process_parts(
        parts, r"^\d+\s", buffer, buffer_level, entry_counter, "swedish"
    )


def process_entry_line_english(line_content, buffer, buffer_level, entry_counter):
    parts = re.split(r"(?=\d+\s*[:)])", line_content)
    return process_parts(
        parts, r"^\d+\s*[:)]", buffer, buffer_level, entry_counter, "english"
    )


def process_oxford_dictionary(line_content, buffer, buffer_level, entry_counter):
    # Process section headers (all caps)
    if re.match(r"^[A-Z][\sA-Z/]+$", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)
        print(f"{indent(buffer_level)}{line_content}")
        return buffer, entry_counter, True

    # Process numbered definitions
    if re.match(r"^\d+\.", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)

        # Extract the definition number and content
        match = re.match(r"^(\d+\.)\s*(.*)", line_content)
        if match:
            content = match.group(2).strip()
            print(wrap_text(entry_counter, content))
            entry_counter += 1
        return buffer, entry_counter, True

    # Process example sentences with bullet points
    if line_content.startswith("•"):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)
        example = line_content.replace("•", "", 1).strip()
        print(f"{indent(buffer_level + 1)}• {example}")
        return buffer, entry_counter, True

    # Process parenthetical information like "(informal)"
    if line_content.startswith("(") and not re.match(r"^\(\d+", line_content):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)
        print(f"{indent(buffer_level)}{line_content}")
        return buffer, entry_counter, True

    # Process word origin, thesaurus, example banks, etc.
    if (
        line_content.startswith("Word Origin:")
        or line_content.startswith("Thesaurus:")
        or line_content.startswith("Example Bank:")
        or line_content.startswith("Synonyms:")
        or line_content.startswith("Verb forms:")
    ):
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)
        print(f"\n{indent(buffer_level)}{line_content}")
        return buffer, entry_counter, True

    # Process POS headers
    if line_content == "verb" or line_content == "noun" or line_content == "adjective":
        if buffer.strip():
            buffer = flush_buffer(buffer, buffer_level + 1)
        print(f"\n{indent(1)}{line_content}.")
        entry_counter = 1
        return buffer, entry_counter, True

    # Accumulate other content in buffer
    buffer += " " + line_content
    return buffer, entry_counter, False


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

            # Skip printing POS for Urban Dictionary
            if current_dict != "urban-en":
                print(f"{indent(1)}{pos}")

            entry_counter = 1

            if len(parts) > 1 and parts[1].strip():
                rest_of_line = parts[1].strip()

                if current_dict in ["wordnet", "oald", "urban"]:
                    rest_of_line, entry_counter = process_english_pos_line(
                        parts, entry_counter
                    )

                if rest_of_line and current_dict != "urban":
                    print(wrap_text(entry_counter, rest_of_line))
                    entry_counter += 1
            continue

        if tag == "#entry_line":
            line_content = line.strip()

            if not line_content:
                pass
            else:
                processed = False

                if current_dict == "wikt-sv":
                    buffer, entry_counter, processed = process_entry_line_swedish(
                        line_content, buffer, buffer_level, entry_counter
                    )
                elif current_dict == "oald":
                    buffer, entry_counter, processed = process_oxford_dictionary(
                        line_content, buffer, buffer_level, entry_counter
                    )
                elif current_dict == "urban":
                    buffer, entry_counter, processed = process_urban_dictionary(
                        line_content, buffer, buffer_level, entry_counter
                    )
                else:
                    buffer, entry_counter, processed = process_entry_line_english(
                        line_content, buffer, buffer_level, entry_counter
                    )

                if processed:
                    continue

            if (
                next_tag
                in ("#pos", "#search_term_related", "#language", "#search_feedback")
                or next_tag is None
            ):
                if buffer.strip():
                    buffer = flush_buffer(buffer, buffer_level + 1)

    if buffer.strip():
        buffer = flush_buffer(buffer, buffer_level + 1)


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
