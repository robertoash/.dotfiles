#!/usr/bin/env python3

import argparse
import hashlib
import json
import logging
import os
import random
import re
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, iterparse, tostring

from dotenv import load_dotenv

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# Directories and filenames
CACHE_BASE = Path("/home/rash/.config/scripts/_cache/iptv")

INPUT_DIR = CACHE_BASE / "input"
SERVER_FILES_DIR = CACHE_BASE / "server_files"
OUTPUT_DIR = CACHE_BASE / "output"

FULL_M3U_FILE_PATH = INPUT_DIR / "FULL_M3U.m3u"
FULL_EPG_FILE_PATH = INPUT_DIR / "FULL_EPG.xml"
TEST_M3U_FILE_PATH = INPUT_DIR / "test_playlist.m3u"

OUTPUT_M3U_FILE_PATH = SERVER_FILES_DIR / "nordic.m3u"
OUTPUT_M3U_MINI_FILE_PATH = SERVER_FILES_DIR / "nordic_mini.m3u"
OUTPUT_EPG_FILE_PATH = SERVER_FILES_DIR / "nordic_epg.xml"
OUTPUT_EPG_MINI_FILE_PATH = SERVER_FILES_DIR / "nordic_epg_mini.xml"

OUTPUT_JSON_ALL_CH_FILE_PATH = OUTPUT_DIR / "all_channels.json"

NAME_TWEAKS = {
    r"^(SWE\|\sTV)\s(\d+)": r"\1\2",  # SWE| TV 4 → SWE| TV4
    r"^(SWEDEN\sTV)\s(\d+)": r"\1\2",  # SWEDEN TV 4 → SWEDEN TV4
    r"^(SWE\|\sSVT)\s(\d+)": r"\1\2",  # SWE| SVT 2 → SWE| SVT2
    r"^LSV\|": "SAL|",
    r"^SE:": "SWE|",
    r"^ES:": "ESP|",
    r"^IT:": "ITA|",
    r"^DK:": "DEN|",
    r"^NO:": "NOR|",
    r"^FI:": "FIN|",
    r"^DE:": "GER|",
    r"^US:": "USA|",
    r"^AU:": "AUS|",
    r"^\(AU\)": "AUS|",
    r"^\[SE\]": "SWE|",
    "- NO EVENT STREAMING -": "",
}

ALL_CATS = ["tv", "movies", "series", "spicy"]


env_path = Path.home() / ".config" / "scripts" / "_secrets" / "iptv.env"
load_dotenv(dotenv_path=env_path)
# Xtream codes
XTREAM_SERVER = os.getenv("XTREAM_SERVER", "")
FIRST_USERNAME = os.getenv("FIRST_USERNAME", "")
FIRST_PASSWORD = os.getenv("FIRST_PASSWORD", "")
EXTRA_USERNAME = os.getenv("EXTRA_USERNAME", "")
EXTRA_PASSWORD = os.getenv("EXTRA_PASSWORD", "")

if not all([XTREAM_SERVER, FIRST_USERNAME, FIRST_PASSWORD]):
    raise RuntimeError("❌ Missing credentials in .env file")

# Filters
FILTER_RULES = {
    "exclude": {
        "name_patterns": [r"^\s*#+\s*.*?\s*#+\s*$"],
        "group_contains": ["religious", "religion", "biblical", "christian"],
    },
    "include": {
        "group_targets": {
            "full": {
                "tv": [
                    "4K UHD",
                    "sweden",
                    "uk|",
                    "eu|",
                    "es|",
                    "it|",
                    "dk|",
                    "us|",
                    "au|",
                    "denmark",
                    "finland",
                    "norway",
                    "australia",
                    "lat| el salvador",
                ],
                "movies": ["|se|", "|dk|", "|en|", "|es|", "top"],
                "series": ["|multi|", "|en|", "|es|", "|se|", "|la|"],
                "spicy": ["adults"],
            },
            "mini": {
                "tv": ["sweden", "lat| el salvador", "uk|", "us|"],
                "spicy": ["adults"],
            },
        },
        "tvg_prefixes": ["se:", "dk:", "no:", "fi:", "it:", "se-", "swe|"],
    },
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.6312.86 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/18.18362",
]
CURL_USER_AGENT = random.choice(USER_AGENTS)


