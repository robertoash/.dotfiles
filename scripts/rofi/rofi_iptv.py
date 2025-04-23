#!/usr/bin/env python3
import argparse
import copy
import json
import logging
import mimetypes
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import psutil

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# ========== CONFIG ==========
ALL_CH_JSON_FILENAME = "all_channels.json"
SOURCE_PATH = Path("/media/sda1/server_bkups/iptv_server/")
TARGET_PATH = Path("/home/rash/.config/scripts/_cache/rofi/iptv/")
INPUT_DIR = "input"
OUTPUT_DIR = "output"
LOGO_DIR = "logos"
INPUT_TARGET_PATH = TARGET_PATH / INPUT_DIR
OUTPUT_TARGET_PATH = TARGET_PATH / OUTPUT_DIR
LOGO_CACHE_DIR = TARGET_PATH / LOGO_DIR
ALL_CH_SOURCE_JSON_PATH = SOURCE_PATH / ALL_CH_JSON_FILENAME
ALL_CH_INPUT_JSON_PATH = INPUT_TARGET_PATH / ALL_CH_JSON_FILENAME
ALL_CH_OUTPUT_JSON_PATH = OUTPUT_TARGET_PATH / ALL_CH_JSON_FILENAME

LOCK_PATH = LOGO_CACHE_DIR / ".logo_download.lock"
STOP_PATH = LOGO_CACHE_DIR / ".logo_download.stop"  # Stop signal path

DOWNLOAD_CONNECTIONS_PER_SERVER = 3
DOWNLOAD_CONNECTIONS_PER_FILE = 2

ALL_CATS = ["tv", "movies", "series", "spicy", "all"]
FIELDS_TO_LEFT_JOIN = ["favorite", "logo_local", "quickbind"]
LOGO_DOWNLOAD_CATS = ["tv", "movies"]
MOVIES_LOGO_FILTER = ["|en|"]

EXCLUDED_CHANNELS = [r"^### ### #"]
NOTIFICATION_ID = "1718"

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

FLAGS = {"force_logo_refresh": False}

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


def is_valid_local_logo(path):
    logging.debug(f"[DEBUG] Validating logo path: {path}")
    if not path or not Path(path).exists():
        return False

    mimetype, _ = mimetypes.guess_type(str(path))
    if mimetype and mimetype.startswith("image"):
        return True

    # Fallback: Accept image-looking files in the logo cache folder
    if Path(path).parent == LOGO_CACHE_DIR and path.suffix.lower() in [
        ".png",
        ".jpg",
        ".jpeg",
    ]:
        logging.debug(f"[DEBUG] Accepting {path} as fallback image")
        return True

    return False


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


