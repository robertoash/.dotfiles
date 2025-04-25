#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import psutil
from dotenv import load_dotenv

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# ========== CONFIG ==========
ALL_CH_JSON_FILENAME = "all_channels.json"

SOURCE_PATH = Path("/media/sda1/server_bkups/iptv_server/")
ALL_CH_SOURCE_JSON_PATH = SOURCE_PATH / ALL_CH_JSON_FILENAME

TARGET_PATH = Path("/home/rash/.config/scripts/_cache/rofi/iptv/")

INPUT_DIR = "input"
INPUT_TARGET_PATH = TARGET_PATH / INPUT_DIR
ALL_CH_INPUT_JSON_PATH = INPUT_TARGET_PATH / ALL_CH_JSON_FILENAME

OUTPUT_DIR = "output"
OUTPUT_TARGET_PATH = TARGET_PATH / OUTPUT_DIR
ALL_CH_OUTPUT_JSON_PATH = OUTPUT_TARGET_PATH / ALL_CH_JSON_FILENAME

ALL_CATS = ["tv", "movies", "series", "spicy", "all"]
FIELDS_TO_LEFT_JOIN = ["favorite", "quickbind"]
EXCLUDED_CHANNELS = [r"^### ### #"]
NOTIFICATION_ID = "1718"

env_path = Path.home() / ".secrets" / "iptv.env"
load_dotenv(dotenv_path=env_path)
USER_TO_REPLACE = os.getenv("USER_TO_REPLACE", "")
PASS_TO_REPLACE = os.getenv("PASS_TO_REPLACE", "")
EXTRA_USERNAME = os.getenv("EXTRA_USERNAME", "")
EXTRA_PASSWORD = os.getenv("EXTRA_PASSWORD", "")

if not all([USER_TO_REPLACE, PASS_TO_REPLACE, EXTRA_USERNAME, EXTRA_PASSWORD]):
    raise RuntimeError("❌ Missing credentials in .env file")

ROFI_CH_SORTING = {
    "quickbind": 0,
    "favorite": 1,
    "name": [
        {
            "regex_patterns": 2,
            "patterns_in_order": [
                r"^SWE|",
                r"^US|",
                r"^SAL|",
                r"^ESP|",
            ],
        },
        {
            "alphabetical": 3,
        },
    ],
}

# ========== UTILS ==========


def configure_logging(args):
    logging_utils.configure_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def slugify(text):
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")


def ensure_dirs(path):
    if not path.exists():
        logging.debug(f"[DEBUG] Creating directory: {path}")
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)


def normalize_filename(name: str) -> str:
    stem = Path(name).stem.lower()
    # Remove any pattern like _123 or _123_
    return re.sub(r"_\d+_?|_\d+$", "", stem).lower()


def notify(title, message="", icon=None, progress=None, close=False, timeout=None):
    cmd = ["dunstify", "-r", NOTIFICATION_ID]
    if close:
        cmd += ["-C"]
    else:
        if timeout:
            cmd += ["-t", str(timeout)]
        if icon:
            cmd += ["-i", icon]
        if progress is not None:
            cmd += ["-h", f"int:value:{progress}"]
        cmd += [title, message]
    if message:
        logging.debug(f"[DEBUG] Sending notification: {title} | {message}")
    else:
        logging.debug(f"[DEBUG] Sending notification: {title}")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_pid_alive(pid):
    alive = psutil.pid_exists(pid)
    logging.debug(f"[DEBUG] Checking PID {pid}: {'alive' if alive else 'dead'}")
    return alive


def save_json(path, data, backup=False):
    logging.debug(f"[DEBUG] Saving JSON to {path} (backup={backup})")
    ensure_dirs(path)

    if backup and path.exists():
        backup = path.with_name(path.stem + "_prev.json")
        path.replace(backup)

    with path.open("w") as f:
        json.dump(data, f, indent=2)


