#!/usr/bin/env python3

import sys
import json
import subprocess
import requests
from urllib.parse import urlencode
import os
from pathlib import Path
import time
import threading
import pickle

JELLYFIN_URL = "http://10.20.10.92:8096"
CACHE_DIR = Path.home() / ".cache" / "rofi_jellyfin"
CACHE_EXPIRY = 300  # 5 minutes

# Load API key from env file
API_KEY = ""
env_file = Path.home() / ".config/scripts/_secrets/jellyfin.env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, _, value = line.partition('=')
                if key.strip() == 'JELLYFIN_API_KEY':
                    API_KEY = value.strip().strip('"').strip("'")
                    break

# Fallback to environment variable if not in file
if not API_KEY:
    API_KEY = os.environ.get("JELLYFIN_API_KEY", "")

class JellyfinClient:
    def __init__(self, base_url, api_key=""):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        self.user_id = None
        self.cache = {}
        
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache if available
        self._load_cache()
        
        if api_key:
            self.headers['X-Emby-Token'] = api_key
            # Get user ID
            self._get_user_id()
    
    def _load_cache(self):
        """Load cache from disk"""
        cache_file = CACHE_DIR / "cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        cache_file = CACHE_DIR / "cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
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
                    self.user_id = users[0]['Id']
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
        
        params = {
            'Recursive': 'true',
            'SortBy': 'SortName',
            'SortOrder': 'Ascending'
        }
        
        if parent_id:
            params['ParentId'] = parent_id
        
        if item_type:
            params['IncludeItemTypes'] = item_type
        
        # Use user-specific endpoint if we have a user ID
        if self.user_id:
            url = f"{self.base_url}/Users/{self.user_id}/Items"
        else:
            url = f"{self.base_url}/Items"
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            items = response.json().get('Items', [])
            self._set_cached(cache_key, items)
            return items
        return []
    
    def get_libraries(self):
        """Get all libraries"""
        url = f"{self.base_url}/Library/VirtualFolders"
        if self.api_key:
            response = requests.get(url, headers=self.headers)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
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
    
    def get_playback_url(self, item_id):
        """Get direct playback URL for an item"""
        if self.api_key:
            return f"{self.base_url}/Videos/{item_id}/stream?static=true&api_key={self.api_key}"
        return f"{self.base_url}/Videos/{item_id}/stream?static=true"

    def get_subtitle_streams(self, item_id):
        """Get available subtitle streams for an item"""
        detailed = self.get_item_details(item_id)
        if detailed and 'MediaSources' in detailed and detailed['MediaSources']:
            for source in detailed['MediaSources']:
                if 'MediaStreams' in source:
                    subtitles = [stream for stream in source['MediaStreams']
                               if stream.get('Type') == 'Subtitle']
                    return subtitles, source.get('Id')
        return [], None

    def get_subtitle_url(self, item_id, media_source_id, subtitle_index, format='vtt'):
        """Get subtitle stream URL"""
        if self.api_key:
            return f"{self.base_url}/Videos/{item_id}/{media_source_id}/Subtitles/{subtitle_index}/Stream.{format}?api_key={self.api_key}"
        return f"{self.base_url}/Videos/{item_id}/{media_source_id}/Subtitles/{subtitle_index}/Stream.{format}"

def format_size(size_bytes):
    """Convert bytes to human readable format"""
    if not size_bytes:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def get_item_size(item, client=None):
    """Get size from item, fetching detailed info if needed"""
    # For movies and episodes, get detailed info with MediaSources
    if client and item.get('Type') in ['Movie', 'Episode'] and 'Id' in item:
        detailed = client.get_item_details(item['Id'])
        if detailed and 'MediaSources' in detailed and detailed['MediaSources']:
            for source in detailed['MediaSources']:
                if 'Size' in source and source['Size']:
                    return source['Size']
    
    # Fallback to basic size field
    if 'Size' in item and item['Size']:
        return item['Size']
    
    return None

