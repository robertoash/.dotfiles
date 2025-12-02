#!/usr/bin/env python3
"""
Xtream API Proxy Server
Filters and proxies Xtream API calls with your custom filter rules
Serves 'full' filter on port 8080 and 'mini' filter on port 7070
"""

import json
import logging
import os
import re
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify, Response, redirect
import requests

# Import configuration
from config import CATEGORY_PATTERNS, EXCLUDE_STREAM_PREFIXES, CACHE_TIMEOUT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Load config from environment
UPSTREAM_SERVER = os.getenv('UPSTREAM_SERVER', '')
UPSTREAM_USERNAME = os.getenv('UPSTREAM_USERNAME', '')
UPSTREAM_PASSWORD = os.getenv('UPSTREAM_PASSWORD', '')
ALT_USERNAME = os.getenv('ALT_USERNAME', '')
ALT_PASSWORD = os.getenv('ALT_PASSWORD', '')

# Multi-user proxy authentication - dynamically load from environment
PROXY_USERS = {}

# Load proxy users from environment variables
user_count = 1
while True:
    username = os.getenv(f'PROXY_USER{user_count}_USERNAME')
    password = os.getenv(f'PROXY_USER{user_count}_PASSWORD')
    stream_user = os.getenv(f'PROXY_USER{user_count}_STREAM_USER')
    stream_pass = os.getenv(f'PROXY_USER{user_count}_STREAM_PASS')

    if not all([username, password, stream_user, stream_pass]):
        break

    PROXY_USERS[username] = {
        "password": password,
        "stream_user": stream_user,
        "stream_pass": stream_pass
    }
    user_count += 1

if not PROXY_USERS:
    raise RuntimeError("No proxy users configured")

if not all([UPSTREAM_SERVER, UPSTREAM_USERNAME, UPSTREAM_PASSWORD]):
    raise RuntimeError("Missing required environment variables")

def get_user_credentials(username, password):
    """Get user credentials and return stream credentials if valid."""
    user_config = PROXY_USERS.get(username)
    if user_config and user_config["password"] == password:
        return user_config["stream_user"], user_config["stream_pass"]
    return None, None

def validate_proxy_credentials(username, password):
    """Validate proxy user credentials."""
    user_config = PROXY_USERS.get(username)
    return user_config and user_config["password"] == password

