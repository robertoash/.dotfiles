#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path

DEBUG = False
indent_level = 1
indent_size = 4


def reset_submap():
    subprocess.Popen(["hyprctl", "dispatch", "submap", "reset"])


def validate_meta(meta):
    meta_required_keys = ["title", "replace_id", "urgency", "time"]

    # Ensure required fields are present
    missing = [k for k in meta_required_keys if k not in meta]
    if missing:
        subprocess.run(
            [
                "dunstify",
                "-r",
                "9999",
                "-u",
                "normal",
                "-a",
                "submap-parser",
                "⚠️ Missing submap metadata",
                f"Missing: {', '.join(missing)}",
            ]
        )
        exit(1)
    else:
        print(f"Meta: {meta}") if DEBUG else None
    return


def extract_meta(path: Path, meta: dict):
    # Extract JSON metadata from submap line
    for line in path.read_text().splitlines():
        if line.strip().startswith("submap = "):
            match = re.search(r"#\s*(\{.*\})$", line)
            if match:
                try:
                    meta.update(json.loads(match.group(1)))
                except json.JSONDecodeError as e:
                    subprocess.run(
                        [
                            "dunstify",
                            "-r",
                            "9999",
                            "-u",
                            "normal",
                            "-a",
                            "submap-parser",
                            "⚠️ Failed to parse submap metadata",
                            f"{e.msg}",
                        ]
                    )
                    print(f"Error: {e}") if DEBUG else None
                    exit(1)

    # Compose meta title with optional icon
    meta["title"] = (
        f'{meta["icon"]} {meta["title"]}' if "icon" in meta else meta["title"]
    )

    # Add action to meta
    meta["action"] = (
        meta["action"] if "action" in meta else "submap-reset, Reset submap"
    )

    return meta


def parse_submap_entries(path: Path, entries: list, meta: dict):
    bind_line = re.compile(r"^bind\s*=\s*(.+?),\s*(.+?),\s*exec,.*?#\s*(\{.*\})$")
    submap_meta_re = re.compile(r"^submap\s*=\s*.+?#\s*(\{.*\})$")

    with path.open() as f:
        for line in f:
            line = line.strip()

            # Submap-level metadata
            meta_match = submap_meta_re.match(line)
            if meta_match:
                try:
                    meta.update(json.loads(meta_match.group(1)))
                except json.JSONDecodeError as e:
                    print(f"Error: {e}") if DEBUG else None
                    pass
                continue

            # Per-bind metadata
            match = bind_line.match(line)
            if match:
                modifiers, key, metadata_json = match.groups()
                try:
                    bind_meta = json.loads(metadata_json)
                    # Skip entries with visibility set to hide
                    if bind_meta.get("visibility") == "hide":
                        continue
                    combo = (
                        f"{modifiers.strip()} + {key.strip()}"
                        if modifiers.strip()
                        else key.strip()
                    )
                    label = bind_meta.get("name", "Unknown")
                    icon = bind_meta.get("icon", "")
                    entries.append((combo, f"{icon} {label}".strip()))
                except json.JSONDecodeError as e:
                    print(f"Error: {e}") if DEBUG else None
                    continue

    return entries, meta


def parse_submap(path: Path):
    entries = []
    meta = {}

    meta = extract_meta(path, meta)
    validate_meta(meta)
    entries, meta = parse_submap_entries(path, entries, meta)

    return entries, meta


def launch_dunstify(entries, meta):
    indent = indent_level * indent_size * " "
    body = "\n".join(f"{indent}{key}: {label}" for key, label in entries)
    print(f"Body: {body}") if DEBUG else None
    command = [
        "dunstify",
        "-r",
        str(meta["replace_id"]),
        "-a",
        "hypr-launcher",
        meta["title"],
        body,
        "-u",
        meta["urgency"],
        "-t",
        str(meta["time"]),
        "-A",
        meta["action"],
    ]
    print(f"Command: {command}") if DEBUG else None
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}") if DEBUG else None
        exit(1)

    if result.stdout.strip() == "submap-reset":
        reset_submap()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Path to the submap config")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    if args.debug:
        DEBUG = True
        print(f"Debug mode: {DEBUG}")

    submap_path = Path(args.path).expanduser()
    print(f"Checking submap existence: {submap_path}") if DEBUG else None
    if not submap_path.exists():
        print(f"❌ Error: file not found: {submap_path}")
        exit(1)

    print(f"Submap path found: {submap_path}") if DEBUG else None

    entries, meta = parse_submap(submap_path)
    print(f"Parsed submap: {entries}") if DEBUG else None
    print(f"Meta: {meta}") if DEBUG else None
    launch_dunstify(entries, meta)
