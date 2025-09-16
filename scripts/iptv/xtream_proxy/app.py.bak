#!/usr/bin/env python3
"""
Xtream API Proxy Server
Filters and proxies Xtream API calls with your custom filter rules
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response, redirect
import requests

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Load config from environment
UPSTREAM_SERVER = os.getenv('UPSTREAM_SERVER', '')
UPSTREAM_USERNAME = os.getenv('UPSTREAM_USERNAME', '')
UPSTREAM_PASSWORD = os.getenv('UPSTREAM_PASSWORD', '')
STREAM_USERNAME = os.getenv('STREAM_USERNAME', '')
STREAM_PASSWORD = os.getenv('STREAM_PASSWORD', '')
PROXY_USERNAME = os.getenv('PROXY_USERNAME', 'proxy_user')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', 'proxy_pass')

if not all([UPSTREAM_SERVER, UPSTREAM_USERNAME, UPSTREAM_PASSWORD]):
    raise RuntimeError("Missing required environment variables")

# Use STREAM credentials for actual streaming if available
if not STREAM_USERNAME:
    STREAM_USERNAME = UPSTREAM_USERNAME
if not STREAM_PASSWORD:
    STREAM_PASSWORD = UPSTREAM_PASSWORD

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

def filter_streams(streams, stream_type, filter_type="full"):
    """Filter streams based on rules."""
    if not streams:
        return []

    filtered = []
    for stream in streams:
        name = stream.get('name', '')
        category_name = stream.get('category_name', '')

        # Guess category for filtering
        if stream_type == 'live':
            category = guess_category(category_name, stream.get('stream_id'), name, name)
        elif stream_type == 'vod':
            category = 'movies'
        elif stream_type == 'series':
            category = 'series'
        else:
            category = 'tv'

        if should_include(name, category, category_name, filter_type):
            # Apply name tweaks
            stream['name'] = apply_tweaks(name)
            stream['category_name'] = apply_tweaks(category_name)
            filtered.append(stream)

    logging.info(f"Filtered {len(streams)} {stream_type} streams to {len(filtered)}")
    return filtered

def generate_m3u_from_streams(streams, stream_type):
    """Generate M3U playlist from filtered streams."""
    m3u_lines = ["#EXTM3U"]

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    m3u_lines.append(f'#EXTINF:-1 tvg-id="" tvg-name="UPDATED: {timestamp}" tvg-logo="" group-title="SYSTEM",UPDATED: {timestamp}')
    m3u_lines.append("http://dummy.url/updated_timestamp")

    for stream in streams:
        stream_id = stream.get('stream_id')
        name = stream.get('name', 'Unknown')
        category = stream.get('category_name', 'Unknown')
        icon = stream.get('stream_icon', '')

        # Build stream URL using proxy credentials
        if stream_type == 'live':
            stream_url = f"{request.host_url.rstrip('/')}/live/{PROXY_USERNAME}/{PROXY_PASSWORD}/{stream_id}.ts"
        elif stream_type == 'vod':
            stream_url = f"{request.host_url.rstrip('/')}/movie/{PROXY_USERNAME}/{PROXY_PASSWORD}/{stream_id}.mp4"
        elif stream_type == 'series':
            stream_url = f"{request.host_url.rstrip('/')}/series/{PROXY_USERNAME}/{PROXY_PASSWORD}/{stream_id}.mp4"

        # Build M3U entry
        extinf = f'#EXTINF:-1 tvg-id="{stream_id}" tvg-name="{name}" tvg-logo="{icon}" group-title="{category}",{name}'
        m3u_lines.append(extinf)
        m3u_lines.append(stream_url)

    return "\n".join(m3u_lines)

# ========== ROUTES ==========

@app.route('/player_api.php')
def player_api():
    """Handle Xtream API calls."""
    # Validate credentials
    username = request.args.get('username')
    password = request.args.get('password')

    if username != PROXY_USERNAME or password != PROXY_PASSWORD:
        return jsonify({"error": "Invalid credentials"}), 401

    action = request.args.get('action')
    category_id = request.args.get('category_id')

    if action == 'get_live_categories':
        categories = make_upstream_call('get_live_categories')
        if categories:
            # Filter categories to only include those with streams we'd show
            live_streams = make_upstream_call('get_live_streams')
            if live_streams:
                filtered_streams = filter_streams(live_streams, 'live')
                # Get unique categories from filtered streams
                valid_category_ids = set(str(s.get('category_id', '')) for s in filtered_streams)
                categories = [cat for cat in categories if str(cat.get('category_id', '')) in valid_category_ids]
        return jsonify(categories or [])

    elif action == 'get_vod_categories':
        categories = make_upstream_call('get_vod_categories')
        if categories:
            vod_streams = make_upstream_call('get_vod_streams')
            if vod_streams:
                filtered_streams = filter_streams(vod_streams, 'vod')
                valid_category_ids = set(str(s.get('category_id', '')) for s in filtered_streams)
                categories = [cat for cat in categories if str(cat.get('category_id', '')) in valid_category_ids]
        return jsonify(categories or [])

    elif action == 'get_series_categories':
        categories = make_upstream_call('get_series_categories')
        if categories:
            series = make_upstream_call('get_series')
            if series:
                filtered_series = filter_streams(series, 'series')
                valid_category_ids = set(str(s.get('category_id', '')) for s in filtered_series)
                categories = [cat for cat in categories if str(cat.get('category_id', '')) in valid_category_ids]
        return jsonify(categories or [])

    elif action == 'get_live_streams':
        params = {'category_id': category_id} if category_id else None
        streams = make_upstream_call('get_live_streams', params)
        filtered = filter_streams(streams, 'live')
        return jsonify(filtered)

    elif action == 'get_vod_streams':
        params = {'category_id': category_id} if category_id else None
        streams = make_upstream_call('get_vod_streams', params)
        filtered = filter_streams(streams, 'vod')
        return jsonify(filtered)

    elif action == 'get_series':
        params = {'category_id': category_id} if category_id else None
        series = make_upstream_call('get_series', params)
        filtered = filter_streams(series, 'series')
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

    if username != PROXY_USERNAME or password != PROXY_PASSWORD:
        return "Invalid credentials", 401

    playlist_type = request.args.get('type', 'm3u_plus')

    if playlist_type == 'm3u_plus':
        # Get all live streams and filter them
        streams = make_upstream_call('get_live_streams')
        if streams:
            filtered = filter_streams(streams, 'live')
            m3u_content = generate_m3u_from_streams(filtered, 'live')
            return Response(m3u_content, mimetype='application/octet-stream')

    return "Playlist type not supported", 400

@app.route('/live/<username>/<password>/<stream_id>.ts')
def proxy_live_stream(username, password, stream_id):
    """Proxy live stream to upstream server."""
    if username != PROXY_USERNAME or password != PROXY_PASSWORD:
        return "Invalid credentials", 401

    # Redirect to upstream server using real credentials
    upstream_url = f"{UPSTREAM_SERVER}/live/{STREAM_USERNAME}/{STREAM_PASSWORD}/{stream_id}.ts"
    return redirect(upstream_url, code=302)

@app.route('/movie/<username>/<password>/<stream_id>.mp4')
def proxy_movie_stream(username, password, stream_id):
    """Proxy movie stream to upstream server."""
    if username != PROXY_USERNAME or password != PROXY_PASSWORD:
        return "Invalid credentials", 401

    upstream_url = f"{UPSTREAM_SERVER}/movie/{STREAM_USERNAME}/{STREAM_PASSWORD}/{stream_id}.mp4"
    return redirect(upstream_url, code=302)

@app.route('/series/<username>/<password>/<stream_id>.mp4')
def proxy_series_stream(username, password, stream_id):
    """Proxy series stream to upstream server."""
    if username != PROXY_USERNAME or password != PROXY_PASSWORD:
        return "Invalid credentials", 401

    upstream_url = f"{UPSTREAM_SERVER}/series/{STREAM_USERNAME}/{STREAM_PASSWORD}/{stream_id}.mp4"
    return redirect(upstream_url, code=302)

@app.route('/xmltv.php')
def proxy_epg():
    """Proxy EPG/XMLTV to upstream server."""
    username = request.args.get('username')
    password = request.args.get('password')

    if username != PROXY_USERNAME or password != PROXY_PASSWORD:
        return "Invalid credentials", 401

    # Redirect to upstream EPG
    upstream_url = f"{UPSTREAM_SERVER}/xmltv.php?username={UPSTREAM_USERNAME}&password={UPSTREAM_PASSWORD}"
    return redirect(upstream_url, code=302)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)