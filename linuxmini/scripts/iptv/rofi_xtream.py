#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import psutil
import requests
import yaml

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# ========== CONFIG ==========
CACHE_DIR = Path("/home/rash/.config/scripts/_cache/iptv/xtream")
FAVORITES_FILE = CACHE_DIR / "favorites.json"
CACHE_EXPIRY = 12 * 3600  # 12 hours in seconds
NOTIFICATION_ID = "1719"

# Load Xtream proxy credentials from environment or sops secrets files
XTREAM_PROXY_SERVER = os.getenv("XTREAM_PROXY_SERVER", "")
XTREAM_PROXY_USERNAME = os.getenv("XTREAM_PROXY_USERNAME", "")
XTREAM_PROXY_PASSWORD = os.getenv("XTREAM_PROXY_PASSWORD", "")

# Fallback to reading from sops secrets files if env vars not set
if not all([XTREAM_PROXY_SERVER, XTREAM_PROXY_USERNAME, XTREAM_PROXY_PASSWORD]):
    secrets_dir = Path(os.getenv("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "secrets"
    xtream_secrets_file = secrets_dir / "xtream"

    if xtream_secrets_file.exists():
        try:
            with xtream_secrets_file.open() as f:
                xtream_data = yaml.safe_load(f)
            XTREAM_PROXY_SERVER = xtream_data.get("upstream", {}).get("server", "")
            XTREAM_PROXY_USERNAME = xtream_data.get("upstream", {}).get("username", "")
            XTREAM_PROXY_PASSWORD = xtream_data.get("upstream", {}).get("password", "")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to load secrets from {xtream_secrets_file}: {e}")

if not all([XTREAM_PROXY_SERVER, XTREAM_PROXY_USERNAME, XTREAM_PROXY_PASSWORD]):
    raise RuntimeError("❌ Missing proxy credentials (check sops-secrets service)")

# ========== UTILS ==========

def configure_logging(args):
    logging_utils.configure_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

def ensure_dirs(path):
    if not path.exists():
        logging.debug(f"[DEBUG] Creating directory: {path}")
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)

def notify(title, message="", icon=None, timeout=None, close=False):
    if close:
        cmd = ["dunstify", "-C", NOTIFICATION_ID]
        logging.debug("[DEBUG] Closing notification")
    else:
        cmd = ["dunstify", "-r", NOTIFICATION_ID]
        if timeout:
            cmd += ["-t", str(timeout)]
        if icon:
            cmd += ["-i", icon]
        cmd += [title, message]
        if message:
            logging.debug(f"[DEBUG] Sending notification: {title} | {message}")
        else:
            logging.debug(f"[DEBUG] Sending notification: {title}")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def load_favorites():
    """Load favorites from JSON file."""
    if FAVORITES_FILE.exists():
        with FAVORITES_FILE.open() as f:
            return json.load(f)
    return {"favorites": [], "quickbinds": {}}

def save_favorites(favorites_data):
    """Save favorites to JSON file."""
    ensure_dirs(FAVORITES_FILE)
    with FAVORITES_FILE.open("w") as f:
        json.dump(favorites_data, f, indent=2)

def apply_tweaks(name):
    """Apply name tweaks from original script."""
    name_tweaks = {
        r"^(SWE\|\sTV)\s(\d+)": r"\1\2",
        r"^(SWEDEN\sTV)\s(\d+)": r"\1\2",
        r"^(SWE\|\sSVT)\s(\d+)": r"\1\2",
        r"^LSV\|": "SAL|",
        r"^SE:": "SWE|",
        r"^ES:": "ESP|",
        r"^IT:": "ITA|",
        r"^DE:": "GER|",
        r"^US:": "USA|",
        r"^AU:": "AUS|",
        r"^\(AU\)": "AUS|",
        r"^\[SE\]": "SWE|",
        "- NO EVENT STREAMING -": "",
    }

    name = name.upper().strip()
    for pattern, replacement in name_tweaks.items():
        if re.search(pattern, name):
            name = re.sub(pattern, replacement, name)
            break
    return name

# ========== CACHING ==========

def get_cache_file(action, extra_params=None):
    """Get cache file path for API call."""
    cache_name = action
    if extra_params:
        cache_name += "_" + "_".join(f"{k}_{v}" for k, v in extra_params.items())
    return CACHE_DIR / f"{cache_name}.json"

def load_from_cache(cache_file):
    """Load data from cache if not expired."""
    if not cache_file.exists():
        return None

    try:
        with cache_file.open() as f:
            cache_data = json.load(f)

        timestamp = cache_data.get("timestamp", 0)
        if time.time() - timestamp < CACHE_EXPIRY:
            logging.debug(f"[DEBUG] Using cached data from {cache_file}")
            return cache_data.get("data")
        else:
            logging.debug(f"[DEBUG] Cache expired for {cache_file}")
    except (json.JSONDecodeError, KeyError) as e:
        logging.debug(f"[DEBUG] Cache file corrupted: {e}")

    return None

def save_to_cache(cache_file, data):
    """Save data to cache with timestamp."""
    ensure_dirs(cache_file)
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    with cache_file.open("w") as f:
        json.dump(cache_data, f, indent=2)
    logging.debug(f"[DEBUG] Saved data to cache: {cache_file}")

# ========== XTREAM API ==========

def make_api_call(action, extra_params=None):
    """Make Xtream API call with caching."""
    # Check cache first
    cache_file = get_cache_file(action, extra_params)
    cached_data = load_from_cache(cache_file)
    if cached_data is not None:
        return cached_data

    # Show persistent refreshing notification
    notify("🔄 Refreshing...", f"Updating {action.replace('_', ' ')}")

    url = f"{XTREAM_PROXY_SERVER}/player_api.php"
    params = {
        "username": XTREAM_PROXY_USERNAME,
        "password": XTREAM_PROXY_PASSWORD,
        "action": action
    }
    if extra_params:
        params.update(extra_params)

    # Headers to mimic a regular browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }

    try:
        logging.debug(f"[DEBUG] API call: {action}")
        response = requests.get(url, params=params, headers=headers, timeout=30)

        logging.debug(f"[DEBUG] Response status: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"[ERROR] API returned status {response.status_code}")
            if response.status_code == 520:
                logging.error("[ERROR] Server returned 520 - may be blocking requests")
            # Close refreshing notification and show error
            notify("", close=True)
            notify("❌ API Error", f"Server returned {response.status_code}")
            return None

        if not response.text.strip():
            logging.error("[ERROR] Empty response from API")
            # Close refreshing notification and show error
            notify("", close=True)
            notify("❌ API Error", "Empty response from server")
            return None

        try:
            data = response.json()
            logging.debug(f"[DEBUG] API response: {type(data)} with {len(data) if isinstance(data, list) else 'unknown'} items")

            # Save to cache
            save_to_cache(cache_file, data)

            # Close refreshing notification
            notify("", close=True)

            return data
        except json.JSONDecodeError as e:
            logging.error(f"[ERROR] Invalid JSON response: {e}")
            logging.debug(f"[DEBUG] Response text: {response.text[:200]}...")
            # Close refreshing notification and show error
            notify("", close=True)
            notify("❌ API Error", "Invalid response format")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"[ERROR] API call failed: {e}")
        # Close refreshing notification and show error
        notify("", close=True)
        notify("❌ API Error", f"Connection failed: {e}")
        return None

def get_live_categories():
    """Get live TV categories."""
    return make_api_call("get_live_categories")

def get_vod_categories():
    """Get VOD categories."""
    return make_api_call("get_vod_categories")

def get_series_categories():
    """Get series categories."""
    return make_api_call("get_series_categories")

def get_live_streams(category_id=None):
    """Get live streams, optionally filtered by category."""
    params = {"category_id": category_id} if category_id else None
    return make_api_call("get_live_streams", params)

def get_vod_streams(category_id=None):
    """Get VOD streams, optionally filtered by category."""
    params = {"category_id": category_id} if category_id else None
    return make_api_call("get_vod_streams", params)

def get_series(category_id=None):
    """Get series, optionally filtered by category."""
    params = {"category_id": category_id} if category_id else None
    return make_api_call("get_series", params)

def get_series_info(series_id):
    """Get series episodes."""
    return make_api_call("get_series_info", {"series_id": series_id})

# ========== STREAM HANDLING ==========

def build_stream_url(stream_id, stream_type="live", container_extension=None):
    """Build stream URL for MPV.

    IMPORTANT: The server requires the correct container extension:
    - .mkv movies must use .mkv (returns 302 redirect)
    - .mp4 movies must use .mp4 (returns 302 redirect)
    - Using wrong extension returns HTTP 551
    """
    if stream_type == "live":
        return f"{XTREAM_PROXY_SERVER}/live/{XTREAM_PROXY_USERNAME}/{XTREAM_PROXY_PASSWORD}/{stream_id}.ts"
    elif stream_type == "movie":
        ext = container_extension or "mkv"  # Fallback to mkv (most common)
        return f"{XTREAM_PROXY_SERVER}/movie/{XTREAM_PROXY_USERNAME}/{XTREAM_PROXY_PASSWORD}/{stream_id}.{ext}"
    elif stream_type == "series":
        ext = container_extension or "mkv"
        return f"{XTREAM_PROXY_SERVER}/series/{XTREAM_PROXY_USERNAME}/{XTREAM_PROXY_PASSWORD}/{stream_id}.{ext}"

def launch_mpv(stream_url, title):
    """Launch MPV with the stream."""
    logging.debug(f"[DEBUG] Launching MPV: {title}")
    logging.debug(f"[DEBUG] Stream URL: {stream_url}")

    try:
        subprocess.Popen([
            "mpv",
            "--force-window=immediate",
            "--cache=yes",
            "--cache-pause=no",
            "--cache-secs=20",
            "--demuxer-max-bytes=100M",
            "--demuxer-max-back-bytes=1M",
            "--network-timeout=60",
            "--stream-lavf-o=reconnect=1",
            "--stream-lavf-o=reconnect_streamed=1",
            "--stream-lavf-o=reconnect_delay_max=5",
            "--stream-lavf-o=follow_redirects=1",
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "--http-header-fields=Accept: */*",
            f"--referrer={XTREAM_PROXY_SERVER}",
            "--wayland-app-id=rofi_xtream",
            f"--title=Xtream - {title}",
            stream_url
        ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        # Copy URL to clipboard
        subprocess.run(["wl-copy", stream_url])
        notify("🎬 Launching stream...", title, timeout=2000)

    except Exception as e:
        logging.error(f"[ERROR] Failed to launch MPV: {e}")
        notify("❌ MPV Error", f"Failed to launch: {e}")

# ========== ROFI INTERFACE ==========

def format_channel_name(channel, favorites_data):
    """Format channel name with favorite/quickbind indicators."""
    name = apply_tweaks(channel.get("name", ""))
    stream_id = str(channel.get("stream_id", ""))

    # Check if it's a favorite
    is_favorite = stream_id in favorites_data["favorites"]

    # Check for quickbind
    quickbind_slot = None
    for slot, qb_id in favorites_data["quickbinds"].items():
        if qb_id == stream_id:
            quickbind_slot = slot
            break

    if quickbind_slot:
        return f"⭐ [{quickbind_slot}] FAV /// {name}"
    elif is_favorite:
        return f"⭐ FAV /// {name}"
    else:
        return f"🔷 {name}"

def sort_channels(channels, favorites_data):
    """Sort channels with favorites first."""
    def sort_key(channel):
        stream_id = str(channel.get("stream_id", ""))
        name = channel.get("name", "")

        # Get quickbind slot (lowest number = highest priority)
        quickbind_slot = 9999
        for slot, qb_id in favorites_data["quickbinds"].items():
            if qb_id == stream_id:
                quickbind_slot = int(slot)
                break

        # Check if favorite
        is_favorite = stream_id in favorites_data["favorites"]

        return (
            quickbind_slot,  # Quickbinds first
            0 if is_favorite else 1,  # Favorites next
            name.lower()  # Then alphabetical
        )

    return sorted(channels, key=sort_key)

def rofi_select(items, prompt, allow_quickbinds=False):
    """Show Rofi selection menu."""
    menu = "\n".join(items)

    cmd = ["rofi", "-dmenu", "-i", "-p", prompt]

    if allow_quickbinds:
        # Add instructions message
        cmd += ["-mesg", "Ctrl+0: Toggle favorites | Ctrl+1-9: Use quickbind slots"]
        # Add quickbind support - try Ctrl instead of Alt to avoid conflicts
        cmd += ["-kb-custom-10", "ctrl+0"]
        # Bind keys for slots 1-9
        for i in range(1, 10):
            cmd += [f"-kb-custom-{i-1}", f"ctrl+{i}"]

    result = subprocess.run(cmd, input=menu, capture_output=True, text=True)

    returncode = result.returncode
    selection = result.stdout.strip()

    if allow_quickbinds:
        if returncode == 19:  # Alt+0 - favorites menu
            return ("favorite", selection)
        elif 10 <= returncode <= 18:  # Alt+1-9 - quickbind slots
            slot = returncode - 9
            return ("quickbind", slot)

    if returncode == 0 and selection:
        return ("select", selection)

    return None

def show_main_menu():
    """Show main content type selection."""
    options = [
        "📺 Live TV",
        "🎬 Movies",
        "📽️ Series"
    ]

    result = rofi_select(options, "Select Content Type")
    if not result:
        return None

    _, selection = result

    if "Live TV" in selection:
        return "live"
    elif "Movies" in selection:
        return "movies"
    elif "Series" in selection:
        return "series"

    return None

def show_categories(content_type):
    """Show categories for the selected content type."""
    if content_type == "live":
        categories = get_live_categories()
    elif content_type == "movies":
        categories = get_vod_categories()
    elif content_type == "series":
        categories = get_series_categories()
    else:
        return None

    if not categories:
        notify("❌ Error", "Failed to load categories")
        return None

    # Add "All" option
    options = ["📋 All Categories"]
    options.extend([f"📁 {cat['category_name']}" for cat in categories])

    result = rofi_select(options, f"Select {content_type.title()} Category")
    if not result:
        return None

    _, selection = result

    if "All Categories" in selection:
        return None  # None means all categories

    # Find the selected category ID
    category_name = selection.replace("📁 ", "")
    for cat in categories:
        if cat["category_name"] == category_name:
            return cat["category_id"]

    return None

def show_streams(content_type, category_id=None):
    """Show streams for the selected category."""
    if content_type == "live":
        streams = get_live_streams(category_id)
    elif content_type == "movies":
        streams = get_vod_streams(category_id)
    elif content_type == "series":
        streams = get_series(category_id)
    else:
        return None

    if not streams:
        notify("❌ Error", "Failed to load streams")
        return None

    favorites_data = load_favorites()

    # Sort streams with favorites first
    sorted_streams = sort_channels(streams, favorites_data)

    # Format display names
    display_names = []
    for stream in sorted_streams:
        display_name = format_channel_name(stream, favorites_data)
        display_names.append(display_name)

    result = rofi_select(display_names, f"Select {content_type.title()}", allow_quickbinds=True)
    if not result:
        return None

    action, selection = result

    if action == "quickbind":
        # Handle quickbind selection
        slot = str(selection)
        stream_id = favorites_data["quickbinds"].get(slot)
        if stream_id:
            # Find the stream by ID
            for stream in sorted_streams:
                if str(stream.get("stream_id")) == stream_id:
                    return ("launch", stream, content_type)
        notify(f"❌ No stream assigned to slot [{slot}]", timeout=2000)
        return None

    elif action == "favorite":
        # Handle favorite toggle
        # Find the selected stream
        clean_selection = re.sub(r'^[⭐🔷]\s*(\[\d+\]\s*FAV\s*///\s*|FAV\s*///\s*)?', '', selection)
        for stream in sorted_streams:
            stream_name = apply_tweaks(stream.get("name", ""))
            if stream_name == clean_selection:
                return ("favorite", stream, content_type)
        return None

    elif action == "select":
        # Find the selected stream
        clean_selection = re.sub(r'^[⭐🔷]\s*(\[\d+\]\s*FAV\s*///\s*|FAV\s*///\s*)?', '', selection)
        for stream in sorted_streams:
            stream_name = apply_tweaks(stream.get("name", ""))
            if stream_name == clean_selection:
                if content_type == "series":
                    return ("series_info", stream, content_type)
                else:
                    return ("launch", stream, content_type)
        return None

    return None

def handle_series_episodes(series):
    """Handle series episode selection."""
    series_info = get_series_info(series["series_id"])
    if not series_info or "episodes" not in series_info:
        notify("❌ Error", "Failed to load episodes")
        return None

    episodes = []
    for season_num, season_data in series_info["episodes"].items():
        for episode in season_data:
            episode_title = f"S{str(season_num).zfill(2)}E{str(episode['episode_num']).zfill(2)} - {episode.get('title', 'Episode')}"
            episodes.append((episode_title, episode))

    if not episodes:
        notify("❌ Error", "No episodes found")
        return None

    episode_titles = [ep[0] for ep in episodes]
    result = rofi_select(episode_titles, f"Select Episode - {series['name']}")

    if not result:
        return None

    _, selection = result

    # Find selected episode
    for title, episode in episodes:
        if title == selection:
            return episode

    return None

def handle_favorite_management(stream, content_type):
    """Handle favorite and quickbind management."""
    favorites_data = load_favorites()
    stream_id = str(stream.get("stream_id"))
    stream_name = apply_tweaks(stream.get("name", ""))

    is_favorite = stream_id in favorites_data["favorites"]

    # Find current quickbind slot
    current_slot = None
    for slot, qb_id in favorites_data["quickbinds"].items():
        if qb_id == stream_id:
            current_slot = slot
            break

    # Build options
    if is_favorite:
        options = [f"🛑 Remove '{stream_name}' from favorites"]
    else:
        options = [f"⭐ Add '{stream_name}' to favorites"]

    # Add quickbind options
    for i in range(1, 10):
        slot = str(i)
        if current_slot == slot:
            options.append(f"🛑 Remove from quickbind slot [{i}]")
        elif slot in favorites_data["quickbinds"]:
            # Slot occupied by another stream
            other_stream_id = favorites_data["quickbinds"][slot]
            options.append(f"🔁 Replace slot [{i}] (currently occupied)")
        else:
            options.append(f"➕ Assign to quickbind slot [{i}]")

    result = rofi_select(options, "Manage Favorites")
    if not result:
        return False

    _, selection = result

    if "Remove" in selection and "favorites" in selection:
        # Remove from favorites
        if stream_id in favorites_data["favorites"]:
            favorites_data["favorites"].remove(stream_id)
        # Also remove from quickbinds
        if current_slot:
            favorites_data["quickbinds"].pop(current_slot, None)
        notify("⭐ Removed from favorites", stream_name, timeout=2000)

    elif "Add" in selection and "favorites" in selection:
        # Add to favorites
        if stream_id not in favorites_data["favorites"]:
            favorites_data["favorites"].append(stream_id)
        notify("⭐ Added to favorites", stream_name, timeout=2000)

    elif "quickbind slot" in selection:
        # Handle quickbind management
        slot_match = re.search(r'\[(\d)\]', selection)
        if slot_match:
            slot = slot_match.group(1)

            if "Remove from quickbind" in selection:
                favorites_data["quickbinds"].pop(slot, None)
                notify(f"🔓 Removed from slot [{slot}]", stream_name, timeout=2000)
            else:
                # Assign to quickbind (also make it a favorite)
                favorites_data["quickbinds"][slot] = stream_id
                if stream_id not in favorites_data["favorites"]:
                    favorites_data["favorites"].append(stream_id)
                notify(f"⭐ Assigned to slot [{slot}]", stream_name, timeout=2000)

    save_favorites(favorites_data)
    return True

# ========== MAIN ==========

def main():
    parser = argparse.ArgumentParser(description="Xtream API Rofi Interface")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--category", choices=["live", "movies", "series"],
                       help="Skip main menu and go directly to content type")
    parser.add_argument("--category-id", type=str, help="Skip category selection")

    args = parser.parse_args()
    configure_logging(args)

    ensure_dirs(CACHE_DIR)

    try:
        # Main navigation loop
        while True:
            # Step 1: Content type selection
            if args.category:
                content_type = args.category
                args.category = None  # Only use once
            else:
                content_type = show_main_menu()
                if not content_type:
                    break

            # Step 2: Category selection (skip by default - show all)
            if args.category_id:
                category_id = args.category_id
                args.category_id = None  # Only use once
            else:
                category_id = None  # Show all categories by default

            # Step 3: Stream selection and action
            while True:
                result = show_streams(content_type, category_id)
                if not result:
                    break

                action, stream, stream_type = result

                if action == "launch":
                    # Launch stream
                    stream_id = stream.get("stream_id")
                    title = apply_tweaks(stream.get("name", ""))
                    container_ext = stream.get("container_extension")
                    stream_url = build_stream_url(stream_id, "live" if stream_type == "live" else "movie", container_ext)
                    launch_mpv(stream_url, title)
                    return

                elif action == "series_info":
                    # Handle series episode selection
                    episode = handle_series_episodes(stream)
                    if episode:
                        episode_id = episode.get("id")
                        container_ext = episode.get("container_extension", "mp4")
                        title = f"{stream.get('name')} - {episode.get('title', 'Episode')}"
                        stream_url = build_stream_url(episode_id, "series", container_ext)
                        launch_mpv(stream_url, title)
                        return

                elif action == "favorite":
                    # Handle favorite management
                    if handle_favorite_management(stream, stream_type):
                        continue  # Refresh the stream list
                    break

                break

            # If we reach here, user wants to go back to main menu
            continue

    except KeyboardInterrupt:
        logging.debug("[DEBUG] Interrupted by user")
    except Exception as e:
        logging.error(f"[ERROR] Unexpected error: {e}")
        notify("❌ Error", str(e))

if __name__ == "__main__":
    main()