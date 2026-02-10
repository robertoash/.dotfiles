#!/usr/bin/env python3
import sys
import subprocess
import os
import tempfile
import json
import re
import shutil
from pathlib import Path

def parse_args():
    """Parse command line arguments"""
    args = {
        'debug': '--debug' in sys.argv,
        'cli': '--cli' in sys.argv,
        'search_terms': []
    }

    # Collect non-flag arguments as search terms
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            args['search_terms'].append(arg)

    return args

API_CONTENT = "https://contento.svt.se/graphql"
API_VIDEO = "https://api.svt.se/videoplayer-api/video/"
DESC_MAX_LENGTH = 100
ROFI_THEME = os.path.expanduser("~/.config/rofi/current_theme_rofi_jellyfin.rasi")

def check_fzf_available():
    """Check if fzf is installed and available"""
    if not shutil.which('fzf'):
        print("Error: fzf is not installed or not in PATH", file=sys.stderr)
        print("Please install fzf: https://github.com/junegunn/fzf", file=sys.stderr)
        sys.exit(1)

def check_rofi_available():
    """Check if rofi is installed and available"""
    if not shutil.which('rofi'):
        print("Error: rofi is not installed or not in PATH", file=sys.stderr)
        print("Install rofi: https://github.com/davatorium/rofi", file=sys.stderr)
        sys.exit(1)

def _graphql_query(query):
    """Execute GraphQL query against SVT API"""
    payload = json.dumps({"query": query})
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", API_CONTENT,
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

def get_selections():
    """Fetch all selections from startForSvtPlay"""
    query = "{startForSvtPlay{selections{id name}}}"
    data = _graphql_query(query)
    selections = data.get('data', {}).get('startForSvtPlay', {}).get('selections', [])
    return [(s['id'], s['name']) for s in selections]

def get_content_from_selection(selection_id):
    """Fetch content from a specific selection"""
    escaped_id = selection_id.replace('"', '\\"')
    query = f'''{{
        selectionById(id:"{escaped_id}"){{
            items{{
                item{{
                    __typename
                    ...on TvSeries{{id name longDescription urls{{svtplay}}}}
                    ...on Episode{{id name longDescription parent{{name}} urls{{svtplay}}}}
                    ...on Single{{id name longDescription urls{{svtplay}}}}
                    ...on TvShow{{id name longDescription urls{{svtplay}}}}
                    ...on KidsTvShow{{id name longDescription urls{{svtplay}}}}
                }}
            }}
        }}
    }}'''
    data = _graphql_query(query)
    items = data.get('data', {}).get('selectionById', {}).get('items', [])

    results = []
    for item_wrapper in items:
        item = item_wrapper.get('item', {})
        if not item.get('urls', {}).get('svtplay'):
            continue

        name = item.get('name', 'No title')
        parent = item.get('parent', {}).get('name')
        if parent:
            name = f"{parent} - {name}"

        desc = item.get('longDescription', '')[:DESC_MAX_LENGTH]
        url = f"https://www.svtplay.se{item.get('urls', {}).get('svtplay', '')}"
        results.append((name, desc, url))

    return results

def get_all_content():
    """Fetch ALL content from ALL selections"""
    query = '''{
        startForSvtPlay{
            selections{
                items{
                    item{
                        __typename
                        ...on TvSeries{name longDescription urls{svtplay}}
                        ...on TvShow{name longDescription urls{svtplay}}
                        ...on Episode{name longDescription urls{svtplay}}
                        ...on Single{name longDescription urls{svtplay}}
                        ...on KidsTvShow{name longDescription urls{svtplay}}
                    }
                }
            }
        }
    }'''
    data = _graphql_query(query)
    selections = data.get('data', {}).get('startForSvtPlay', {}).get('selections', [])

    results = []
    for selection in selections:
        for item_wrapper in selection.get('items', []):
            item = item_wrapper.get('item', {})
            if not item.get('urls', {}).get('svtplay'):
                continue

            name = item.get('name', 'No title')
            desc = item.get('longDescription', '')[:DESC_MAX_LENGTH]
            url = f"https://www.svtplay.se{item.get('urls', {}).get('svtplay', '')}"
            results.append((name, desc, url))

    return list(set(results))  # Remove duplicates

def search_content(search_term):
    """Search for content by keyword"""
    escaped_term = search_term.replace('"', '\\"')
    query = f'''{{
        searchPage(query:"{escaped_term}",maxHits:100){{
            flat{{
                hits{{
                    teaser{{name description item{{urls{{svtplay}}}}}}
                    categoryTeaser{{heading slug}}
                }}
            }}
        }}
    }}'''
    data = _graphql_query(query)
    search_data = data.get('data') or {}
    search_page = search_data.get('searchPage') or {}
    flat = search_page.get('flat') or {}
    hits = flat.get('hits', [])

    results = []
    for hit in hits:
        if 'teaser' in hit and hit['teaser'] is not None:
            teaser = hit['teaser']
            if not teaser.get('item', {}).get('urls', {}).get('svtplay'):
                continue
            name = teaser.get('name', '')
            desc = teaser.get('description', '')[:DESC_MAX_LENGTH]
            url = f"https://www.svtplay.se{teaser.get('item', {}).get('urls', {}).get('svtplay', '')}"
            results.append((name, desc, url))
        elif 'categoryTeaser' in hit and hit['categoryTeaser'] is not None:
            cat = hit['categoryTeaser']
            name = cat.get('heading', '').replace('<em>', '').replace('</em>', '')
            url = f"https://www.svtplay.se/{cat.get('slug', '')}"
            results.append((name, '[Category]', url))

    return results