def get_aggregate_size(item, client):
    """Calculate total size for series/seasons/libraries"""
    item_type = item.get('Type', '')
    # Check if this is a library
    if 'CollectionType' in item:
        item_type = 'Library'
    total_size = 0
    
    if item_type == 'Series' and client:
        # Get all episodes in the series
        episodes = client.get_items(parent_id=item['Id'], item_type='Episode')
        for ep in episodes:
            size = get_item_size(ep, client)
            if size:
                total_size += size
    elif item_type == 'Season' and client:
        # Get all episodes in the season
        episodes = client.get_items(parent_id=item['Id'], item_type='Episode')
        for ep in episodes:
            size = get_item_size(ep, client)
            if size:
                total_size += size
    elif item_type == 'CollectionFolder' and client:
        # Get total for library (movies or all series)
        lib_name = item.get('Name', '').lower()
        if lib_name in ['movies', 'films']:
            movies = client.get_items(parent_id=item['ItemId'], item_type='Movie')
            for movie in movies:
                size = get_item_size(movie, client)
                if size:
                    total_size += size
        elif lib_name in ['tv shows', 'tv', 'series']:
            series_list = client.get_items(parent_id=item['ItemId'], item_type='Series')
            for series in series_list:
                series_size = get_aggregate_size(series, client)
                total_size += series_size
    elif item_type == 'Library' and client:
        # Handle libraries from VirtualFolders API
        collection_type = item.get('CollectionType', '')
        library_id = item.get('ItemId')
        if collection_type == 'movies':
            movies = client.get_items(parent_id=library_id, item_type='Movie')
            for movie in movies:
                size = get_item_size(movie, client)
                if size:
                    total_size += size
        elif collection_type == 'tvshows':
            series_list = client.get_items(parent_id=library_id, item_type='Series')
            for series in series_list:
                series_size = get_aggregate_size(series, client)
                total_size += series_size
    
    return total_size

def has_valid_file(item, client):
    """Check if an episode/movie has a valid file on disk"""
    if not client or item.get('Type') not in ['Movie', 'Episode']:
        return True  # Assume valid for non-media items
    
    detailed = client.get_item_details(item['Id'])
    if detailed and 'MediaSources' in detailed and detailed['MediaSources']:
        for source in detailed['MediaSources']:
            # Check if it has a path and size
            if source.get('Path') and source.get('Size'):
                return True
    return False

def browse_with_loading(client, library_id=None, parent_item=None, series_item=None, sort_by_size=False):
    """Browse library with smart loading feedback"""

    def check_cache_exists():
        """Check if data is likely cached"""
        if library_id is None:
            # Libraries are usually cached
            return client._get_cached('libraries') is not None
        else:
            # Check if items are cached
            if parent_item and parent_item.get('Type') == 'Series':
                cache_key = f"items_{parent_item['Id']}_Season"
            elif parent_item and parent_item.get('Type') == 'Season':
                cache_key = f"items_{parent_item['Id']}_Episode"
            else:
                cache_key = f"items_{library_id}_Movie,Series"
            return client._get_cached(cache_key) is not None

    def show_loading():
        loading_items = ["🔄 Loading media library...", "⏳ Please wait...", "", "Press Escape to cancel"]
        rofi_input = "\n".join(loading_items)

        rofi_cmd = [
            'rofi', '-dmenu', '-p', 'Loading...',
            '-i', '-theme-str', 'listview { lines: 4; }',
            '-no-custom'
        ]

        try:
            subprocess.run(rofi_cmd, input=rofi_input, text=True, capture_output=True)
        except Exception:
            pass

    # Check if we need loading screen
    show_loading_screen = not check_cache_exists()
    loading_thread = None

    if show_loading_screen:
        # Start loading rofi in background
        loading_thread = threading.Thread(target=show_loading, daemon=True)
        loading_thread.start()
        # Give it a moment to appear
        time.sleep(0.1)

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
                name = lib.get('Name', '').lower()
                if name in ['movies', 'films', 'tv shows', 'tv', 'series']:
                    filtered_libraries.append(lib)

            if not filtered_libraries:
                filtered_libraries = libraries

            items = filtered_libraries
            prompt = "Select Library"
        else:
            # Load items from library
            if parent_item and parent_item.get('Type') == 'Series':
                items = client.get_items(parent_id=parent_item['Id'], item_type='Season')
            elif parent_item and parent_item.get('Type') == 'Season':
                items = client.get_items(parent_id=parent_item['Id'], item_type='Episode')
            else:
                items = client.get_items(parent_id=library_id, item_type='Movie,Series')

            if not items:
                return

            prompt = "Select Media"

        # Kill any loading rofi processes if we showed them
        if show_loading_screen:
            try:
                subprocess.run(['pkill', '-f', 'rofi.*Loading'], capture_output=True)
            except:
                pass

        # Show actual menu
        action, selected = show_rofi_menu(items, prompt, client, sort_by_size)

        # Handle the selection
        if action == 'select' and selected:
            handle_selection(client, selected, library_id, parent_item, sort_by_size)
        elif action == 'sort':
            browse_with_loading(client, library_id, parent_item, series_item, not sort_by_size)
        elif action == 'refresh':
            client.cache = {}
            client._save_cache()
            browse_with_loading(client, library_id, parent_item, series_item, sort_by_size)
        elif action == 'back':
            if parent_item:
                if parent_item.get('Type') == 'Season' and series_item:
                    browse_with_loading(client, library_id, series_item, None, sort_by_size)
                elif parent_item.get('Type') == 'Series':
                    browse_with_loading(client, library_id, None, None, sort_by_size)
            elif library_id:
                browse_with_loading(client, None, None, None, sort_by_size)

    except Exception as e:
        # Kill loading processes and show error
        if show_loading_screen:
            try:
                subprocess.run(['pkill', '-f', 'rofi.*Loading'], capture_output=True)
            except:
                pass
        print(f"Error loading data: {e}")

