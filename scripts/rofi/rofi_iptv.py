#!/usr/bin/env python3
import argparse
import hashlib
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
M3U_PATH = Path("/media/sda1/server_bkups/iptv_server/nordic.m3u")
FULL_CHANNELS_PATH = Path(
    "/home/rash/.config/scripts/_cache/rofi/iptv/all_channels.json"
)
LOGO_CACHE_DIR = Path("/home/rash/.config/scripts/_cache/rofi/iptv/logos")

LOCK_PATH = LOGO_CACHE_DIR / ".logo_download.lock"
STOP_PATH = LOGO_CACHE_DIR / ".logo_download.stop"  # Stop signal path

DOWNLOAD_CONNECTIONS_PER_SERVER = 3
DOWNLOAD_CONNECTIONS_PER_FILE = 2

GROUP_HANDLING = {
    "TV": ["MOVIES", "SERIES", "ADULTS"],
    "MOVIES": ["MOVIES"],
    "SERIES": ["SERIES"],
    "SPICY": ["ADULTS"],
}

NAME_TWEAKS = {
    r"^SWE\| TV (\d{1,2})": r"SWE| TV\1",
    r"^SWE\| SVT (\d{1,2})": r"SWE| SVT\1",
    "- NO EVENT STREAMING -": "",
    "SE:": "SWE|",
}
EXCLUDED_CHANNELS = [r"^### ### #"]
NOTIFICATION_ID = "9999"

FLAGS = {"refresh_channels": False, "refresh_logos": False, "dump_cache": False}

# ========== UTILS ==========


def configure_logging(args):
    logging_utils.configure_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def slugify(text):
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")


def is_excluded(name):
    excluded = any(re.match(pattern, name) for pattern in EXCLUDED_CHANNELS)
    if excluded:
        logging.debug(f"[DEBUG] Channel excluded: {name}")
    return excluded


def apply_name_tweaks(name):
    for pattern, replacement in NAME_TWEAKS.items():
        name = re.sub(pattern, replacement, name)
    return name


def ensure_dirs(path):
    if not path.exists():
        logging.debug(f"[DEBUG] Creating directory: {path}")
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)


def strip_trailing_number(filename: str) -> str:
    """Strips _1, _2, etc. from the end of a slugified name."""
    return re.sub(r"(_\d+)?\.png$", ".png", filename)


def guess_category(group, tvg_id=None, tvg_name=None):
    TARGET_TVGS = ["se:", "dk:", "no:", "fi:", "it:", "se-", "swe|"]
    group = (group or "").lower()
    tvg_id = (tvg_id or "").lower()
    tvg_name = (tvg_name or "").lower()

    if not tvg_id:
        if "ppv" in group or any(tvg_name.startswith(pfx) for pfx in TARGET_TVGS):
            return "TV"
        elif "adults" in group or "xx" in tvg_id or "xxx" in tvg_name:
            return "SPICY"
        elif "series" in group:
            return "SERIES"
        else:
            return "MOVIES"
    elif "adults" in group or "xx" in tvg_id or "xxx" in tvg_name:
        return "SPICY"
    else:
        return "TV"


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
    logging.debug(f"[DEBUG] Sending notification: {title} | {message}")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_pid_alive(pid):
    alive = psutil.pid_exists(pid)
    logging.debug(f"[DEBUG] Checking PID {pid}: {'alive' if alive else 'dead'}")
    return alive


def is_valid_local_logo(path):
    logging.debug(f"[DEBUG] Validating logo path: {path}")
    return (
        path
        and Path(path).exists()
        and mimetypes.guess_type(path)[0].startswith("image")
        and Path(path).parent == LOGO_CACHE_DIR
    )


def save_json(path, data, backup=False):
    logging.debug(f"[DEBUG] Saving JSON to {path} (backup={backup})")
    ensure_dirs(path)

    if backup and path.exists():
        backup = path.with_name(path.stem + "_prev.json")
        path.replace(backup)

    with path.open("w") as f:
        json.dump(data, f, indent=2)


def load_cached_channels(path):
    logging.debug(f"[DEBUG] Loading channels from {path}")
    if path.exists():
        with path.open() as f:
            data = json.load(f)
            logging.debug(f"[DEBUG] Loaded {len(data)} channels from cache")
            return data
    logging.debug("[DEBUG] No cache found, returning empty list")
    return []