def get_mpv_flags(debug_mode):
    """Get mpv flags based on hostname and debug mode"""
    flags = []
    if not debug_mode:
        flags.extend(['--really-quiet', '--no-terminal'])

    hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
    if hostname == 'linuxmini':
        flags.append('--wayland-app-id=mpv-svtplay')

    return flags

def play_video(url, debug_mode=False):
    """Play video URL with mpv (handles live streams via SVT API)"""
    mpv_flags = get_mpv_flags(debug_mode)

    # Extract video ID from URL
    video_id_match = re.search(r'/video/([^/]+)', url)

    if video_id_match:
        video_id = video_id_match.group(1)
        print("Checking stream info...", file=sys.stderr)

        # Check SVT API for stream info
        api_url = f"{API_VIDEO}{video_id}"
        result = subprocess.run(['curl', '-s', '--max-time', '10', api_url], capture_output=True, text=True)

        if result.returncode == 0:
            try:
                api_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                api_data = {}

            is_live = api_data.get('live', False)

            if is_live:
                # Live stream - get HLS URL
                for ref in api_data.get('videoReferences', []):
                    if ref.get('format') == 'hls':
                        hls_url = ref.get('url')
                        if hls_url and (hls_url.startswith('http://') or hls_url.startswith('https://')):
                            # Verify URL is accessible
                            check = subprocess.run(
                                ['curl', '-sf', '--max-time', '10', hls_url],
                                capture_output=True,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            if check.returncode == 0:
                                print("Starting live stream...", file=sys.stderr)
                                url = hls_url
                                break
                        else:
                            print("Live stream URL unavailable, falling back to yt-dlp...", file=sys.stderr)

    # Start playback
    print("Starting playback...", file=sys.stderr)
    mpv_cmd = ['mpv'] + mpv_flags + [url]

    if debug_mode:
        result = subprocess.run(mpv_cmd)
        return result.returncode == 0
    else:
        # Background playback
        process = subprocess.Popen(
            mpv_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for window to appear
        wait_result = subprocess.run(
            ['hypr-window-ops', 'window-wait', '--pid', str(process.pid)],
            capture_output=True
        )

        if wait_result.returncode != 0:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("svtp: Playback failed. Run with --debug for details.", file=sys.stderr)
            return False

        return True

def show_fzf_menu(items, prompt="Select", preview=True):
    """Show fzf menu and return selected item"""
    # Write items to temp file
    tmpfile = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    for item in items:
        if len(item) == 2:
            # Simple tuple (id, name)
            tmpfile.write(f"{item[0]}\t{item[1]}\n")
        else:
            # Full tuple (name, desc, url)
            tmpfile.write(f"{item[0]}\t{item[1]}\t{item[2]}\n")
    tmpfile.close()

    # Build fzf command
    fzf_cmd = [
        'fzf',
        '--delimiter=\t',
        '--with-nth=1',
        '--prompt', f"{prompt} > ",
        '--height=40%'
    ]

    if preview and len(items) > 0 and len(items[0]) > 2:
        fzf_cmd.extend([
            '--preview', 'echo {2}; echo; echo {3}',
            '--preview-window=down:3:wrap'
        ])

    # Run fzf
    try:
        with open(tmpfile.name, 'r') as f:
            result = subprocess.run(
                fzf_cmd,
                stdin=f,
                capture_output=True,
                text=True
            )
    finally:
        # Cleanup
        os.unlink(tmpfile.name)

    if result.returncode == 0:
        return result.stdout.strip()
    return None

def browse_with_fzf(debug_mode=False):
    """Browse SVT Play with fzf interface"""
    check_fzf_available()

    # Show main menu
    menu_items = [
        ('editors_pick', "Editor's Pick"),
        ('categories', 'Categories'),
        ('all_content', 'All Content')
    ]

    selected = show_fzf_menu(menu_items, "SVT Play Browser", preview=False)
    if not selected:
        return

    choice = selected.split('\t')[0]

    # Handle menu choice
    content = []
    if choice == 'editors_pick':
        print("Fetching editor's picks...", file=sys.stderr)
        content = get_content_from_selection('popular_start')
    elif choice == 'categories':
        # Show categories submenu
        print("Loading categories...", file=sys.stderr)
        categories = get_selections()
        selected_cat = show_fzf_menu(categories, "Select category", preview=False)
        if not selected_cat:
            return

        cat_id = selected_cat.split('\t')[0]
        cat_name = selected_cat.split('\t')[1]
        print(f"Fetching content from {cat_name}...", file=sys.stderr)
        content = get_content_from_selection(cat_id)
    elif choice == 'all_content':
        print("Fetching all available content (this may take a moment)...", file=sys.stderr)
        content = get_all_content()

    if not content:
        print("No results found", file=sys.stderr)
        return

    # Show content selection
    content = sorted(set(content))  # Remove duplicates and sort
    selected = show_fzf_menu(content, "Select video")
    if not selected:
        return

    # Extract URL and play
    url = selected.split('\t')[-1]
    play_video(url, debug_mode)

def handle_search_with_fzf(search_term, debug_mode=False):
    """Handle search mode with fzf"""
    check_fzf_available()

    print(f"Searching for: {search_term}", file=sys.stderr)
    results = search_content(search_term)

    if not results:
        print(f"No results found for '{search_term}'", file=sys.stderr)
        return

    if len(results) == 1:
        # Single result - play directly
        url = results[0][2]
        play_video(url, debug_mode)
    else:
        # Multiple results - show in fzf
        print(f"Found {len(results)} results", file=sys.stderr)
        selected = show_fzf_menu(results, "Select")
        if selected:
            url = selected.split('\t')[-1]
            play_video(url, debug_mode)

def show_rofi_menu(items, prompt="Select", show_back=False):
    """Show rofi menu and return (action, selected_item)"""
    menu_text = []
    item_map = {}

    for item in items:
        if len(item) == 2:
            # Simple tuple (id, name) - for categories
            display = f"📂 {item[1]}"
            item_map[display] = item
        else:
            # Full tuple (name, desc, url) - for content
            name, desc, url = item
            # Determine icon based on content type
            if 'episode' in name.lower() or ' - ' in name:
                icon = '📼'
            else:
                icon = '📺'
            display = f"{icon} {name}"
            item_map[display] = item
        menu_text.append(display)

    # Build rofi command
    mesg = "Alt+h: Back" if show_back else ""
    rofi_cmd = [
        'rofi',
        '-dmenu',
        '-i',
        '-p', prompt,
        '-theme', ROFI_THEME
    ]

    if show_back:
        rofi_cmd.extend([
            '-kb-custom-1', 'Alt+h',
            '-mesg', mesg
        ])

    # Run rofi
    result = subprocess.run(
        rofi_cmd,
        input='\n'.join(menu_text),
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        # Normal selection
        selected = result.stdout.strip()
        return ('select', item_map.get(selected))
    elif result.returncode == 10:
        # Alt+h pressed (back)
        return ('back', None)
    else:
        # Cancelled
        return (None, None)

def show_rofi_error(message):
    """Show error dialog in rofi"""
    subprocess.run(['rofi', '-e', message], capture_output=True)

def browse_with_rofi(debug_mode=False):
    """Browse SVT Play with rofi interface"""
    check_rofi_available()

    # Show main menu
    menu_items = [
        ('editors_pick', "📺 Editor's Pick"),
        ('categories', '📂 Categories'),
        ('all_content', '📋 All Content')
    ]

    # Format for rofi (just display names)
    display_items = [(item[0], item[1]) for item in menu_items]
    action, selected = show_rofi_menu(display_items, "SVT Play", show_back=False)

    if action != 'select' or not selected:
        return

    choice = selected[0]

    # Handle menu choice
    content = []
    if choice == 'editors_pick':
        content = get_content_from_selection('popular_start')
    elif choice == 'categories':
        # Show categories submenu
        categories = get_selections()
        action, selected_cat = show_rofi_menu(categories, "Select Category", show_back=True)

        if action == 'back':
            # Go back to main menu
            browse_with_rofi(debug_mode)
            return
        elif action != 'select' or not selected_cat:
            return

        cat_id, cat_name = selected_cat
        content = get_content_from_selection(cat_id)
    elif choice == 'all_content':
        content = get_all_content()

    if not content:
        show_rofi_error("No results found")
        return

    # Show content selection
    content = sorted(set(content))  # Remove duplicates and sort
    action, selected = show_rofi_menu(content, "Select Video", show_back=True)

    if action == 'back':
        # Go back to main menu
        browse_with_rofi(debug_mode)
        return
    elif action != 'select' or not selected:
        return

    # Extract URL and play
    url = selected[2]
    if not play_video(url, debug_mode):
        show_rofi_error("Playback failed. Run with --debug for details.")

def main():
    args = parse_args()
    debug_mode = args['debug']
    cli_mode = args['cli']
    search_terms = args['search_terms']

    # Determine mode: CLI (fzf) vs Rofi
    use_cli = cli_mode or bool(search_terms)

    # Check for direct URL or video ID
    if search_terms:
        input_str = ' '.join(search_terms)

        # Check if it's a URL or video ID
        if input_str.startswith('http') or input_str.startswith('/video/'):
            url = input_str if input_str.startswith('http') else f"https://www.svtplay.se{input_str}"
            return 0 if play_video(url, debug_mode) else 1

        # Search mode (always uses fzf)
        handle_search_with_fzf(input_str, debug_mode)
    elif use_cli:
        # Browse with fzf
        browse_with_fzf(debug_mode)
    else:
        # Browse with rofi (default)
        browse_with_rofi(debug_mode)

    return 0

if __name__ == "__main__":
    sys.exit(main())