def handle_selection(client, selected, library_id, parent_item, sort_by_size):
    """Handle menu selection"""
    item_type = selected.get('Type', '')

    if item_type in ['Movie', 'Episode']:
        # Play the item with subtitles
        url = client.get_playback_url(selected['Id'])
        title = selected.get('Name', '')
        subtitle_urls = get_preferred_subtitles(client, selected['Id'])
        play_with_mpv(url, title, subtitle_urls)
        return  # Exit after starting playback
    elif item_type == 'Series':
        # Browse into series - show seasons
        browse_with_loading(client, library_id, selected, None, sort_by_size)
    elif item_type == 'Season':
        # Browse into season - show episodes
        series_item = parent_item if parent_item and parent_item.get('Type') == 'Series' else None
        browse_with_loading(client, library_id, selected, series_item, sort_by_size)
    elif 'ItemId' in selected:
        # Library selected
        browse_with_loading(client, selected['ItemId'], sort_by_size=sort_by_size)

def show_rofi_menu(items, prompt="Select", client=None, sort_by_size=False, show_loading=False):
    """Show rofi menu with items"""
    rofi_input = []
    item_map = {}
    items_with_size = []
    
    # First pass: filter out phantom episodes and get sizes
    for item in items:
        item_type = item.get('Type', '')
        
        # Skip phantom episodes without files
        if item_type in ['Movie', 'Episode']:
            if not has_valid_file(item, client):
                continue
        
        # Check if this is a library item
        if 'CollectionType' in item:
            item_type = 'Library'
        
        # Get appropriate size
        if item_type in ['Movie', 'Episode']:
            size = get_item_size(item, client)
        elif item_type in ['Series', 'Season', 'CollectionFolder']:
            size = get_aggregate_size(item, client)
        elif item_type == 'Library':
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
        items_with_size.sort(key=lambda x: x[0].get('Name', ''))
    
    # Second pass: create menu entries
    for item, size in items_with_size:
        item_type = item.get('Type', '')
        # Check if this is a library (from VirtualFolders API)
        if 'CollectionType' in item:
            item_type = 'Library'
        name = item.get('Name', 'Unknown')
        size_str = format_size(size) if size else ""
        
        # Format display string
        if item_type == 'Series':
            # Need to fetch detailed info for series to get season count
            if client and 'Id' in item:
                detailed = client.get_item_details(item['Id'])
                if detailed:
                    season_count = detailed.get('ChildCount', 0)
                else:
                    season_count = item.get('ChildCount', 0)
            else:
                season_count = item.get('ChildCount', 0)
            
            # Show size before season count for TV shows
            display = f"📺 {name}"
            if size_str:
                display += f" - {size_str}"
            if season_count > 0:
                display += f" ({season_count} season{'s' if season_count != 1 else ''})"
        elif item_type == 'Season':
            # Get episode count for season
            if client and 'Id' in item:
                detailed = client.get_item_details(item['Id'])
                if detailed:
                    episode_count = detailed.get('ChildCount', 0)
                else:
                    episode_count = item.get('ChildCount', 0)
            else:
                episode_count = item.get('ChildCount', 0)
            
            # Show size before episode count for seasons
            display = f"📂 {name}"
            if size_str:
                display += f" - {size_str}"
            if episode_count > 0:
                display += f" ({episode_count} episode{'s' if episode_count != 1 else ''})"
        elif item_type == 'Episode':
            season = item.get('ParentIndexNumber', '')
            episode = item.get('IndexNumber', '')
            display = f"🎬 S{season:02d}E{episode:02d}: {name}"
            if size_str:
                display += f" - {size_str}"
        elif item_type == 'Movie':
            year = item.get('ProductionYear', '')
            year_str = f"({year})" if year else ""
            display = f"🎬 {name} {year_str}"
            if size_str:
                display += f" - {size_str}"
        elif item_type == 'CollectionFolder':
            # Skip collections unless it's Movies or TV Shows
            if name.lower() in ['movies', 'films']:
                display = f"🎞️ Films"
                if size_str:
                    display += f" - {size_str}"
            elif name.lower() in ['tv shows', 'tv', 'series']:
                display = f"📺 TV Shows"
                if size_str:
                    display += f" - {size_str}"
            else:
                continue  # Skip this item
        elif item_type == 'Library':
            # Handle libraries from VirtualFolders API
            collection_type = item.get('CollectionType', '')
            if collection_type == 'movies' or name.lower() in ['movies', 'films']:
                display = f"🎞️ Films"
                if size_str:
                    display += f" - {size_str}"
            elif collection_type == 'tvshows' or name.lower() in ['tv shows', 'tv', 'series']:
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
    sort_toggle = "Size ↓" if not sort_by_size else "Name"  # Show what user can toggle TO
    
    # Only show delete option if not at library level
    is_library_level = all('CollectionType' in item or 'LibraryOptions' in item 
                           for item, _ in items_with_size) if items_with_size else False
    
    if is_library_level:
        mesg = f"Alt+s: Sort by {sort_toggle} | Alt+r: Refresh | Alt+h: Back"
    else:
        mesg = f"Alt+d: Delete | Alt+s: Sort by {sort_toggle} | Alt+r: Refresh | Alt+h: Back"
    
    rofi_cmd = [
        'rofi', '-dmenu',
        '-p', prompt,
        '-i',
        '-kb-custom-1', 'Alt+d',
        '-kb-custom-2', 'Alt+s', 
        '-kb-custom-3', 'Alt+h',
        '-kb-custom-4', 'Alt+r',
        '-mesg', mesg,
        '-theme', '/home/rash/.config/rofi/current_theme_rofi_jellyfin.rasi'
    ]
    
    # Run rofi
    result = subprocess.run(
        rofi_cmd,
        input='\n'.join(rofi_input),
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Normal selection
        selected = result.stdout.strip()
        return ('select', item_map.get(selected))
    elif result.returncode == 10:
        # Alt+d pressed (custom-1)
        selected = result.stdout.strip()
        return ('delete', item_map.get(selected))
    elif result.returncode == 11:
        # Alt+s pressed (custom-2) - toggle sort
        return ('sort', None)
    elif result.returncode == 12:
        # Alt+h pressed (custom-3) - go back
        return ('back', None)
    elif result.returncode == 13:
        # Alt+r pressed (custom-4) - refresh cache
        return ('refresh', None)
    else:
        # Cancelled
        return (None, None)

def play_with_mpv(url, title="", subtitle_urls=None):
    """Play media with mpv including subtitles"""
    mpv_cmd = ['mpv']
    if title:
        mpv_cmd.append(f'--title={title}')

    # Add subtitle files
    if subtitle_urls:
        for sub_url in subtitle_urls:
            mpv_cmd.append(f'--sub-file={sub_url}')

    # Set custom window class for Wayland/Hyprland targeting
    mpv_cmd.append('--wayland-app-id=rofi_jellyfin')
    mpv_cmd.append(url)

    subprocess.run(mpv_cmd)

def get_preferred_subtitles(client, item_id):
    """Get preferred subtitle URLs for an item"""
    subtitles, media_source_id = client.get_subtitle_streams(item_id)
    if not subtitles or not media_source_id:
        return []

    # Find the best English subtitle
    preferred_langs = ['eng', 'en', 'english']
    selected_subtitle = None

    # First, try to find English subtitles
    for subtitle in subtitles:
        sub_lang = subtitle.get('Language', '').lower()
        display_title = subtitle.get('DisplayTitle', '').lower()
        codec = subtitle.get('Codec', '').lower()

        # Skip image-based subtitles (PGS, VOBSUB, etc.)
        if codec in ['dvd_subtitle', 'hdmv_pgs_subtitle', 'vobsub']:
            continue

        # Check if this is an English subtitle
        for lang in preferred_langs:
            if lang in sub_lang or lang in display_title:
                selected_subtitle = subtitle
                break
        if selected_subtitle:
            break

    # If no English subtitles found, get first text-based subtitle
    if not selected_subtitle:
        for subtitle in subtitles:
            codec = subtitle.get('Codec', '').lower()
            if codec not in ['dvd_subtitle', 'hdmv_pgs_subtitle', 'vobsub']:
                selected_subtitle = subtitle
                break

    if selected_subtitle:
        index = selected_subtitle.get('Index')
        if index is not None:
            # Use SRT format as it's more reliable than VTT
            sub_url = client.get_subtitle_url(item_id, media_source_id, index, 'srt')
            return [sub_url]

    return []

def browse_library(client, library_id=None, parent_item=None, series_item=None, sort_by_size=False):
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
            name = lib.get('Name', '').lower()
            if name in ['movies', 'films', 'tv shows', 'tv', 'series']:
                filtered_libraries.append(lib)
        
        if not filtered_libraries:
            # Fall back to all libraries if no matching ones found
            filtered_libraries = libraries
        
        action, selected = show_rofi_menu(filtered_libraries, "Select Library", client, sort_by_size)
        if action == 'select' and selected:
            browse_library(client, selected['ItemId'], sort_by_size=sort_by_size)
        elif action == 'sort':
            # Toggle sort and re-show
            browse_library(client, library_id, parent_item, series_item, not sort_by_size)
        elif action == 'refresh':
            # Clear cache and refresh
            client.cache = {}
            client._save_cache()
            browse_library(client, library_id, parent_item, series_item, sort_by_size)
        elif action == 'back':
            # Can't go back from library selection
            pass
    else:
        # Show items in library or parent
        if parent_item and parent_item.get('Type') == 'Series':
            # Show seasons
            items = client.get_items(parent_id=parent_item['Id'], item_type='Season')
        elif parent_item and parent_item.get('Type') == 'Season':
            # Show episodes
            items = client.get_items(parent_id=parent_item['Id'], item_type='Episode')
        else:
            # Show movies or series in the library
            items = client.get_items(parent_id=library_id, item_type='Movie,Series')
        
        if not items:
            print("No items found")
            return
        
        prompt = parent_item['Name'] if parent_item else "Select Item"
        action, selected = show_rofi_menu(items, prompt, client, sort_by_size)
        
        if action == 'sort':
            # Toggle sort and re-show
            browse_library(client, library_id, parent_item, series_item, not sort_by_size)
            return
        elif action == 'refresh':
            # Clear cache and refresh
            client.cache = {}
            client._save_cache()
            browse_library(client, library_id, parent_item, series_item, sort_by_size)
            return
        elif action == 'back':
            # Handle back navigation
            if parent_item:
                # Go back based on parent type
                if parent_item.get('Type') == 'Season':
                    # Go back to series (show seasons again)
                    if series_item:
                        browse_library(client, library_id, series_item, None, sort_by_size)
                    else:
                        # Try to find the series
                        series_id = parent_item.get('SeriesId')
                        if series_id:
                            detail = client.get_item_details(series_id)
                            if detail:
                                browse_library(client, library_id, detail, None, sort_by_size)
                            else:
                                browse_library(client, library_id, None, None, sort_by_size)
                        else:
                            browse_library(client, library_id, None, None, sort_by_size)
                elif parent_item.get('Type') == 'Series':
                    # Go back to library
                    browse_library(client, library_id, None, None, sort_by_size)
            else:
                # Go back to library selection
                browse_library(client, None, None, None, sort_by_size)
            return
        elif action == 'select':
            if selected:
                item_type = selected.get('Type', '')
                
                if item_type in ['Movie', 'Episode']:
                    # Play the item with subtitles
                    url = client.get_playback_url(selected['Id'])
                    title = selected.get('Name', '')
                    subtitle_urls = get_preferred_subtitles(client, selected['Id'])
                    play_with_mpv(url, title, subtitle_urls)
                    return  # Exit after starting playback
                elif item_type == 'Series':
                    # Browse into series - show seasons
                    browse_library(client, library_id, selected, None, sort_by_size)
                elif item_type == 'Season':
                    # Browse into season - show episodes
                    # Pass the series as the third parameter for proper back navigation
                    browse_library(client, library_id, selected, parent_item if parent_item and parent_item.get('Type') == 'Series' else None, sort_by_size)
                elif item_type == 'CollectionFolder':
                    # This is a library
                    browse_library(client, selected['ItemId'], None, None, sort_by_size)
        
        elif action == 'delete' and selected:
            # Confirm deletion with a safer default
            name = selected.get('Name', 'this item')
            item_type = selected.get('Type', 'item')
            
            # Show more detail in confirmation
            if item_type == 'Episode':
                season = selected.get('ParentIndexNumber', '')
                episode = selected.get('IndexNumber', '')
                confirm_prompt = f"Delete S{season:02d}E{episode:02d}: {name}?"
            else:
                confirm_prompt = f"Delete {item_type.lower()}: {name}?"
            
            confirm_result = subprocess.run(
                ['rofi', '-dmenu', '-p', confirm_prompt, 
                 '-theme', '/home/rash/.config/rofi/current_theme_rofi_jellyfin.rasi',
                 '-mesg', 'This will permanently delete the file from Jellyfin and disk'],
                input="No (Cancel)\nYes (Delete)",
                capture_output=True,
                text=True
            )
            
            if confirm_result.returncode == 0 and "Yes" in confirm_result.stdout:
                if client.delete_item(selected['Id']):
                    # Show success and refresh
                    subprocess.run(
                        ['rofi', '-e', f"'{name}' deleted successfully"],
                        capture_output=True
                    )
                else:
                    subprocess.run(
                        ['rofi', '-e', f"Failed to delete '{name}'"],
                        capture_output=True
                    )
            
            # Always go back to the current view after delete confirmation (Yes or No)
            browse_library(client, library_id, parent_item, series_item, sort_by_size)

def main():
    # Initialize client with API key from env file
    client = JellyfinClient(JELLYFIN_URL, API_KEY)
    
    # Test connection
    try:
        libraries = client.get_libraries()
        if not libraries:
            subprocess.run(
                ['rofi', '-e', 'No libraries found. Check your Jellyfin connection or API key.'],
                capture_output=True
            )
            sys.exit(1)
    except Exception as e:
        subprocess.run(
            ['rofi', '-e', f"Failed to connect to Jellyfin: {str(e)}"],
            capture_output=True
        )
        sys.exit(1)
    
    # Start browsing with loading feedback
    browse_with_loading(client)

if __name__ == "__main__":
    main()