def generate_channel_id(channel: dict) -> str:
    key_fields = [
        (channel.get("name") or "").strip(),
        (channel.get("group") or "").strip().upper(),
        (channel.get("url") or "").strip(),
        (channel.get("logo_url") or "").strip(),
    ]
    joined = "|".join(key_fields)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]  # short but unique


def sort_channels_for_display(channels):
    """Sorts channels with favorites at the top."""
    return sorted(channels, key=lambda ch: not ch.get("favorite", False))


def handle_favorite_names(channels):
    for ch in channels:
        name = ch["name"]
        if ch.get("favorite", False):
            display_name = f"⭐ FAVORITE - {name}"
        else:
            display_name = f"🔷 {name}"
        ch["display_name"] = display_name
    return channels


def toggle_favorite(channel, enable=None):
    """Toggles or explicitly sets a channel's favorite status."""
    if enable is None:
        channel["favorite"] = not channel.get("favorite", False)
    else:
        channel["favorite"] = bool(enable)


# ========== CORE LOGIC ==========


def load_or_parse_channels():
    logging.debug("[DEBUG] Starting channel load/parse")
    m3u_mtime = M3U_PATH.stat().st_mtime
    if FULL_CHANNELS_PATH.exists():
        cache_mtime = FULL_CHANNELS_PATH.stat().st_mtime
        if not FLAGS["refresh_channels"] and m3u_mtime <= cache_mtime:
            logging.debug("[DEBUG] Using cached channels")
            return load_cached_channels(FULL_CHANNELS_PATH)

    logging.debug("[DEBUG] Parsing M3U file")
    # Parse full m3u
    parsed = parse_m3u(M3U_PATH)

    # Generate channel_id hash
    for ch in parsed:
        key_fields = [
            ch.get("name", "") or "",
            ch.get("group", "") or "",
            ch.get("url", "") or "",
            ch.get("logo_url", "") or "",
        ]
        ch["channel_id"] = hashlib.sha256("".join(key_fields).encode()).hexdigest()

    logging.debug(f"[DEBUG] Saving {len(parsed)} parsed channels")
    save_json(FULL_CHANNELS_PATH, parsed, backup=True)

    return parsed