def configure_logging(args):
    logging_utils.configure_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def backup_if_exists(path):
    if path.exists():
        backup = path.with_suffix(".bkup")
        path.replace(backup)
        logging.debug(f"[DEBUG] Backed up {path} to {backup}")
    else:
        logging.debug(f"[DEBUG] {path} does not exist. Backup skipped.")


def ensure_dirs(path):
    if not path.exists():
        logging.debug(f"[DEBUG] Creating dir/file: {path}")
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)


def save_and_backup(filemap: dict, backup=False):
    """
    Saves multiple files from a {Path: data} dict.
    Optionally backs up existing ones.
    """
    for path, data in filemap.items():
        ensure_dirs(path)
        if backup:
            backup_if_exists(path)
        else:
            logging.debug(f"[DEBUG] No backup needed for {path}")

        with path.open("w", encoding="utf-8") as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, indent=2)
            elif isinstance(data, str):
                f.write(data)
            elif isinstance(data, list):  # If ever passed unjoined lines
                f.write("\n".join(data))
            else:
                f.write(str(data))  # Fallback


def timestamp_playlist(content, start_time):
    """Adds a dummy timestamp channel with script run duration."""
    logging.debug("[DEBUG] Timestamping playlist...")
    end_time = datetime.now()
    timestamp = end_time.strftime("%Y-%m-%d %H:%M")
    duration = end_time - start_time
    minutes, seconds = divmod(duration.total_seconds(), 60)
    duration_str = f"{int(minutes)}m {int(seconds)}s"

    timestamp_channel = (
        f'#EXTINF:-1 tvg-id="" tvg-name="UPDATED: {timestamp}" '
        f'tvg-logo="" group-title="SYSTEM",UPDATED: {timestamp}. Took {duration_str}\n'
        f"http://dummy.url/updated_timestamp\n"
    )
    # Add header + timestamp + rest of content
    return f"#EXTM3U\n{timestamp_channel}\n{content.strip()}\n"


def slugify(text):
    return re.sub(r"[^\w\-]+", "_", text.lower()).strip("_")


def generate_channel_id(channel: dict) -> str:
    key_fields = [
        (channel.get("name") or "").strip(),
        (channel.get("group") or "").strip().upper(),
        (channel.get("url") or "").strip(),
        (channel.get("logo_url") or "").strip(),
    ]
    joined = "|".join(key_fields)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]  # short but unique


def split_and_save_cat_jsons(channels_json):
    """Splits JSON into multiple files based on category."""
    for category in ALL_CATS:
        filtered_json = [
            channel for channel in channels_json if channel["category"] == category
        ]
        save_and_backup(
            {OUTPUT_DIR / f"{category}_channels.json": filtered_json},
            backup=True,
        )


def check_connectivity(host="line.trx-ott.com", port=80):
    logging.info(f"Checking connectivity to {host}:{port}...")
    try:
        socket.create_connection((host, port), timeout=10)
        logging.info("✅ Connectivity OK.")
    except Exception as exc:
        logging.error(f"❌ Connectivity issue: {exc}")