def download_logos(channels, prev_channels):
    start_time = time.time()

    if STOP_PATH.exists():
        STOP_PATH.unlink()

    STOPPED = False

    logging.debug("[DEBUG] Starting logo download process")

    # Convert prev_channels list to a lookup dict
    prev_logo_map = {
        ch["channel_id"]: ch.get("logo_url", "")
        for ch in prev_channels
        if "channel_id" in ch
    }
    logging.debug(
        f"[DEBUG] Built logo URL map for {len(prev_logo_map)} previous channels"
    )

    existing_basenames = {
        normalize_filename(f.name) for f in LOGO_CACHE_DIR.glob("*.png")
    }

    if LOCK_PATH.exists():
        try:
            pid = int(LOCK_PATH.read_text())
            if is_pid_alive(pid):
                logging.debug(
                    f"[DEBUG] Lock active by PID {pid}, skipping logo download"
                )
                return
            else:
                LOCK_PATH.unlink()
        except Exception as e:
            logging.debug(f"[DEBUG] Error reading lock file: {e}")
            LOCK_PATH.unlink()

    # ✅ Force refresh if cache is completely empty (e.g., after nuke)
    if not any(LOGO_CACHE_DIR.glob("*.png")):
        logging.warning("[WARN] Logo cache is empty. Forcing refresh.")
        FLAGS["force_logo_refresh"] = True

    try:
        # Ensure path before writing lock
        ensure_dirs(LOCK_PATH)
        LOCK_PATH.write_text(str(os.getpid()))

        total = len(channels)
        downloaded = new = refreshed = skipped = failed = with_logo = 0

        for i, ch in enumerate(channels, 1):
            # Check for stop signal before continuing
            if STOPPED := STOP_PATH.exists():
                logging.debug("[DEBUG] Stop signal received. Aborting logo download.")
                STOPPED = True
                break

            if ch["category"] not in LOGO_DOWNLOAD_CATS:
                logging.debug(
                    f"[DEBUG] Skipping {ch['name']} (not in {LOGO_DOWNLOAD_CATS})"
                )
                continue
            if ch["category"] == "movies" and not any(
                filter in ch["group"].lower() for filter in MOVIES_LOGO_FILTER
            ):
                logging.debug(
                    f"[DEBUG] Skipping {ch['name']}: "
                    f"Movie doesn't contain filters {MOVIES_LOGO_FILTER}"
                )
                continue

            name = ch["name"]
            logo_url = ch.get("logo_url")
            if not logo_url:
                logging.debug(f"[DEBUG] Skipping {name} (no logo_url)")
                continue

            ensure_dirs(LOGO_CACHE_DIR)
            local_path = LOGO_CACHE_DIR / f"{slugify(name)}.png"
            filename = local_path.name
            unchanged = prev_logo_map.get(ch["channel_id"], "") == logo_url

            if not FLAGS["force_logo_refresh"] and unchanged:
                logging.debug(f"[DEBUG] Skipping {name} (unchanged)")
                skipped += 1
                continue
            basename = normalize_filename(filename)
            if ch["category"] == "tv" and basename in existing_basenames:
                logo_path = LOGO_CACHE_DIR / f"{basename}.png"
                ch["logo_local"] = str(logo_path)
                with_logo += 1
                logging.debug(
                    f"[DEBUG] Skipping {name} (basename '{basename}' already cached) "
                    f"→ assigned {logo_path.name}"
                )
                skipped += 1
                continue
            else:
                try:
                    logging.debug(f"[DEBUG] Downloading logo for {name} → {filename}")
                    was_present = local_path.exists()
                    subprocess.run(
                        [
                            "aria2c",
                            "--quiet=true",
                            "--dir",
                            str(LOGO_CACHE_DIR),
                            "--out",
                            filename,
                            "--allow-overwrite=true",
                            "--timeout=5",
                            "--max-tries=2",
                            "--max-connection-per-server",
                            str(DOWNLOAD_CONNECTIONS_PER_SERVER),
                            "--split",
                            str(DOWNLOAD_CONNECTIONS_PER_FILE),
                            logo_url,
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )
                    ch["logo_local"] = str(local_path)
                    with_logo += 1
                    existing_basenames.add(basename)
                    downloaded += 1
                    if was_present:
                        refreshed += 1  # File exists, so we're refreshing it
                    else:
                        new += 1  # File doesn't exist, so it's a new download
                except Exception as e:
                    logging.debug(f"[DEBUG] Error downloading logo for {name}: {e}")
                    failed += 1

            progress = int((i / total) * 100)
            notify(
                "Downloading logos...",
                f"{downloaded} dl ({new} new, {refreshed} refreshed), "
                f"{skipped} skipped, {failed} failed, {with_logo} with logo",
                progress=progress,
            )

    finally:
        end_time = time.time()
        if not STOPPED:
            # ✅ Save updated full list with new logo_local values
            save_json(ALL_CH_OUTPUT_JSON_PATH, channels, backup=False)
            # ✅ Ensure the input for the next run has up-to-date metadata
            save_json(ALL_CH_INPUT_JSON_PATH, channels, backup=False)

            # ✅ Save tv/movies category slices (all, not filtered)
            for cat in LOGO_DOWNLOAD_CATS:
                save_json(
                    OUTPUT_TARGET_PATH / f"{cat}_channels.json",
                    [ch for ch in channels if ch.get("category") == cat],
                    backup=False,
                )

            # Report on results
            if downloaded > 0:
                notify(
                    "✅ Logos done",
                    f"{downloaded} dl ({new} new, {refreshed} refreshed) | "
                    f"{skipped} skip | {failed} fail",
                    timeout=3000,
                )
            logging.debug(
                f"[DEBUG] Logo download took {end_time - start_time:.2f} seconds"
            )
            logging.debug(
                f"[DEBUG] Logo download complete: {downloaded} dl "
                f"({new} new, {refreshed} refreshed), {skipped} skip, "
                f"{failed} fail, {with_logo} with logo"
            )
            logging.debug("[DEBUG] Cleaning up unused logos")
            cleanup_unused_logos()
        else:
            logging.info("[INFO] Logo download was interrupted by stop signal")
            notify(
                "⚠️ Logo download stopped",
                f"{downloaded} dl ({new} new, {refreshed} refreshed) | "
                f"{skipped} skip | {failed} fail | {with_logo} with logo",
                timeout=3000,
            )

        if LOCK_PATH.exists():
            LOCK_PATH.unlink()


def trigger_logo_stop():
    STOP_PATH = LOGO_CACHE_DIR / ".logo_download.stop"
    STOP_PATH.touch()
    logging.info("[INFO] Stop signal sent to background logo downloader.")


def cleanup_unused_logos():
    all_referenced = set()

    for cat in ALL_CATS:
        path = OUTPUT_TARGET_PATH / f"{cat}_channels.json"
        if not path.exists():
            logging.debug(f"[DEBUG] Skipping {cat} (no cache found)")
            continue

        current_channels = load_channels(path)
        referenced = {
            Path(ch["logo_local"]).name
            for ch in current_channels
            if ch.get("logo_local")
        }

        logging.debug(f"[DEBUG] {cat}: {len(referenced)} logos referenced")
        all_referenced.update(referenced)

    # 🚨 Safety net: Avoid mass deletion if reference list is suspiciously small
    if len(all_referenced) < 10:
        logging.warning(
            "⚠️ Too few referenced logos — cleanup aborted to avoid mass deletion."
        )
        return

    deleted = kept = skipped = 0
    for file in LOGO_CACHE_DIR.iterdir():
        if not file.is_file():
            continue  # skip dirs or junk

        mime, _ = mimetypes.guess_type(str(file))
        if mime and mime.startswith("image"):
            if file.name not in all_referenced:
                # logging.debug(f"[DEBUG] Deleting unused image: {file}")
                file.unlink()
                deleted += 1
            else:
                kept += 1
        else:
            # logging.debug(f"[DEBUG] Skipping non-image file: {file} ({mime})")
            skipped += 1

    logging.info(
        f"[INFO] Cleanup complete: {deleted} deleted, {kept} kept, {skipped} skipped."
    )
    logging.debug("[DEBUG] ✅ Cleanup complete.")


def left_join_metadata(source_channels, target_channels, fields):
    """
    Performs a LEFT JOIN-style merge of metadata fields from source to target using channel_id.

    For each channel in target_channels:
    - If a channel with the same channel_id exists in source_channels,
      copy specified fields (e.g., favorite, logo_local) if present.
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
    if ALL_CH_INPUT_JSON_PATH.exists():
        input_channels = load_channels(ALL_CH_INPUT_JSON_PATH)
    else:
        input_channels = []

    joined_channels = left_join_metadata(
        input_channels, upstream_channels, fields=FIELDS_TO_LEFT_JOIN
    )

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
    if LOCK_PATH.exists():
        try:
            pid = int(LOCK_PATH.read_text())
            if is_pid_alive(pid):
                logging.warning(
                    f"[WARN] Sync aborted: logo download in progress by PID {pid}"
                )
                sys.exit(1)
            else:
                logging.debug("[DEBUG] Removing stale logo lock")
                LOCK_PATH.unlink()
        except Exception as e:
            logging.debug(f"[DEBUG] Failed to read logo lock: {e}")
            LOCK_PATH.unlink()
    sync_json_to_upstream()
    logging.info(f"[INFO] Sync complete. Fresh cache saved to {ALL_CH_INPUT_JSON_PATH}")


def handle_download_logos_only():
    """Handle the --download-logos-only argument.
    Merges metadata into input, downloads logos, and promotes updated state.
    """
    logging.debug("[DEBUG] Download-logos-only mode activated")

    if (
        not ALL_CH_INPUT_JSON_PATH.exists()
        or ALL_CH_INPUT_JSON_PATH.stat().st_size < 10
    ):
        logging.warning(
            f"[WARN] No valid merged input found: {ALL_CH_INPUT_JSON_PATH}. Syncing..."
        )
        sync_json_to_upstream()

    all_channels = load_channels(ALL_CH_INPUT_JSON_PATH)
    if not all_channels or not isinstance(all_channels, list):
        logging.error("❌ Input sync failed or upstream JSON is invalid.")
        sys.exit(1)

    all_channels_prev = copy.deepcopy(all_channels)

    all_channels = left_join_metadata(
        all_channels_prev, all_channels, FIELDS_TO_LEFT_JOIN
    )

    download_logos(all_channels, all_channels_prev)


def launch_mpv(selected):
    """Launch MPV with caching, retry, and background tolerance."""
    logging.debug(f"[DEBUG] Launching MPV: {selected}")

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
                selected,
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

    if returncode == 18:  # Alt+0
        return ("favorite", stdout)
    elif 10 <= returncode <= 17:  # Alt+1 to Alt+9
        slot = returncode - 9  # 10 → 1, 11 → 2, ..., 17 → 8, 18 was already handled
        return ("quickbind", slot)
    elif returncode == 0:
        return ("launch", stdout)
    else:
        return None


def handle_selected_channel(selected, sorted_and_favs):
    """Handle the selected channel by launching MPV and showing notifications."""
    logging.debug(f"[DEBUG] User selected: {selected}")
    selected_entry = next((ch for ch in sorted_and_favs if ch["url"] == selected), None)
    if selected_entry:
        name = selected_entry["name"]
        logo = selected_entry.get("logo_local")
        if is_valid_local_logo(logo):
            notify(
                "Launching stream...",
                f"🎬 {name}",
                icon=logo,
                timeout=4000,
            )
        else:
            notify(
                "Launching stream...",
                f"🎬 {name}",
                timeout=2000,
            )

    logging.debug("[DEBUG] Launching MPV with caching")

    launch_mpv(selected)

    logging.debug("[DEBUG] MPV exited, script ending")


def handle_favorite_toggle(selected_channel, sorted_and_favs):
    toggle_favorite(selected_channel)
    save_json(ALL_CH_OUTPUT_JSON_PATH, sorted_and_favs, backup=True)
    split_and_save_cat_jsons(sorted_and_favs)
    notify("⭐ Favorite toggled", selected_channel["name"], timeout=2000)


def handle_favorite_submenu(display_name, selected_channel, sorted_and_favs):
    has_fav = selected_channel.get("favorite", False)
    current_slot = selected_channel.get("quickbind")

    instruction = (
        "🧭 Select channel name to remove from favorites, "
        "or a quickbind slot to assign/remove"
    )
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
        "--force-logo-refresh",
        action="store_true",
        help="Force re-download of all channel logos.",
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
        "--download-logos-only",
        action="store_true",
        help="Only download logos and exit.",
    )
    parser.add_argument(
        "--sync-json",
        action="store_true",
        help="Sync upstream JSON into local cache, preserving favorites and logo paths",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove logos no longer referenced by any channel",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Signal background logo downloader to stop.",
    )

    args = parser.parse_args()

    configure_logging(args)

    logging.debug("[DEBUG] Debug mode enabled")
    logging.debug(f"[DEBUG] Logo cache: {LOGO_CACHE_DIR}")

    if args.stop:
        trigger_logo_stop()
        sys.exit(0)
    if args.force_logo_refresh:
        FLAGS["force_logo_refresh"] = True
        logging.debug("[DEBUG] Forcing logo download")
    if args.category not in ALL_CATS:
        logging.error(f"[ERROR] Invalid category: {args.category}")
        sys.exit(1)
    if args.sync_json:
        handle_sync_json()
        sys.exit(0)
    if args.cleanup:
        cleanup_unused_logos()
        sys.exit(0)
    if args.download_logos_only:
        handle_download_logos_only()
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
                if str(ch.get("quickbind")) == str(selection)
            ),
            None,
        )

        if action == "quickbind":
            slot = selection
            if selected_channel:
                handle_selected_channel(selected_channel["url"], sorted_and_favs)
            else:
                notify(f"❌ No channel assigned to quickbind [{slot}]", timeout=2000)
            break

        if not selected_channel:
            logging.warning(f"[WARN] Selected display name not found: {selection}")
            break

        if action == "favorite":
            if handle_favorite_submenu(selection, selected_channel, sorted_and_favs):
                continue

        elif action == "launch":
            handle_selected_channel(selected_channel["url"], sorted_and_favs)
            break


if __name__ == "__main__":
    main()