def parse_m3u(path):
    logging.debug(f"[DEBUG] Starting M3U parse: {path}")
    channels = []
    with path.open(encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("#EXTINF:"):
            meta, url = lines[i], lines[i + 1]
            tvg_id = re.search(r'tvg-id="([^"]+)"', meta)
            group = re.search(r'group-title="([^"]+)"', meta)
            name = re.search(r'tvg-name="([^"]+)"', meta)
            logo = re.search(r'tvg-logo="([^"]+)"', meta)
            if group and name:
                group, name, tvg_id = (
                    group.group(1),
                    name.group(1),
                    tvg_id.group(1) if tvg_id else "",
                )
                if is_excluded(name):
                    i += 2
                    continue
                name = apply_name_tweaks(name)
                local_logo = str(LOGO_CACHE_DIR / f"{slugify(name)}.png")
                channel = {
                    "tvg_id": tvg_id,
                    "name": name,
                    "group": group,
                    "category": guess_category(group, tvg_id, name),
                    "url": url,
                    "logo_url": logo.group(1) if logo else None,
                    "logo_local": local_logo if Path(local_logo).exists() else None,
                }
                channel["channel_id"] = generate_channel_id(channel)
                channels.append(channel)
        i += 1
    logging.info(f"[INFO] Parsed {len(channels)} channels from M3U")
    return channels


def filter_channels_by_category(channels, category):
    logging.debug(f"[DEBUG] Filtering channels for category: {category}")
    filtered = []

    for ch in channels:
        group = ch.get("group", "").upper()
        if category == "TV":
            # TV includes everything not matching other categories
            if not any(
                tag in group
                for tag in GROUP_HANDLING["MOVIES"]
                + GROUP_HANDLING["SERIES"]
                + GROUP_HANDLING["SPICY"]
            ):
                filtered.append(ch)
        else:
            keywords = GROUP_HANDLING.get(category, [])
            if any(tag in group for tag in keywords):
                filtered.append(ch)

    logging.debug(f"[DEBUG] Found {len(filtered)} channels in category {category}")
    return filtered


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
        strip_trailing_number(f.name) for f in LOGO_CACHE_DIR.glob("*.png")
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

    try:
        # Ensure path before writing lock
        ensure_dirs(LOCK_PATH)
        LOCK_PATH.write_text(str(os.getpid()))

        total = len(channels)
        downloaded = new = refreshed = skipped = failed = 0

        for i, ch in enumerate(channels, 1):
            # Check for stop signal before continuing
            if STOPPED := STOP_PATH.exists():
                logging.debug("[DEBUG] Stop signal received. Aborting logo download.")
                STOPPED = True
                break

            name = ch["name"]
            logo_url = ch.get("logo_url")
            if not logo_url:
                logging.debug(f"[DEBUG] Skipping {name} (no logo_url)")
                continue

            ensure_dirs(LOGO_CACHE_DIR)
            local_path = LOGO_CACHE_DIR / f"{slugify(name)}.png"
            filename = local_path.name
            unchanged = prev_logo_map.get(ch["channel_id"], "") == logo_url

            if not FLAGS["refresh_logos"] and unchanged:
                logging.debug(f"[DEBUG] Skipping {name} (unchanged)")
                skipped += 1
                continue
            basename = strip_trailing_number(filename)
            if basename in existing_basenames:
                logging.debug(
                    f"[DEBUG] Skipping {name} (basename '{basename}' already cached)"
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
            if downloaded > 0:
                notify(
                    "Downloading logos...",
                    f"{downloaded} dl ({new} new, {refreshed} refreshed), "
                    f"{skipped} skipped, {failed} failed",
                    progress=progress,
                )

    finally:
        end_time = time.time()
        if not STOPPED:
            save_json(FULL_CHANNELS_PATH, channels, backup=False)
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
                f"({new} new, {refreshed} refreshed), {skipped} skip, {failed} fail"
            )
            logging.debug("[DEBUG] Cleaning up unused logos")
            cleanup_unused_logos()
        else:
            logging.info("[INFO] Logo download was interrupted by stop signal")
            notify(
                "⚠️ Logo download stopped",
                f"{downloaded} dl ({new} new, {refreshed} refreshed) | "
                f"{skipped} skip | {failed} fail",
                timeout=3000,
            )

        if LOCK_PATH.exists():
            LOCK_PATH.unlink()


def trigger_logo_stop():
    STOP_PATH = LOGO_CACHE_DIR / ".logo_download.stop"
    STOP_PATH.touch()
    logging.info("[INFO] Stop signal sent to background logo downloader.")


def cleanup_unused_logos():
    current_channels = load_cached_channels(FULL_CHANNELS_PATH)
    referenced = {
        Path(ch["logo_local"]).name for ch in current_channels if ch.get("logo_local")
    }

    deleted = kept = skipped = 0
    for file in LOGO_CACHE_DIR.iterdir():
        if not file.is_file():
            continue  # skip dirs or junk

        mime, _ = mimetypes.guess_type(str(file))
        if mime and mime.startswith("image"):
            if file.name not in referenced:
                logging.debug(f"[DEBUG] Deleting unused image: {file}")
                file.unlink()
                deleted += 1
            else:
                kept += 1
        else:
            logging.debug(f"[DEBUG] Skipping non-image file: {file} ({mime})")
            skipped += 1

    logging.info(
        f"[INFO] Cleanup complete: {deleted} deleted, {kept} kept, {skipped} skipped."
    )


def rofi_select(channels):
    logging.debug("[DEBUG] Opening Rofi menu")
    menu = "\n".join(ch["display_name"] for ch in channels)
    try:
        selected = subprocess.run(
            ["rofi", "-dmenu", "-i", "-p", "Select IPTV Channel"],
            input=menu,
            capture_output=True,
            text=True,
            check=True,
        )
        display_name = selected.stdout.strip()
        url = next(
            (ch["url"] for ch in channels if ch["display_name"] == display_name), None
        )
        logging.debug(f"[DEBUG] User selected: {display_name}")
        return url
    except subprocess.CalledProcessError:
        logging.debug("[DEBUG] User cancelled selection")
        return None


# ========== MAIN ==========


def main():
    global DUMP_CACHE, FORCE_LOGO_REFRESH, FORCE_CHANNEL_REFRESH

    logging.debug("[DEBUG] Starting main()")

    valid_categories = list(GROUP_HANDLING.keys())

    parser = argparse.ArgumentParser(
        description="Launch IPTV channels via Rofi with category filtering.",
    )
    parser.add_argument(
        "--refresh-channels",
        action="store_true",
        help="Force re-parse of the M3U and update all category caches.",
    )
    parser.add_argument(
        "--download-logos",
        action="store_true",
        help="Force re-download of all channel logos.",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="TV",
        choices=valid_categories,
        help="Channel category to show [default: TV].",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.",
    )
    parser.add_argument(
        "--dump-cache",
        action="store_true",
        help="Dump the cache and start from scratch.",
    )
    parser.add_argument(
        "--download-logos-only",
        action="store_true",
        help="Only download logos and exit.",
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
    logging.debug(f"[DEBUG] M3U path: {M3U_PATH}")
    logging.debug(f"[DEBUG] Cache path: {FULL_CHANNELS_PATH}")
    logging.debug(f"[DEBUG] Logo cache: {LOGO_CACHE_DIR}")

    if args.stop:
        trigger_logo_stop()
        sys.exit(0)
    if args.dump_cache:
        DUMP_CACHE = True
        FORCE_LOGO_REFRESH = True
        FORCE_CHANNEL_REFRESH = True
        logging.debug("[DEBUG] Cache dump requested — forcing full refresh")
    if args.refresh_channels:
        FORCE_CHANNEL_REFRESH = True
        logging.debug("[DEBUG] Forcing channel refresh")
        logging.debug("[DEBUG] Forcing channel refresh")
    if args.download_logos:
        FORCE_LOGO_REFRESH = True
        logging.debug("[DEBUG] Forcing logo download")
    if args.cleanup:
        cleanup_unused_logos()
        sys.exit(0)
    if args.download_logos_only:
        logging.debug("[DEBUG] Download-logos-only mode activated")
        all_channels = load_cached_channels(FULL_CHANNELS_PATH)
        prev_path = FULL_CHANNELS_PATH.with_name(FULL_CHANNELS_PATH.stem + "_prev.json")
        if prev_path.exists():
            all_channels_prev = load_cached_channels(prev_path)
        else:
            logging.debug("[DEBUG] No previous channel cache found, using empty list")
            all_channels_prev = []
        download_logos(all_channels, all_channels_prev)
        sys.exit(0)

    logging.debug(f"[DEBUG] Category selected: {args.category}")

    all_channels = load_or_parse_channels()
    logging.debug(f"[DEBUG] Loaded {len(all_channels)} total channels")

    filtered = filter_channels_by_category(all_channels, args.category)
    logging.debug(
        f"[DEBUG] Filtered down to {len(filtered)} channels for category '{args.category}'"
    )

    # Start background logo download
    cmd = ["python3", str(Path(__file__).resolve()), "--download-logos-only"]
    logging.debug(f"[DEBUG] Launching background logo downloader: {cmd}")
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    sorted_channels = sort_channels_for_display(filtered)

    sorted_and_favs = handle_favorite_names(sorted_channels)

    logging.debug("[DEBUG] Showing user menu")
    selected = rofi_select(sorted_and_favs)

    if selected:
        logging.debug(f"[DEBUG] User selected: {selected}")
        selected_entry = next((ch for ch in filtered if ch["url"] == selected), None)
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
                    "🎬 Launching stream...",
                    f"🎬 {name}",
                    timeout=2000,
                )

        logging.debug("[DEBUG] Launching MPV with caching")
        subprocess.Popen(
            [
                "mpv",
                "--cache=yes",
                "--cache-secs=10",
                "--demuxer-max-bytes=50M",
                "--no-audio-display",
                "--force-window=immediate",
                selected,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logging.debug("[DEBUG] MPV exited, script ending")
        sys.exit(0)
    else:
        logging.debug("[DEBUG] No channel selected, exiting")


if __name__ == "__main__":
    main()