def handle_fav_names(channels):
    for ch in channels:
        name = ch["name"]
        if ch.get("quickbind"):
            slot = ch["quickbind"]
            display_name = f"⭐ [{slot}] FAV /// {name}"
        elif ch.get("favorite", False):
            display_name = f"⭐ FAV /// {name}"
        else:
            display_name = f"🔷 {name}"
        ch["display_name"] = display_name
    return channels


def sort_channels(channels):
    def channel_sort_key(ch):
        sort_key = []

        # 1. Quickbind
        if "quickbind" in ROFI_CH_SORTING:
            sort_key.append(
                ch.get("quickbind") if ch.get("quickbind") is not None else 9999
            )

        # 2. Favorite
        if "favorite" in ROFI_CH_SORTING:
            sort_key.append(0 if ch.get("favorite") else 1)

        # 3. Name-based rules
        if "name" in ROFI_CH_SORTING:
            name = ch.get("name", "")
            for rule in ROFI_CH_SORTING["name"]:
                if "regex_patterns" in rule:
                    patterns = rule["patterns_in_order"]
                    for i, pattern in enumerate(patterns):
                        if re.search(pattern, name):
                            sort_key.append(i)
                            break
                    else:
                        sort_key.append(len(patterns))
                elif "alphabetical" in rule:
                    sort_key.append(name.lower())

        return tuple(sort_key)

    return sorted(channels, key=channel_sort_key)


def toggle_favorite(channel, enable=None):
    """Toggles or explicitly sets a channel's favorite status."""
    if enable is None:
        channel["favorite"] = not channel.get("favorite", False)
    else:
        channel["favorite"] = bool(enable)


# ========== CORE LOGIC ==========


def load_channels(path):
    logging.debug("[DEBUG] Starting channel load")
    if path.exists():
        logging.debug(f"[DEBUG] Loading channels from {path}")
        with path.open() as f:
            data = json.load(f)
            logging.debug(f"[DEBUG] Loaded {len(data)} channels from cache")
            return data
    logging.debug("[DEBUG] No cache found, returning empty list")
    return []


def left_join_metadata(source_channels, target_channels, fields):
    """
    Performs a LEFT JOIN-style merge of metadata fields from source to target using channel_id.

    For each channel in target_channels:
    - If a channel with the same channel_id exists in source_channels,
      copy specified fields (e.g., favorite) if present.
    - Fields in target will only be updated if found in the source.

    Channels present only in source (but not in target) are ignored.
    """
    logging.debug(
        f"[DEBUG] Starting LEFT JOIN of {len(source_channels)} → {len(target_channels)} channels"
    )

    meta_map = {
        ch["channel_id"]: {f: ch.get(f) for f in fields}
        for ch in source_channels
        if "channel_id" in ch
    }

    matches = 0
    for ch in target_channels:
        meta = meta_map.get(ch.get("channel_id"))
        if not meta:
            logging.debug(
                f"[DEBUG] No match for channel: {ch['name']} ({ch['group']}) → metadata not merged"
            )
            continue
        matches += 1
        for field in fields:
            if field in meta and meta[field] is not None:
                ch[field] = meta[field]

    logging.info(
        f"[INFO] Metadata joined for {matches} out of {len(target_channels)} channels"
    )

    return target_channels


def split_and_save_cat_jsons(channels_json):
    """Splits JSON into multiple files based on category."""
    for category in ALL_CATS:
        if category == "all":
            filtered_json = channels_json  # Don't filter — save everything
        else:
            filtered_json = [
                channel for channel in channels_json if channel["category"] == category
            ]
        logging.debug(f"[DEBUG] Saving {category} channels: {len(filtered_json)}")
        save_json(
            OUTPUT_TARGET_PATH / f"{category}_channels.json",
            filtered_json,
            backup=True,
        )