def download_file(url, output_path, description="file"):
    """Downloads a file using aria2c with smart timeout and retry settings."""
    try:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        backup_if_exists(output_path)

        aria_command = [
            "aria2c",
            "--max-connection-per-server=1",
            "--split=4",
            "--continue=true",
            "--auto-file-renaming=false",
            "--retry-wait=10",
            "--max-tries=20",
            "--timeout=120",  # Match curl's connect timeout
            "--max-download-limit=0",  # No speed cap
            "--max-overall-download-limit=0",
            "--connect-timeout=120",  # NEW: matches curl
            "--max-resume-failure-tries=5",
            "--summary-interval=10",
            "--console-log-level=warn",
            "-d",
            str(output_path.parent),
            "-o",
            output_path.name,
            url,
        ]

        logging.debug(f"[DEBUG] Downloading {description} with aria2c...")
        logging.debug(f"[DEBUG] Running: {' '.join(map(str, aria_command))}")

        result = subprocess.run(aria_command, stdout=sys.stdout, stderr=sys.stderr)
        logging.debug(f"[DEBUG] Return code: {result.returncode}")

        if result.returncode != 0:
            logging.error(f"[ERROR] ❌ Error downloading {description}")
            return None

        if output_path.exists() and output_path.stat().st_size > 0:
            logging.info(f"✅ {description.capitalize()} downloaded to {output_path}")
            return output_path
        else:
            logging.error(f"[ERROR] ⚠️ Downloaded {description} is empty or missing.")
            return None
    except Exception as exc:
        logging.error(f"[ERROR] 💥 Exception during download of {description}: {exc}")
        return None


def download_full_playlist():
    url = (
        f"{XTREAM_SERVER}/get.php?username={FIRST_USERNAME}"
        f"&password={FIRST_PASSWORD}&type=m3u_plus&output=ts"
    )
    logging.debug(f"Playlist URL: {url}")
    return download_file(url, FULL_M3U_FILE_PATH, "playlist")


def download_epg():
    url = (
        f"{XTREAM_SERVER}/xmltv.php?username={FIRST_USERNAME}&password={FIRST_PASSWORD}"
    )
    logging.debug(f"EPG URL: {url}")
    return download_file(url, FULL_EPG_FILE_PATH, "EPG")


def apply_tweaks(apply_field):
    apply_field = apply_field.upper().strip()
    for pattern, replacement in NAME_TWEAKS.items():
        if re.search(pattern, apply_field):
            apply_field = re.sub(pattern, replacement, apply_field)
            break  # 🛑 STOP after the first successful tweak!
    return apply_field


def looks_like_series_by_name(display_name: str) -> bool:
    return bool(re.search(r"S\d{1,2}\s+E\d{1,3}", display_name, re.IGNORECASE))


def guess_category(group, tvg_id=None, tvg_name=None, display_name=None):
    group = group.lower() if group else ""
    tvg_id = tvg_id.lower() if tvg_id else ""
    tvg_name = tvg_name.lower() if tvg_name else ""
    display_name = display_name.lower() if display_name else ""

    if not tvg_id:
        if "ppv" in group or any(
            tvg_name.startswith(prefix)
            for prefix in FILTER_RULES["include"]["tvg_prefixes"]
        ):
            category = "tv"
        elif "adults" in group:
            category = "spicy"
        elif (
            "series" in group
            or looks_like_series_by_name(group)
            or looks_like_series_by_name(display_name)
        ):
            category = "series"
        else:
            category = "movies"
    elif "adults" in group:
        category = "spicy"
    else:
        category = "tv"
    return category


def should_include(name, category, group, filter_type="full"):
    name = name.strip().lower()
    group = group.strip().lower()
    category = category.strip().lower()

    def record_reason(reason):
        logging.debug(
            f"[DEBUG] {filter_type} filter rejected "
            f"cat:{category} - name:{name} - group:{group} → {reason}"
        )

    for pattern in FILTER_RULES["exclude"]["name_patterns"]:
        if re.match(pattern, name, re.IGNORECASE):
            record_reason(f"excluded_by_name_pattern: {pattern}")
            return False

    if any(bad in group for bad in FILTER_RULES["exclude"]["group_contains"]):
        record_reason(f"excluded_by_group_keyword: {group}")
        return False

    if filter_type == "mini" and category == "series":
        record_reason(f"excluded_by_debug_flag: {category}")
        return False

    targets = FILTER_RULES["include"]["group_targets"].get(filter_type, {})
    accepted_groups = targets.get(category, [])

    matched = next((target for target in accepted_groups if target in group), None)
    if not matched:
        record_reason(f"group_not_matched: {group} [{category}/{filter_type}]")
        return False

    return True