# Filter rules from your original script
NAME_TWEAKS = {
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

FILTER_RULES = {
    "exclude": {
        "name_patterns": [r"^\s*#+\s*.*?\s*#+\s*$"],
        "group_contains": ["religious", "religion", "biblical", "christian"],
    },
    "include": {
        "group_targets": {
            "full": {
                "tv": [
                    "4K UHD", "sweden", "se|", "nordic", "ppv", "uk|", "eu|",
                    "es|", "it|", "us|", "au|", "australia", "la| el salvador",
                ],
                "movies": ["|se|", "|en|", "|es|", "top"],
                "series": ["|multi|", "|en|", "|es|", "|se|", "|la|"],
                "spicy": ["adults"],
            },
            "mini": {
                "tv": ["sweden", "la| el salvador", "uk|", "us|"],
                "spicy": ["adults"],
            },
        },
        "tvg_prefixes": ["se:", "it:", "se-", "swe|"],
        "tv_group_prefixes": ["la|", "us|", "uk|", "eu|", "es|", "it|", "au|", "se|", "nordic|"],
    },
}


def apply_tweaks(name):
    """Apply name tweaks."""
    name = name.upper().strip()
    for pattern, replacement in NAME_TWEAKS.items():
        if re.search(pattern, name):
            name = re.sub(pattern, replacement, name)
            break
    return name

def looks_like_series_by_name(display_name):
    """Check if name looks like a series."""
    return bool(re.search(r"S\d{1,2}\s+E\d{1,3}", display_name, re.IGNORECASE))

def guess_category(group, tvg_id=None, tvg_name=None, display_name=None):
    """Guess category based on group and other metadata."""
    group = group.lower() if group else ""
    tvg_id = str(tvg_id).lower() if tvg_id else ""
    tvg_name = tvg_name.lower() if tvg_name else ""
    display_name = display_name.lower() if display_name else ""

    if not tvg_id:
        if ("ppv" in group or
            any(tvg_name.startswith(prefix) for prefix in FILTER_RULES["include"]["tvg_prefixes"]) or
            any(group.startswith(prefix) for prefix in FILTER_RULES["include"]["tv_group_prefixes"])):
            category = "tv"
        elif "adults" in group:
            category = "spicy"
        elif ("series" in group or looks_like_series_by_name(group) or looks_like_series_by_name(display_name)):
            category = "series"
        else:
            category = "movies"
    elif "adults" in group:
        category = "spicy"
    else:
        category = "tv"
    return category

def should_include(name, category, group, filter_type="full"):
    """Check if a channel should be included based on filter rules."""
    name = name.strip().lower()
    group = group.strip().lower()
    category = category.strip().lower()

    # Check exclusions
    for pattern in FILTER_RULES["exclude"]["name_patterns"]:
        if re.match(pattern, name, re.IGNORECASE):
            return False

    if any(bad in group for bad in FILTER_RULES["exclude"]["group_contains"]):
        return False

    if filter_type == "mini" and category == "series":
        return False

    # Check inclusions
    targets = FILTER_RULES["include"]["group_targets"].get(filter_type, {})
    accepted_groups = targets.get(category, [])

    return any(target in group for target in accepted_groups)

def make_upstream_call(action, extra_params=None):
    """Make API call to upstream Xtream server."""
    url = f"{UPSTREAM_SERVER}/player_api.php"
    params = {
        "username": UPSTREAM_USERNAME,
        "password": UPSTREAM_PASSWORD,
        "action": action
    }
    if extra_params:
        params.update(extra_params)

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Upstream API error: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Upstream API call failed: {e}")
        return None

# Cache for category lookups to improve performance
_category_cache = {}
_cache_timestamp = {}

def get_allowed_category_ids(stream_type, filter_type="full"):
    """Get allowed category IDs based on patterns with caching."""
    cache_key = f"{stream_type}_{filter_type}"

    # Check cache
    if cache_key in _category_cache:
        cache_age = time.time() - _cache_timestamp.get(cache_key, 0)
        if cache_age < CACHE_TIMEOUT:
            return _category_cache[cache_key]

    patterns = CATEGORY_PATTERNS.get(stream_type, {})
    allowed_patterns = patterns.get("full_and_mini", []).copy()

    if filter_type == "full":
        allowed_patterns.extend(patterns.get("full_only", []))

    logging.info(f"Patterns for {stream_type} {filter_type}: {allowed_patterns}")

    # Get categories from upstream API
    if stream_type == "live":
        categories = make_upstream_call("get_live_categories")
    elif stream_type == "vod":
        categories = make_upstream_call("get_vod_categories")
    elif stream_type == "series":
        categories = make_upstream_call("get_series_categories")
    else:
        return set()

    if not categories:
        return set()

    # Find matching category IDs
    allowed_ids = set()
    for category in categories:
        category_name = category.get("category_name", "")
        for pattern in allowed_patterns:
            if category_name.startswith(pattern):
                allowed_ids.add(str(category.get("category_id", "")))
                break

    # Cache the result
    _category_cache[cache_key] = allowed_ids
    _cache_timestamp[cache_key] = time.time()

    logging.info(f"Found {len(allowed_ids)} allowed {stream_type} categories for {filter_type} filter")
    return allowed_ids

def filter_streams(streams, stream_type, filter_type="full"):
    """Filter streams based on category patterns and stream name exclusions."""
    if not streams:
        return []

    # Get allowed category IDs for this stream type and filter
    allowed_category_ids = get_allowed_category_ids(stream_type, filter_type)

    if not allowed_category_ids:
        logging.warning(f"No allowed categories found for {stream_type} {filter_type} filter")
        return []

    filtered = []

    for stream in streams:
        name = stream.get('name', '')
        category_id = str(stream.get('category_id', ''))

        # Apply stream name exclusions (e.g., streams starting with #)
        excluded = False
        for prefix in EXCLUDE_STREAM_PREFIXES:
            if name.startswith(prefix):
                excluded = True
                break

        if excluded:
            continue

        # Check if stream's category is allowed
        if category_id in allowed_category_ids:
            # Apply name tweaks
            stream['name'] = apply_tweaks(name)
            # Keep original category_name as it might be populated by IPTV player
            filtered.append(stream)

    logging.info(f"Filtered {len(streams)} {stream_type} streams to {len(filtered)} ({filter_type} filter)")
    return filtered

def generate_m3u_from_streams(streams, stream_type, filter_type="full", username="", password=""):
    """Generate M3U playlist from filtered streams."""
    m3u_lines = ["#EXTM3U"]

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    m3u_lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="UPDATED: {timestamp} ({filter_type})" tvg-logo="" group-title="SYSTEM",UPDATED: {timestamp} ({filter_type})')
    m3u_lines.append("http://dummy.url/updated_timestamp")

    for stream in streams:
        stream_id = stream.get('stream_id')
        name = stream.get('name', 'Unknown')
        category = stream.get('category_name', 'Unknown')
        icon = stream.get('stream_icon', '')

        # Build stream URL using proxy credentials
        if stream_type == 'live':
            stream_url = f"{request.host_url.rstrip('/')}/live/{username}/{password}/{stream_id}.ts"
        elif stream_type == 'vod':
            stream_url = f"{request.host_url.rstrip('/')}/movie/{username}/{password}/{stream_id}.mp4"
        elif stream_type == 'series':
            stream_url = f"{request.host_url.rstrip('/')}/series/{username}/{password}/{stream_id}.mp4"

        # Build M3U entry
        extinf = f'#EXTINF:-1 tvg-id="{stream_id}" tvg-name="{name}" tvg-logo="{icon}" group-title="{category}",{name}'
        m3u_lines.append(extinf)
        m3u_lines.append(stream_url)

    return "\n".join(m3u_lines)

def create_app(filter_type="full"):
    """Create Flask app with routes."""
    app = Flask(__name__)
    app.config['FILTER_TYPE'] = filter_type

    @app.route('/player_api.php')
    def player_api():
        """Handle Xtream API calls."""
        # Validate credentials
        username = request.args.get('username')
        password = request.args.get('password')

        if not validate_proxy_credentials(username, password):
            return jsonify({"error": "Invalid credentials"}), 401

        action = request.args.get('action')
        category_id = request.args.get('category_id')
        filter_type = app.config.get('FILTER_TYPE', 'full')

        if action == 'get_live_categories':
            categories = make_upstream_call('get_live_categories')
            if categories:
                # Filter categories to only include those with streams we'd show
                live_streams = make_upstream_call('get_live_streams')
                if live_streams:
                    filtered_streams = filter_streams(live_streams, 'live', filter_type)
                    # Get unique categories from filtered streams
                    valid_category_ids = set(str(s.get('category_id', '')) for s in filtered_streams)
                    categories = [cat for cat in categories if str(cat.get('category_id', '')) in valid_category_ids]
            return jsonify(categories or [])

        elif action == 'get_vod_categories':
            categories = make_upstream_call('get_vod_categories')
            if categories:
                vod_streams = make_upstream_call('get_vod_streams')
                if vod_streams:
                    filtered_streams = filter_streams(vod_streams, 'vod', filter_type)
                    valid_category_ids = set(str(s.get('category_id', '')) for s in filtered_streams)
                    categories = [cat for cat in categories if str(cat.get('category_id', '')) in valid_category_ids]
            return jsonify(categories or [])

        elif action == 'get_series_categories':
            categories = make_upstream_call('get_series_categories')
            if categories:
                series = make_upstream_call('get_series')
                if series:
                    filtered_series = filter_streams(series, 'series', filter_type)
                    valid_category_ids = set(str(s.get('category_id', '')) for s in filtered_series)
                    categories = [cat for cat in categories if str(cat.get('category_id', '')) in valid_category_ids]
            return jsonify(categories or [])

        elif action == 'get_live_streams':
            params = {'category_id': category_id} if category_id else None
            streams = make_upstream_call('get_live_streams', params)
            filtered = filter_streams(streams, 'live', filter_type)
            return jsonify(filtered)

        elif action == 'get_vod_streams':
            params = {'category_id': category_id} if category_id else None
            streams = make_upstream_call('get_vod_streams', params)
            filtered = filter_streams(streams, 'vod', filter_type)
            return jsonify(filtered)

        elif action == 'get_series':
            params = {'category_id': category_id} if category_id else None
            series = make_upstream_call('get_series', params)
            filtered = filter_streams(series, 'series', filter_type)
            return jsonify(filtered)

        elif action == 'get_series_info':
            series_id = request.args.get('series_id')
            if series_id:
                return jsonify(make_upstream_call('get_series_info', {'series_id': series_id}) or {})

        return jsonify({"error": "Invalid action"}), 400

    @app.route('/get.php')
    def get_playlist():
        """Generate M3U playlist."""
        # Validate credentials
        username = request.args.get('username')
        password = request.args.get('password')

        if not validate_proxy_credentials(username, password):
            return "Invalid credentials", 401

        playlist_type = request.args.get('type', 'm3u_plus')
        filter_type = app.config.get('FILTER_TYPE', 'full')

        if playlist_type == 'm3u_plus':
            # Get all live streams and filter them
            streams = make_upstream_call('get_live_streams')
            if streams:
                filtered = filter_streams(streams, 'live', filter_type)
                m3u_content = generate_m3u_from_streams(filtered, 'live', filter_type, username, password)
                return Response(m3u_content, mimetype='application/octet-stream')

        return "Playlist type not supported", 400

    @app.route('/live/<username>/<password>/<stream_id>.ts')
    def proxy_live_stream(username, password, stream_id):
        """Proxy live stream to upstream server."""
        stream_user, stream_pass = get_user_credentials(username, password)
        if not stream_user or not stream_pass:
            return "Invalid credentials", 401

        # Redirect to upstream server using real credentials
        upstream_url = f"{UPSTREAM_SERVER}/live/{stream_user}/{stream_pass}/{stream_id}.ts"
        return redirect(upstream_url, code=302)

    @app.route('/movie/<username>/<password>/<stream_id>.mp4')
    def proxy_movie_stream(username, password, stream_id):
        """Proxy movie stream to upstream server."""
        stream_user, stream_pass = get_user_credentials(username, password)
        if not stream_user or not stream_pass:
            return "Invalid credentials", 401

        upstream_url = f"{UPSTREAM_SERVER}/movie/{stream_user}/{stream_pass}/{stream_id}.mp4"
        return redirect(upstream_url, code=302)

    @app.route('/series/<username>/<password>/<stream_id>.mp4')
    def proxy_series_stream(username, password, stream_id):
        """Proxy series stream to upstream server."""
        stream_user, stream_pass = get_user_credentials(username, password)
        if not stream_user or not stream_pass:
            return "Invalid credentials", 401

        upstream_url = f"{UPSTREAM_SERVER}/series/{stream_user}/{stream_pass}/{stream_id}.mp4"
        return redirect(upstream_url, code=302)

    @app.route('/xmltv.php')
    def proxy_epg():
        """Proxy EPG/XMLTV to upstream server."""
        username = request.args.get('username')
        password = request.args.get('password')

        stream_user, stream_pass = get_user_credentials(username, password)
        if not stream_user or not stream_pass:
            return "Invalid credentials", 401

        # Redirect to upstream EPG using the user's stream credentials
        upstream_url = f"{UPSTREAM_SERVER}/xmltv.php?username={stream_user}&password={stream_pass}"
        return redirect(upstream_url, code=302)

    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        filter_type = app.config.get('FILTER_TYPE', 'full')
        return jsonify({"status": "healthy", "filter_type": filter_type, "timestamp": datetime.now().isoformat()})

    return app

def run_server(port, filter_type):
    """Run server on specific port."""
    app = create_app(filter_type)
    logging.info(f"Starting {filter_type} filter server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # Start both servers in separate threads

    # Full filter on 8080
    full_thread = threading.Thread(target=run_server, args=(8080, "full"))
    full_thread.daemon = True
    full_thread.start()

    # Mini filter on 7070
    mini_thread = threading.Thread(target=run_server, args=(7070, "mini"))
    mini_thread.daemon = True
    mini_thread.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down servers")