def sync_json_to_upstream():
    """Sync upstream JSON into local input, preserving metadata fields."""
    logging.debug("[DEBUG] Sync JSON triggered")

    if not ALL_CH_SOURCE_JSON_PATH.exists():
        logging.error(f"❌ Upstream JSON not found: {ALL_CH_SOURCE_JSON_PATH}")
        return

    upstream_channels = load_channels(ALL_CH_SOURCE_JSON_PATH)

    # 🧠 Now we merge FROM INPUT (our last run), not _prev or output
    if ALL_CH_OUTPUT_JSON_PATH.exists():
        input_channels = load_channels(ALL_CH_OUTPUT_JSON_PATH)
    else:
        input_channels = []

    joined_channels = left_join_metadata(
        input_channels, upstream_channels, fields=FIELDS_TO_LEFT_JOIN
    )

    joined_channels = [
        {**ch, "url": patch_stream_url(ch["url"])} for ch in joined_channels
    ]

    # Save merged result back to input (since input is state now)
    save_json(ALL_CH_INPUT_JSON_PATH, joined_channels, backup=True)
    split_and_save_cat_jsons(joined_channels)

    for field in FIELDS_TO_LEFT_JOIN:
        local_count = sum(1 for ch in joined_channels if ch.get(field))
        updated_count = sum(1 for ch in upstream_channels if ch.get(field))

        if local_count > updated_count:
            logging.warning(
                f"[WARN] Metadata field `{field}` dropped from "
                f"{local_count} to {updated_count} during left join"
            )
        elif local_count == updated_count:
            if local_count == 0:
                logging.info(
                    f"[INFO] No records updated for `{field}` during left join"
                )
            else:
                logging.info(
                    f"[INFO] Metadata field `{field}` fully preserved ({local_count})"
                )
        else:
            logging.info(
                f"[INFO] Metadata field `{field}` expanded: {local_count} → {updated_count}"
            )


def patch_stream_url(url: str) -> str:
    # Skip if already patched
    if f"/{EXTRA_USERNAME}/{EXTRA_PASSWORD}/" in url:
        return url

    old_segment = f"/{USER_TO_REPLACE}/{PASS_TO_REPLACE}/"
    new_segment = f"/{EXTRA_USERNAME}/{EXTRA_PASSWORD}/"

    if old_segment in url:
        return url.replace(old_segment, new_segment)
    return url  # unchanged if pattern not found


def filter_for_show(category):
    relevant_json = OUTPUT_TARGET_PATH / f"{category}_channels.json"
    logging.debug(f"[DEBUG] Cache path: {relevant_json}")

    filtered_channels = safe_load_channels(relevant_json, category)

    logging.debug(f"[DEBUG] Loaded {len(filtered_channels)} total channels")

    sorted_channels = sort_channels(filtered_channels)

    return handle_fav_names(sorted_channels)


def safe_load_channels(path, category=None):
    """Load channels from path. Trigger sync if file is missing/empty."""
    if not path.exists() or path.stat().st_size < 10:
        logging.warning(f"[WARN] Channel cache missing or empty: {path}")
        sync_json_to_upstream()  # Auto-fallback
    channels = load_channels(path)
    if category:
        channels = [ch for ch in channels if ch.get("category") == category]
    return channels


def handle_sync_json():
    """Handle the --sync-json command line argument."""
    sync_json_to_upstream()
    logging.info(f"[INFO] Sync complete. Fresh cache saved to {ALL_CH_INPUT_JSON_PATH}")