def filter_epg_streaming(epg_path: Path, allowed_ids: set[str]) -> str:
    from copy import deepcopy
    
    # Elements to keep
    root = Element("tv")
    channels = []
    programmes = []

    for event, elem in iterparse(epg_path, events=("end",)):
        if elem.tag == "channel" and elem.attrib.get("id") in allowed_ids:
            # Make a deep copy before clearing to preserve element content
            channels.append(deepcopy(elem))
        elif elem.tag == "programme" and elem.attrib.get("channel") in allowed_ids:
            # Make a deep copy before clearing to preserve element content
            programmes.append(deepcopy(elem))
        elem.clear()  # Free memory early

    for el in channels + programmes:
        root.append(el)

    return tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def parse_and_filter_playlist(playlist_file, epg_path=None):
    logging.debug(f"[DEBUG] Starting M3U parse: {playlist_file}")
    channels_json = []
    filtered_lines = []
    mini_filtered_lines = []

    # EPG ids
    full_ids = set()
    mini_ids = set()

    with open(playlist_file, "r", encoding="utf-8") as f:
        lines = [
            line.strip()
            for line in f
            if line.strip() and line.strip().upper() != "#EXTM3U"
        ]
    i = 0

    while i < len(lines) - 1:
        if lines[i].startswith("#EXTINF:"):
            meta, stream_url = lines[i], lines[i + 1]

            def extract(pattern, string):
                match = re.search(pattern, string)
                return match.group(1) if match else ""

            tvg_id = extract(r'tvg-id="([^"]+)"', meta)
            group = extract(r'group-title="([^"]+)"', meta)
            name = extract(r'tvg-name="([^"]+)"', meta)
            logo = extract(r'tvg-logo="([^"]+)"', meta)
            # Get display name from the part after the comma (fallback if tvg-name missing)
            display_name = extract(r",(.*)$", meta).strip()

            if group and name:
                category = guess_category(group, tvg_id, name, display_name)

                # Run both filters separately
                include_full = should_include(
                    name=name,
                    category=category,
                    group=group,
                    filter_type="full",
                )
                include_mini = should_include(
                    name=name,
                    category=category,
                    group=group,
                    filter_type="mini",
                )

                if not include_full and not include_mini:
                    i += 2
                    continue  # skip completely

                name = apply_tweaks(name)
                group = apply_tweaks(group)
                # Fix metadata in M3U line
                meta = re.sub(r'tvg-name="[^"]+"', f'tvg-name="{name}"', meta)
                meta = re.sub(r'group-title="[^"]+"', f'group-title="{group}"', meta)
                meta = re.sub(
                    r",(.*)$", f",{name}", meta
                )  # Channel display name after comma

                channel = {
                    "tvg_id": tvg_id,
                    "name": name,
                    "group": group,
                    "category": category,
                    "url": stream_url,
                    "logo_url": logo or None,
                }
                channel["channel_id"] = generate_channel_id(channel)
                channels_json.append(channel)

                if include_full:
                    filtered_lines.append(meta)
                    filtered_lines.append(stream_url)
                    if tvg_id:
                        full_ids.add(tvg_id)

                if include_mini:
                    mini_filtered_lines.append(meta)
                    mini_filtered_lines.append(stream_url)
                    if tvg_id:
                        mini_ids.add(tvg_id)

            i += 2
        else:
            i += 1

    filtered_m3u = "\n".join(filtered_lines)
    mini_m3u = "\n".join(mini_filtered_lines)

    logging.info(f"[INFO] Parsed {len(channels_json)} channels from M3U")

    # 👇 EPG filtering here (ONLY if epg_path provided)
    logging.info("[INFO] Filtering Full & Mini EPGs...")
    filtered_epg = filtered_epg_mini = None
    if epg_path:
        filtered_epg = filter_epg_streaming(epg_path, full_ids)
        filtered_epg_mini = filter_epg_streaming(epg_path, mini_ids)

    return channels_json, filtered_m3u, mini_m3u, filtered_epg, filtered_epg_mini


