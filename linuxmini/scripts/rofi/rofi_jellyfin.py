#!/usr/bin/env python3

import sys
import subprocess
import requests
import os
from pathlib import Path
import time
import pickle
from jellyfin_apiclient_python import JellyfinClient as OfficialJellyfinClient

CACHE_DIR = Path.home() / ".config/scripts/_cache/rofi_jellyfin"
CACHE_EXPIRY = 300  # 5 minutes

# Load Jellyfin credentials from SOPS secrets
JELLYFIN_URL = os.getenv("JELLYFIN_URL", "")
API_KEY = os.getenv("JELLYFIN_API_KEY", "")

# Fallback to reading from sops secrets files if env vars not set
if not all([JELLYFIN_URL, API_KEY]):
    secrets_dir = Path(os.getenv("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "secrets"
    jellyfin_secrets_file = secrets_dir / "jellyfin"

    if jellyfin_secrets_file.exists():
        try:
            with jellyfin_secrets_file.open() as f:
                jellyfin_data = yaml.safe_load(f)
            JELLYFIN_URL = jellyfin_data.get("server", "")
            API_KEY = jellyfin_data.get("api_key", "")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to load secrets from {jellyfin_secrets_file}: {e}")

if not all([JELLYFIN_URL, API_KEY]):
    raise RuntimeError("❌ Missing Jellyfin credentials (check sops-secrets service)")


class JellyfinClient:
    def __init__(self, base_url, api_key=""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {}
        self.user_id = None
        self.cache = {}

        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing cache if available
        self._load_cache()

        if api_key:
            self.headers["X-Emby-Token"] = api_key
            # Get user ID
            self._get_user_id()

    def _load_cache(self):
        """Load cache from disk"""
        cache_file = CACHE_DIR / "cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    self.cache = pickle.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self):
        """Save cache to disk"""
        cache_file = CACHE_DIR / "cache.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self.cache, f)
        except:
            pass

    def _get_cached(self, key):
        """Get cached value if not expired"""
        if key in self.cache:
            timestamp, value = self.cache[key]
            if time.time() - timestamp < CACHE_EXPIRY:
                return value
        return None

    def _set_cached(self, key, value):
        """Set cached value with timestamp"""
        self.cache[key] = (time.time(), value)
        self._save_cache()

    def _get_user_id(self):
        """Get the user ID for authenticated requests"""
        try:
            response = requests.get(f"{self.base_url}/Users", headers=self.headers)
            if response.status_code == 200:
                users = response.json()
                if users:
                    self.user_id = users[0]["Id"]
        except:
            pass

    def get_items(self, parent_id=None, item_type=None):
        """Get items from Jellyfin server with caching"""
        # Create cache key
        cache_key = f"items_{parent_id}_{item_type}"

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        params = {"Recursive": "true", "SortBy": "SortName", "SortOrder": "Ascending"}

        if parent_id:
            params["ParentId"] = parent_id

        if item_type:
            params["IncludeItemTypes"] = item_type

        # Use user-specific endpoint if we have a user ID
        if self.user_id:
            url = f"{self.base_url}/Users/{self.user_id}/Items"
        else:
            url = f"{self.base_url}/Items"

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 200:
            items = response.json().get("Items", [])
            self._set_cached(cache_key, items)
            return items
        return []

    def get_libraries(self):
        """Get all libraries with caching"""
        cache_key = "libraries"

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/Library/VirtualFolders"
        if self.api_key:
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)

        if response.status_code == 200:
            libraries = response.json()
            self._set_cached(cache_key, libraries)
            return libraries
        return []

    def delete_item(self, item_id):
        """Delete an item from Jellyfin"""
        url = f"{self.base_url}/Items/{item_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 204:
            # Clear cache on successful delete
            self.cache = {}
            self._save_cache()
            return True
        return False

    def get_item_details(self, item_id):
        """Get detailed information for a specific item with caching"""
        cache_key = f"details_{item_id}"

        # Check cache first
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        if self.user_id:
            url = f"{self.base_url}/Users/{self.user_id}/Items/{item_id}"
        else:
            url = f"{self.base_url}/Items/{item_id}"

        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            details = response.json()
            self._set_cached(cache_key, details)
            return details
        return None

    # Note: Direct streaming methods removed as we now use jellyfin-mpv-shim for playback

    def get_sessions(self):
        """Get active Jellyfin sessions"""
        url = f"{self.base_url}/Sessions"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []

    def get_mpv_shim_session(self):
        """Find jellyfin-mpv-shim session"""
        sessions = self.get_sessions()
        for session in sessions:
            client = session.get("Client", "").lower()
            app_name = session.get("ApplicationVersion", "").lower()
            device_name = session.get("DeviceName", "").lower()

            # Look for jellyfin-mpv-shim indicators
            if (
                "mpv" in client
                or "mpv" in app_name
                or "mpv" in device_name
                or "shim" in client
                or "shim" in app_name
                or "shim" in device_name
                or "jellyfin mpv shim" in device_name
            ):
                return session
        return None

    def debug_sessions(self):
        """Debug function to show all available sessions"""
        sessions = self.get_sessions()
        debug_info = f"Found {len(sessions)} sessions:\\n"
        for i, session in enumerate(sessions):
            debug_info += f"{i + 1}. Device: {session.get('DeviceName', 'Unknown')}\\n"
            debug_info += f"   Client: {session.get('Client', 'Unknown')}\\n"
            debug_info += f"   App: {session.get('ApplicationVersion', 'Unknown')}\\n"
            debug_info += f"   ID: {session.get('Id', 'Unknown')}\\n"
            debug_info += f"   Capabilities: {session.get('Capabilities', {})}\\n\\n"
        return debug_info

    def play_on_session(self, session_id, item_ids, play_command="PlayNow"):
        """Send play command to a specific session using playstate command"""

        # Try the playstate command endpoint format
        url = f"{self.base_url}/Sessions/{session_id}/Playing/Play"

        # For Play command, we need to send the item info
        data = {"ItemIds": [item_ids[0]], "PlayCommand": play_command}

        try:
            print(f"Trying PlaystateCommand Play: {url}")
            print(f"Data: {data}")
            response = requests.post(url, headers=self.headers, json=data)
            print(f"Response status: {response.status_code}")
            if response.status_code in [200, 204]:
                return True
            print(f"Response: {response.text}")

            # Fallback to the original approach
            return self._try_sessions_playing(session_id, item_ids[0], play_command)
        except Exception as e:
            print(f"Exception: {e}")
            return self._try_sessions_playing(session_id, item_ids[0], play_command)

    def _try_sessions_playing(self, session_id, item_id, play_command):
        """Try the /Sessions/{sessionId}/Playing endpoint with official API spec"""
        url = f"{self.base_url}/Sessions/{session_id}/Playing"

        # Use official API specification format
        data = {
            "itemIds": [item_id],
            "playCommand": play_command,
            "sessionId": session_id,  # Include sessionId in body too
        }

        try:
            print(f"Trying Sessions/Playing with official spec: {url}")
            print(f"Data: {data}")
            response = requests.post(url, headers=self.headers, json=data)
            print(f"Response status: {response.status_code}")
            if response.status_code in [200, 204]:
                return True
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

        return False


def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if not size_bytes:
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_item_size(item, client=None):
    """Get size from item, fetching detailed info if needed"""
    # For movies and episodes, get detailed info with MediaSources
    if client and item.get("Type") in ["Movie", "Episode"] and "Id" in item:
        detailed = client.get_item_details(item["Id"])
        if detailed and "MediaSources" in detailed and detailed["MediaSources"]:
            for source in detailed["MediaSources"]:
                if "Size" in source and source["Size"]:
                    return source["Size"]

    # Fallback to basic size field
    if "Size" in item and item["Size"]:
        return item["Size"]

    return None


def get_aggregate_size(item, client):
    """Calculate total size for series/seasons/libraries"""
    item_type = item.get("Type", "")
    # Check if this is a library
    if "CollectionType" in item:
        item_type = "Library"
    total_size = 0

    if item_type == "Series" and client:
        # Get all episodes in the series
        episodes = client.get_items(parent_id=item["Id"], item_type="Episode")
        for ep in episodes:
            size = get_item_size(ep, client)
            if size:
                total_size += size
    elif item_type == "Season" and client:
        # Get all episodes in the season
        episodes = client.get_items(parent_id=item["Id"], item_type="Episode")
        for ep in episodes:
            size = get_item_size(ep, client)
            if size:
                total_size += size
    elif item_type == "CollectionFolder" and client:
        # Get total for library (movies or all series)
        lib_name = item.get("Name", "").lower()
        if lib_name in ["movies", "films"]:
            movies = client.get_items(parent_id=item["ItemId"], item_type="Movie")
            for movie in movies:
                size = get_item_size(movie, client)
                if size:
                    total_size += size
        elif lib_name in ["tv shows", "tv", "series"]:
            series_list = client.get_items(parent_id=item["ItemId"], item_type="Series")
            for series in series_list:
                series_size = get_aggregate_size(series, client)
                total_size += series_size
    elif item_type == "Library" and client:
        # Handle libraries from VirtualFolders API
        collection_type = item.get("CollectionType", "")
        library_id = item.get("ItemId")
        if collection_type == "movies":
            movies = client.get_items(parent_id=library_id, item_type="Movie")
            for movie in movies:
                size = get_item_size(movie, client)
                if size:
                    total_size += size
        elif collection_type == "tvshows":
            series_list = client.get_items(parent_id=library_id, item_type="Series")
            for series in series_list:
                series_size = get_aggregate_size(series, client)
                total_size += series_size

    return total_size


def has_valid_file(item, client):
    """Check if an episode/movie has a valid file on disk"""
    if not client or item.get("Type") not in ["Movie", "Episode"]:
        return True  # Assume valid for non-media items

    detailed = client.get_item_details(item["Id"])
    if detailed and "MediaSources" in detailed and detailed["MediaSources"]:
        for source in detailed["MediaSources"]:
            # Check if it has a path and size
            if source.get("Path") and source.get("Size"):
                return True
    return False


def browse_with_loading(
    client, library_id=None, parent_item=None, series_item=None, sort_by_size=False
):
    """Browse library with smart loading feedback"""

    def check_cache_exists():
        """Check if data is likely cached"""
        if library_id is None:
            # Check if libraries are cached
            cached_libraries = client._get_cached("libraries")
            return cached_libraries is not None and len(cached_libraries) > 0
        else:
            # Check if items are cached using the cache mechanism
            if parent_item and parent_item.get("Type") == "Series":
                cache_key = f"items_{parent_item['Id']}_Season"
            elif parent_item and parent_item.get("Type") == "Season":
                cache_key = f"items_{parent_item['Id']}_Episode"
            else:
                cache_key = f"items_{library_id}_Movie,Series"
            cached_result = client._get_cached(cache_key)
            return cached_result is not None and len(cached_result) > 0


    # Check if we need to load cache first
    is_cached = check_cache_exists()
    print(f"Debug: Is cached = {is_cached}")

    if not is_cached:
        # Load data to populate cache, then continue
        if library_id is None:
            libraries = client.get_libraries()
        else:
            # Pre-load the items we'll need
            if parent_item and parent_item.get("Type") == "Series":
                client.get_items(parent_id=parent_item["Id"], item_type="Season")
            elif parent_item and parent_item.get("Type") == "Season":
                client.get_items(parent_id=parent_item["Id"], item_type="Episode")
            else:
                client.get_items(parent_id=library_id, item_type="Movie,Series")


    # Load the actual data
    try:
        if library_id is None:
            # Load libraries
            libraries = client.get_libraries()
            if not libraries:
                return

            # Filter libraries
            filtered_libraries = []
            for lib in libraries:
                name = lib.get("Name", "").lower()
                if name in ["movies", "films", "tv shows", "tv", "series"]:
                    filtered_libraries.append(lib)

            if not filtered_libraries:
                filtered_libraries = libraries

            items = filtered_libraries
            prompt = "Select Library"
        else:
            # Load items from library
            if parent_item and parent_item.get("Type") == "Series":
                items = client.get_items(
                    parent_id=parent_item["Id"], item_type="Season"
                )
            elif parent_item and parent_item.get("Type") == "Season":
                items = client.get_items(
                    parent_id=parent_item["Id"], item_type="Episode"
                )
            else:
                items = client.get_items(parent_id=library_id, item_type="Movie,Series")

            if not items:
                return

            prompt = "Select Media"


        # Show actual menu
        action, selected = show_rofi_menu(items, prompt, client, sort_by_size)

        # Handle the selection
        if action == "select" and selected:
            handle_selection(client, selected, library_id, parent_item, sort_by_size)
        elif action == "sort":
            browse_with_loading(
                client, library_id, parent_item, series_item, not sort_by_size
            )
        elif action == "refresh":
            client.cache = {}
            client._save_cache()
            browse_with_loading(
                client, library_id, parent_item, series_item, sort_by_size
            )
        elif action == "back":
            if parent_item:
                if parent_item.get("Type") == "Season" and series_item:
                    browse_with_loading(
                        client, library_id, series_item, None, sort_by_size
                    )
                elif parent_item.get("Type") == "Series":
                    browse_with_loading(client, library_id, None, None, sort_by_size)
            elif library_id:
                browse_with_loading(client, None, None, None, sort_by_size)

    except Exception as e:
        print(f"Error loading data: {e}")


def handle_selection(client, selected, library_id, parent_item, sort_by_size):
    """Handle menu selection"""
    item_type = selected.get("Type", "")

    if item_type in ["Movie", "Episode"]:
        # Cast the item to jellyfin-mpv-shim
        title = selected.get("Name", "")
        cast_to_mpv_shim(client, selected["Id"], title)
        return  # Exit after starting playback
    elif item_type == "Series":
        # Browse into series - show seasons
        browse_with_loading(client, library_id, selected, None, sort_by_size)
    elif item_type == "Season":
        # Browse into season - show episodes
        series_item = (
            parent_item if parent_item and parent_item.get("Type") == "Series" else None
        )
        browse_with_loading(client, library_id, selected, series_item, sort_by_size)
    elif "ItemId" in selected:
        # Library selected
        browse_with_loading(client, selected["ItemId"], sort_by_size=sort_by_size)


def show_rofi_menu(
    items, prompt="Select", client=None, sort_by_size=False, show_loading=False
):
    """Show rofi menu with items"""
    rofi_input = []
    item_map = {}
    items_with_size = []

    # First pass: filter out phantom episodes and get sizes
    for item in items:
        item_type = item.get("Type", "")

        # Skip phantom episodes without files
        if item_type in ["Movie", "Episode"]:
            if not has_valid_file(item, client):
                continue

        # Check if this is a library item
        if "CollectionType" in item:
            item_type = "Library"

        # Get appropriate size
        if item_type in ["Movie", "Episode"]:
            size = get_item_size(item, client)
        elif item_type in ["Series", "Season", "CollectionFolder"]:
            size = get_aggregate_size(item, client)
        elif item_type == "Library":
            # Calculate library size
            size = get_aggregate_size(item, client)
        else:
            size = None

        items_with_size.append((item, size))

    # Sort if requested
    if sort_by_size:
        items_with_size.sort(key=lambda x: x[1] if x[1] else 0, reverse=True)
    else:
        # Sort by name
        items_with_size.sort(key=lambda x: x[0].get("Name", ""))

    # Second pass: create menu entries
    for item, size in items_with_size:
        item_type = item.get("Type", "")
        # Check if this is a library (from VirtualFolders API)
        if "CollectionType" in item:
            item_type = "Library"
        name = item.get("Name", "Unknown")
        size_str = format_size(size) if size else ""

        # Format display string
        if item_type == "Series":
            # Need to fetch detailed info for series to get season count
            if client and "Id" in item:
                detailed = client.get_item_details(item["Id"])
                if detailed:
                    season_count = detailed.get("ChildCount", 0)
                else:
                    season_count = item.get("ChildCount", 0)
            else:
                season_count = item.get("ChildCount", 0)

            # Show size before season count for TV shows
            display = f"📺 {name}"
            if size_str:
                display += f" - {size_str}"
            if season_count > 0:
                display += f" ({season_count} season{'s' if season_count != 1 else ''})"
        elif item_type == "Season":
            # Get episode count for season
            if client and "Id" in item:
                detailed = client.get_item_details(item["Id"])
                if detailed:
                    episode_count = detailed.get("ChildCount", 0)
                else:
                    episode_count = item.get("ChildCount", 0)
            else:
                episode_count = item.get("ChildCount", 0)

            # Show size before episode count for seasons
            display = f"📂 {name}"
            if size_str:
                display += f" - {size_str}"
            if episode_count > 0:
                display += (
                    f" ({episode_count} episode{'s' if episode_count != 1 else ''})"
                )
        elif item_type == "Episode":
            season = item.get("ParentIndexNumber", "")
            episode = item.get("IndexNumber", "")
            display = f"🎬 S{season:02d}E{episode:02d}: {name}"
            if size_str:
                display += f" - {size_str}"
        elif item_type == "Movie":
            year = item.get("ProductionYear", "")
            year_str = f"({year})" if year else ""
            display = f"🎬 {name} {year_str}"
            if size_str:
                display += f" - {size_str}"
        elif item_type == "CollectionFolder":
            # Skip collections unless it's Movies or TV Shows
            if name.lower() in ["movies", "films"]:
                display = f"🎞️ Films"
                if size_str:
                    display += f" - {size_str}"
            elif name.lower() in ["tv shows", "tv", "series"]:
                display = f"📺 TV Shows"
                if size_str:
                    display += f" - {size_str}"
            else:
                continue  # Skip this item
        elif item_type == "Library":
            # Handle libraries from VirtualFolders API
            collection_type = item.get("CollectionType", "")
            if collection_type == "movies" or name.lower() in ["movies", "films"]:
                display = f"🎞️ Films"
                if size_str:
                    display += f" - {size_str}"
            elif collection_type == "tvshows" or name.lower() in [
                "tv shows",
                "tv",
                "series",
            ]:
                display = f"📺 TV Shows"
                if size_str:
                    display += f" - {size_str}"
            else:
                display = f"📁 {name}"
                if size_str:
                    display += f" - {size_str}"
        else:
            display = f"📄 {name}"
            if size_str:
                display += f" - {size_str}"

        rofi_input.append(display)
        item_map[display] = item

    # Don't add Back button - we'll use Alt+h instead

    # Prepare rofi command with keyboard shortcuts
    sort_toggle = (
        "Size ↓" if not sort_by_size else "Name"
    )  # Show what user can toggle TO

    # Only show delete option if not at library level
    is_library_level = (
        all(
            "CollectionType" in item or "LibraryOptions" in item
            for item, _ in items_with_size
        )
        if items_with_size
        else False
    )

    if is_library_level:
        mesg = f"Alt+s: Sort by {sort_toggle} | Alt+r: Refresh | Alt+h: Back"
    else:
        mesg = f"Alt+d: Delete | Alt+s: Sort by {sort_toggle} | Alt+r: Refresh | Alt+h: Back"

    rofi_cmd = [
        "rofi",
        "-dmenu",
        "-p",
        prompt,
        "-i",
        "-kb-custom-1",
        "Alt+d",
        "-kb-custom-2",
        "Alt+s",
        "-kb-custom-3",
        "Alt+h",
        "-kb-custom-4",
        "Alt+r",
        "-mesg",
        mesg,
        "-theme",
        "/home/rash/.config/rofi/current_theme_rofi_jellyfin.rasi",
    ]

    # Clear any loading notification before rofi starts
    subprocess.run(['dunstify', '-C', '12345'], capture_output=True)

    # Run rofi
    result = subprocess.run(
        rofi_cmd, input="\n".join(rofi_input), capture_output=True, text=True
    )

    if result.returncode == 0:
        # Normal selection
        selected = result.stdout.strip()
        return ("select", item_map.get(selected))
    elif result.returncode == 10:
        # Alt+d pressed (custom-1)
        selected = result.stdout.strip()
        return ("delete", item_map.get(selected))
    elif result.returncode == 11:
        # Alt+s pressed (custom-2) - toggle sort
        return ("sort", None)
    elif result.returncode == 12:
        # Alt+h pressed (custom-3) - go back
        return ("back", None)
    elif result.returncode == 13:
        # Alt+r pressed (custom-4) - refresh cache
        return ("refresh", None)
    else:
        # Cancelled
        return (None, None)


def cast_to_mpv_shim(client, item_id, title=""):
    """Cast media to jellyfin-mpv-shim using official API client"""

    # Initialize official Jellyfin client
    official_client = OfficialJellyfinClient()
    official_client.config.app(
        "rofi_jellyfin", "1.0.0", "rofi_script", "rofi_jellyfin_001"
    )
    official_client.config.data["auth.ssl"] = JELLYFIN_URL.startswith("https")

    # Authenticate with API key
    try:
        official_client.authenticate(
            {"Servers": [{"AccessToken": client.api_key, "address": JELLYFIN_URL}]},
            discover=False,
        )
    except Exception as e:
        print(f"Failed to authenticate with official client: {e}")
        subprocess.run(
            ["rofi", "-e", "Failed to authenticate with Jellyfin"], capture_output=True
        )
        return False

    # Find the mpv-shim session
    mpv_session = client.get_mpv_shim_session()

    if not mpv_session:
        # Print debugging info for all sessions to CLI
        debug_info = client.debug_sessions()
        print(
            f"jellyfin-mpv-shim not found. Make sure it's running and connected to Jellyfin.\n\n{debug_info}"
        )
        subprocess.run(
            ["rofi", "-e", "jellyfin-mpv-shim not found. Check terminal for details."],
            capture_output=True,
        )
        return False

    session_id = mpv_session.get("Id")
    if not session_id:
        print("Could not get session ID for jellyfin-mpv-shim.")
        subprocess.run(
            ["rofi", "-e", "Could not get session ID for jellyfin-mpv-shim."],
            capture_output=True,
        )
        return False

    # Use official client's remote method
    try:
        print(f"Sending remote command via official client")
        print(f"Session ID: {session_id}, Item ID: {item_id}")

        # Use the correct remote_play_media method
        response = official_client.jellyfin.remote_play_media(
            id=session_id,
            item_ids=[item_id],
            command="PlayNow"
        )

        print(f"remote command response: {response}")

        device_name = mpv_session.get("DeviceName", "jellyfin-mpv-shim")
        print(f'Successfully sent remote command for "{title}" to {device_name}')
        return True

    except Exception as e:
        # Print debugging info to CLI
        device_name = mpv_session.get("DeviceName", "jellyfin-mpv-shim")
        capabilities = mpv_session.get("Capabilities", {})
        print(f"Failed to send remote command: {e}")
        print(f"Device: {device_name}")
        print(f"Session ID: {session_id}")
        print(f"Item ID: {item_id}")
        print(f"Capabilities: {capabilities}")
        subprocess.run(
            ["rofi", "-e", "Failed to start playback. Check terminal for details."],
            capture_output=True,
        )
        return False


# Note: Subtitle handling is now done by jellyfin-mpv-shim automatically


def browse_library(
    client, library_id=None, parent_item=None, series_item=None, sort_by_size=False
):
    """Browse Jellyfin library"""
    if library_id is None:
        # Show libraries - filter to only Movies and TV Shows
        libraries = client.get_libraries()
        if not libraries:
            print("No libraries found")
            return

        # Filter to only Movies and TV Shows libraries
        filtered_libraries = []
        for lib in libraries:
            name = lib.get("Name", "").lower()
            if name in ["movies", "films", "tv shows", "tv", "series"]:
                filtered_libraries.append(lib)

        if not filtered_libraries:
            # Fall back to all libraries if no matching ones found
            filtered_libraries = libraries

        action, selected = show_rofi_menu(
            filtered_libraries, "Select Library", client, sort_by_size
        )
        if action == "select" and selected:
            browse_library(client, selected["ItemId"], sort_by_size=sort_by_size)
        elif action == "sort":
            # Toggle sort and re-show
            browse_library(
                client, library_id, parent_item, series_item, not sort_by_size
            )
        elif action == "refresh":
            # Clear cache and refresh
            client.cache = {}
            client._save_cache()
            browse_library(client, library_id, parent_item, series_item, sort_by_size)
        elif action == "back":
            # Can't go back from library selection
            pass
    else:
        # Show items in library or parent
        if parent_item and parent_item.get("Type") == "Series":
            # Show seasons
            items = client.get_items(parent_id=parent_item["Id"], item_type="Season")
        elif parent_item and parent_item.get("Type") == "Season":
            # Show episodes
            items = client.get_items(parent_id=parent_item["Id"], item_type="Episode")
        else:
            # Show movies or series in the library
            items = client.get_items(parent_id=library_id, item_type="Movie,Series")

        if not items:
            print("No items found")
            return

        prompt = parent_item["Name"] if parent_item else "Select Item"
        action, selected = show_rofi_menu(items, prompt, client, sort_by_size)

        if action == "sort":
            # Toggle sort and re-show
            browse_library(
                client, library_id, parent_item, series_item, not sort_by_size
            )
            return
        elif action == "refresh":
            # Clear cache and refresh
            client.cache = {}
            client._save_cache()
            browse_library(client, library_id, parent_item, series_item, sort_by_size)
            return
        elif action == "back":
            # Handle back navigation
            if parent_item:
                # Go back based on parent type
                if parent_item.get("Type") == "Season":
                    # Go back to series (show seasons again)
                    if series_item:
                        browse_library(
                            client, library_id, series_item, None, sort_by_size
                        )
                    else:
                        # Try to find the series
                        series_id = parent_item.get("SeriesId")
                        if series_id:
                            detail = client.get_item_details(series_id)
                            if detail:
                                browse_library(
                                    client, library_id, detail, None, sort_by_size
                                )
                            else:
                                browse_library(
                                    client, library_id, None, None, sort_by_size
                                )
                        else:
                            browse_library(client, library_id, None, None, sort_by_size)
                elif parent_item.get("Type") == "Series":
                    # Go back to library
                    browse_library(client, library_id, None, None, sort_by_size)
            else:
                # Go back to library selection
                browse_library(client, None, None, None, sort_by_size)
            return
        elif action == "select":
            if selected:
                item_type = selected.get("Type", "")

                if item_type in ["Movie", "Episode"]:
                    # Cast the item to jellyfin-mpv-shim
                    title = selected.get("Name", "")
                    cast_to_mpv_shim(client, selected["Id"], title)
                    return  # Exit after starting playback
                elif item_type == "Series":
                    # Browse into series - show seasons
                    browse_library(client, library_id, selected, None, sort_by_size)
                elif item_type == "Season":
                    # Browse into season - show episodes
                    # Pass the series as the third parameter for proper back navigation
                    browse_library(
                        client,
                        library_id,
                        selected,
                        (
                            parent_item
                            if parent_item and parent_item.get("Type") == "Series"
                            else None
                        ),
                        sort_by_size,
                    )
                elif item_type == "CollectionFolder":
                    # This is a library
                    browse_library(client, selected["ItemId"], None, None, sort_by_size)

        elif action == "delete" and selected:
            # Confirm deletion with a safer default
            name = selected.get("Name", "this item")
            item_type = selected.get("Type", "item")

            # Show more detail in confirmation
            if item_type == "Episode":
                season = selected.get("ParentIndexNumber", "")
                episode = selected.get("IndexNumber", "")
                confirm_prompt = f"Delete S{season:02d}E{episode:02d}: {name}?"
            else:
                confirm_prompt = f"Delete {item_type.lower()}: {name}?"

            confirm_result = subprocess.run(
                [
                    "rofi",
                    "-dmenu",
                    "-p",
                    confirm_prompt,
                    "-theme",
                    "/home/rash/.config/rofi/current_theme_rofi_jellyfin.rasi",
                    "-mesg",
                    "This will permanently delete the file from Jellyfin and disk",
                ],
                input="No (Cancel)\nYes (Delete)",
                capture_output=True,
                text=True,
            )

            if confirm_result.returncode == 0 and "Yes" in confirm_result.stdout:
                if client.delete_item(selected["Id"]):
                    # Show success and refresh
                    subprocess.run(
                        ["rofi", "-e", f"'{name}' deleted successfully"],
                        capture_output=True,
                    )
                else:
                    subprocess.run(
                        ["rofi", "-e", f"Failed to delete '{name}'"],
                        capture_output=True,
                    )

            # Always go back to the current view after delete confirmation (Yes or No)
            browse_library(client, library_id, parent_item, series_item, sort_by_size)


def main():
    # Initialize client with API key from env file
    client = JellyfinClient(JELLYFIN_URL, API_KEY)

    # Test connection with lightweight endpoint
    try:
        response = requests.get(f"{JELLYFIN_URL}/Users", headers={"X-Emby-Token": API_KEY})
        if response.status_code != 200:
            subprocess.run(
                [
                    "rofi",
                    "-e",
                    "Connection failed. Check your Jellyfin URL or API key.",
                ],
                capture_output=True,
            )
            sys.exit(1)
    except Exception as e:
        subprocess.run(
            ["rofi", "-e", f"Failed to connect to Jellyfin: {str(e)}"],
            capture_output=True,
        )
        sys.exit(1)

    # Check if we need to show initial loading notification
    def check_cache_exists():
        """Check if libraries are cached"""
        cached_libraries = client._get_cached("libraries")
        return cached_libraries is not None and len(cached_libraries) > 0

    is_cached = check_cache_exists()

    if not is_cached:
        # Show persistent notification for initial load only
        subprocess.run([
            'dunstify',
            'Jellyfin',
            'Loading library cache...',
            '-t', '0',  # Persistent
            '-r', '12345'  # Replaceable ID
        ], capture_output=True)

    # Start browsing with loading feedback
    browse_with_loading(client)


if __name__ == "__main__":
    main()