def launch_mpv(selected_entry):
    """Launch MPV with caching, retry, and background tolerance."""
    logging.debug(f"[DEBUG] Launching MPV: {selected_entry}")

    try:
        subprocess.Popen(
            [
                "mpv",
                "--quiet",  # Suppress logs in terminal
                "--force-window=immediate",  # Open window immediately, even before playback starts
                "--cache=yes",  # Enable playback cache
                "--cache-pause=no",  # Instant start
                "--cache-secs=20",  # Buffer 20 seconds of media ahead
                "--demuxer-max-bytes=100M",  # Allow demuxer to read up to 100MB into buffer
                "--demuxer-max-back-bytes=1M",  # Up to 1MB back-buffering (helps with seeking)
                "--network-timeout=60",  # Wait up to 60s on network stalls before aborting
                "--stream-lavf-o=reconnect=1",  # Reconnect if the stream fails
                "--stream-lavf-o=reconnect_streamed=1",  # Reconnect streamed formats
                "--stream-lavf-o=reconnect_delay_max=5",  # Max 5s before retrying a reconnect
                "--wayland-app-id=rofi_iptv",
                f"--title=IPTV - {selected_entry['name']}",  # Title with channel name
                selected_entry["url"],
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.debug("[DEBUG] MPV launched successfully")
    except Exception as e:
        logging.error(f"[ERROR] Failed to launch MPV: {e}")
        subprocess.run(["dunstify", "⚠️ MPV Error", f"Failed to launch stream: {e}"])


def rofi_select(channels):
    logging.debug("[DEBUG] Opening Rofi menu with favorite toggle + quickbinds")
    menu = "\n".join(ch["display_name"] for ch in channels)

    quickbinds = sorted(
        [ch for ch in channels if "quickbind" in ch], key=lambda ch: ch["quickbind"]
    )
    kb_args = []
    for i in range(len(quickbinds)):
        kb_args += [f"-kb-custom-{i}", f"Alt+{i}"]
    kb_args += ["-kb-custom-10", "Alt+0"]

    result = subprocess.run(
        ["rofi", "-dmenu", "-i", "-p", "Select IPTV Channel"] + kb_args,
        input=menu,
        capture_output=True,
        text=True,
    )

    returncode = result.returncode
    logging.debug(f"[DEBUG] Rofi return code: {returncode}")
    stdout = result.stdout.strip()

    if returncode == 19:  # Alt+0
        return ("favorite", stdout)
    elif 10 <= returncode <= 18:  # Alt+1 to Alt+9
        slot = returncode - 9  # 10 → 1, 11 → 2, ..., 17 → 8, 18 was already handled
        return ("quickbind", slot)
    elif returncode == 0:
        return ("launch", stdout)
    else:
        return None


def handle_selected_channel(selected_url, sorted_and_favs):
    """Handle the selected channel by launching MPV and showing notifications."""
    logging.debug(f"[DEBUG] User selected: {selected_url}")
    selected_entry = next(
        (ch for ch in sorted_and_favs if ch["url"] == selected_url), None
    )
    if selected_entry:
        name = selected_entry["name"]
        notify(
            "Launching stream...",
            f"🎬 {name}",
            timeout=2000,
        )

    logging.debug("[DEBUG] Launching MPV with caching")

    launch_mpv(selected_entry)

    logging.debug("[DEBUG] MPV exited, script ending")


def handle_favorite_toggle(selected_channel, sorted_and_favs):
    toggle_favorite(selected_channel)
    save_json(ALL_CH_INPUT_JSON_PATH, sorted_and_favs, backup=True)
    save_json(ALL_CH_OUTPUT_JSON_PATH, sorted_and_favs, backup=True)
    split_and_save_cat_jsons(sorted_and_favs)
    notify("⭐ Favorite toggled", selected_channel["name"], timeout=2000)


def handle_favorite_submenu(display_name, selected_channel, sorted_and_favs):
    has_fav = selected_channel.get("favorite", False)
    current_slot = selected_channel.get("quickbind")

    if has_fav:
        instruction = "🧭 Select to remove from favorites, or manage quickbind slot"
    else:
        instruction = "🧭 Select to add to favorites, or assign a quickbind slot"

    rofi_lines = [instruction, display_name]  # 🥇 Channel name now always second line

    for i in range(1, 10):
        if current_slot == i:
            label = f"🛑 Remove from Quickbind Slot [{i}]"
        else:
            owner = next(
                (ch for ch in sorted_and_favs if ch.get("quickbind") == i), None
            )
            if owner and owner != selected_channel:
                label = f"🔁 Replace {owner['name']} on Quickbind Slot [{i}]"
            elif current_slot:
                label = f"🔁 Move to Quickbind Slot [{i}]"
            else:
                label = f"➕ Add to Quickbind Slot [{i}]"
        rofi_lines.append(label)

    submenu = subprocess.run(
        ["rofi", "-dmenu", "-i", "-p", "Modify favorites"],
        input="\n".join(rofi_lines),
        capture_output=True,
        text=True,
    )

    selection = submenu.stdout.strip()

    if not selection or selection == instruction:
        notify(
            "❌ Invalid choice. Please select a channel or quickbind slot.",
            timeout=2000,
        )
        return True

    if selection == display_name:
        if has_fav:
            selected_channel.pop("favorite", None)
            selected_channel.pop("quickbind", None)
            notify("⭐ Favorite removed", selected_channel["name"], timeout=2000)
            # 🧼 Resort entire list by name
            sorted_and_favs.sort(key=lambda ch: ch["name"].lower())
        else:
            selected_channel["favorite"] = True
            notify("⭐ Favorite added", selected_channel["name"], timeout=2000)

    elif match := re.search(r"\[(\d)\]", selection):
        slot = int(match.group(1))
        if "Remove from Quickbind" in selection:
            selected_channel.pop("quickbind", None)
            notify(
                f"🔓 Quickbind [{slot}] removed", selected_channel["name"], timeout=2000
            )
        else:
            for ch in sorted_and_favs:
                if ch.get("quickbind") == slot:
                    ch.pop("quickbind")
            selected_channel["quickbind"] = slot
            selected_channel["favorite"] = True
            notify(
                f"⭐ Assigned to quickbind [{slot}]",
                selected_channel["name"],
                timeout=2000,
            )

    save_json(ALL_CH_OUTPUT_JSON_PATH, sorted_and_favs, backup=True)
    split_and_save_cat_jsons(sorted_and_favs)
    return True


# ========== MAIN ==========


def main():
    global FLAGS

    logging.debug("[DEBUG] Starting main()")

    parser = argparse.ArgumentParser(
        description="Launch IPTV channels via Rofi with category filtering.",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="tv",
        choices=ALL_CATS,
        help="Channel category to show [default: tv].",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.",
    )
    parser.add_argument(
        "--sync-json",
        action="store_true",
        help="Sync upstream JSON into local cache, preserving favorites",
    )

    args = parser.parse_args()

    configure_logging(args)

    logging.debug("[DEBUG] Debug mode enabled")

    if args.category not in ALL_CATS:
        logging.error(f"[ERROR] Invalid category: {args.category}")
        sys.exit(1)
    if args.sync_json:
        handle_sync_json()
        sys.exit(0)
    logging.debug(f"[DEBUG] Category selected: {args.category}")

    while True:
        sorted_and_favs = filter_for_show(args.category)

        logging.debug("[DEBUG] Showing user menu")
        selected = rofi_select(sorted_and_favs)

        if not selected:
            logging.debug("[DEBUG] No channel selected, exiting")
            break

        action, selection = selected

        logging.debug(f"[DEBUG] Selected action: {action}, selection: {selection}")

        selected_channel = next(
            (
                ch
                for ch in sorted_and_favs
                if ch.get("display_name") == selection or ch.get("name") == selection
            ),
            None,
        )

        if action == "quickbind":
            slot = int(selection)
            quickbound = next(
                (ch for ch in sorted_and_favs if ch.get("quickbind") == slot), None
            )
            if quickbound:
                handle_selected_channel(
                    selected_url=quickbound["url"],
                    sorted_and_favs=sorted_and_favs,
                )
            else:
                notify(f"❌ No channel assigned to quickbind [{slot}]", timeout=2000)
            break

        if not selected_channel:
            logging.warning(f"[WARN] Selected display name not found: {selection}")
            break

        if action == "favorite":
            if handle_favorite_submenu(
                display_name=selection,
                selected_channel=selected_channel,
                sorted_and_favs=sorted_and_favs,
            ):
                continue

        elif action == "launch":
            handle_selected_channel(
                selected_url=selected_channel["url"],
                sorted_and_favs=sorted_and_favs,
            )
            break


if __name__ == "__main__":
    main()