def patch_stream_url(url: str) -> str:
    # Skip if already patched
    if f"/{EXTRA_USERNAME}/{EXTRA_PASSWORD}/" in url:
        return url

    old_segment = f"/{FIRST_USERNAME}/{FIRST_PASSWORD}/"
    new_segment = f"/{EXTRA_USERNAME}/{EXTRA_PASSWORD}/"

    if old_segment in url:
        return url.replace(old_segment, new_segment)
    return url  # unchanged if pattern not found


def left_join_metadata(source_channels, target_channels, fields):
    """
    Performs a LEFT JOIN-style merge of metadata fields from source to target using channel_id.

    For each channel in target_channels:
    - If a channel with the same channel_id exists in source_channels,
      copy specified fields (e.g., favorite) if present.
    - Fields in target will only be updated if found in the source.

    Channels present only in source (but not in target) are ignored.
    """
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


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode",
        )
        parser.add_argument(
            "--prepare-output-only",
            action="store_true",
            help=(
                "Skip download and parsing, only patch and split output based on "
                "existing input files."
            ),
        )
        args = parser.parse_args()

        configure_logging(args)

        start_time = datetime.now()

        if not args.prepare_output_only:
            check_connectivity()

            logging.info("[INFO] Downloading full playlist.")
            playlist_file = download_full_playlist()
            logging.info(f"[INFO] Downloaded full playlist to {playlist_file}.")

            logging.info("[INFO] Downloading EPG...")
            full_epg = download_epg()
            logging.info(f"[INFO] Downloaded EPG to {full_epg}...")
        else:
            logging.info("[INFO] Skipping download of full playlist and EPG...")
            playlist_file = INPUT_DIR / "FULL_M3U.m3u"
            full_epg = INPUT_DIR / "FULL_EPG.xml"

        if playlist_file:
            logging.info("[INFO] Parsing m3u and filtering...")
            channels_json, filtered_m3u, mini_m3u, filtered_epg, filtered_epg_mini = (
                parse_and_filter_playlist(playlist_file, epg_path=full_epg)
            )
            logging.info("[INFO] Timestamping m3u file...")
            if filtered_m3u:
                timestamped_m3u = timestamp_playlist(filtered_m3u, start_time)
            logging.info("[INFO] Timestamping MINI file...")
            if mini_m3u:
                timestamped_mini_m3u = timestamp_playlist(mini_m3u, start_time)
            logging.info("[INFO] Saving full + mini M3U and all_channels.json...")

            if OUTPUT_JSON_ALL_CH_FILE_PATH.exists():
                with OUTPUT_JSON_ALL_CH_FILE_PATH.open() as f:
                    old_channels = json.load(f)
                channels_json = left_join_metadata(
                    old_channels, channels_json, fields=["favorite", "quickbind"]
                )
            else:
                logging.info(
                    "[INFO] No existing intermediate JSON found. Skipping metadata join."
                )

            save_and_backup(
                {
                    OUTPUT_M3U_FILE_PATH: timestamped_m3u,
                    OUTPUT_M3U_MINI_FILE_PATH: timestamped_mini_m3u,
                    OUTPUT_JSON_ALL_CH_FILE_PATH: channels_json,
                },
                backup=False,
            )
            logging.info("[INFO] Splitting and saving category JSONs...")

            # 👇 PATCH all channel URLs BEFORE splitting
            patched_channels_json = [
                {**ch, "url": patch_stream_url(ch["url"])} for ch in channels_json
            ]

            # 👇 NOW split and save patched channels
            split_and_save_cat_jsons(patched_channels_json)

        if full_epg and filtered_epg and filtered_epg_mini:
            logging.info("[INFO] Saving filtered EPGs....")
            save_and_backup(
                {
                    OUTPUT_EPG_FILE_PATH: filtered_epg,
                    OUTPUT_EPG_MINI_FILE_PATH: filtered_epg_mini,
                },
                backup=False,
            )

    except Exception as exc:
        logging.error(f"[ERROR] Fatal error in main execution: {exc}")

    finally:
        logging.info("[INFO] Script finished.")


if __name__ == "__main__":
    main()
