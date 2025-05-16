#!/usr/bin/env python3
import subprocess
import sys

# --- CONFIG ---
ROFI_CMD = [
    "rofi",
    "-dmenu",
    "-theme",
    "~/.config/rofi/current_theme_single_column.rasi",
    "-p",
    "Watch Later 📺",
]
LAUNCH_CMD = ["mpv"]
# Browser and profile to use for cookies
BROWSER = "vivaldi"
PROFILE = "rash"


# --- FUNCTIONS ---
def rofi_prompt(items, prompt_text=None):
    """Show the magical rofi selection menu ✨"""
    cmd = ROFI_CMD.copy()
    if prompt_text:
        cmd[-1] = prompt_text

    input_str = "\n".join(items)
    result = subprocess.run(
        cmd,
        input=input_str.encode(),
        stdout=subprocess.PIPE,
    )
    return result.stdout.decode().strip()


def fetch_watch_later():
    """The critical treasure hunt - actually works! 💎"""

    # Format for output string, broken into multiple lines to meet line length requirements
    format_str = (
        "%(channel)s|||%(title)s|||%(duration_string)s|||"
        "%(is_live)s|||https://www.youtube.com/watch?v=%(id)s"
    )

    # Different URLs to try for Watch Later - YouTube changes its API regularly
    urls_to_try = [
        "https://www.youtube.com/playlist?list=WL",  # Standard format
        "https://www.youtube.com/feed/watch_later",  # Feed format
    ]

    errors = []
    for url in urls_to_try:
        try:
            print(f"🔍 Trying to access Watch Later via: {url}")

            # Basic command structure using browser cookies
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--cookies-from-browser",
                f"{BROWSER}:{PROFILE}",
                "--no-warnings",
                url,
                "--print",
                format_str,
            ]

            # Add extra authentication flags to increase chances of success
            cmd.insert(1, "--extractor-args")
            cmd.insert(2, "youtube:player_client=web")

            output = subprocess.check_output(cmd, stderr=subprocess.PIPE)
            videos = parse_videos(output)

            if videos:
                print(f"✅ Successfully accessed Watch Later via: {url}")
                return videos
            else:
                errors.append(f"No videos found using URL: {url}")

        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else str(e)
            errors.append(f"Error with {url}: {error_output}")

    # If we reach here, all URLs failed
    print("🚨 Could not access Watch Later playlist.")
    for error in errors:
        print(f"  - {error}")

    # Test if cookies are valid at all
    try:
        print("🔍 Testing if your browser cookies are valid...")
        test_cmd = [
            "yt-dlp",
            "--cookies-from-browser",
            f"{BROWSER}:{PROFILE}",
            "https://www.youtube.com",
            "--skip-download",
        ]
        subprocess.check_output(test_cmd, stderr=subprocess.PIPE)
        print(
            "✅ Your cookies are valid, but can't access Watch Later. "
            "Try using a different browser profile where you are logged into YouTube."
        )
    except subprocess.CalledProcessError:
        print("❌ Your browser cookies appear to be invalid or expired!")
        print("Please log in to YouTube in your browser.")

    sys.exit(1)


def parse_videos(output):
    """Turn YouTube's cryptic output into useful data 🧩"""
    lines = output.decode().strip().split("\n")
    videos = []

    for line in lines:
        if not line.strip():
            continue

        try:
            parts = line.split("|||")
            if len(parts) != 5:
                continue

            channel, title, duration, is_live, url = parts
            prefix = "🔴 LIVE: " if is_live.lower() == "true" else ""
            suffix = f" [{duration}]" if duration else ""

            display = f"{prefix}{channel} - {title}{suffix}"
            videos.append({"display": display, "url": url, "title": title})
        except Exception as e:
            print(f"⚠️ Error parsing video: {str(e)}")
            continue

    return videos


def launch_video(video):
    """Fire the video into your eyeballs 👀"""
    cmd = LAUNCH_CMD + [f"--title=Watch Later - {video['title']}", video["url"]]
    subprocess.Popen(cmd)


# --- MAIN ---
def main():
    """The grand orchestration 🎭"""
    print("🎬 Fetching your Watch Later videos...")
    videos = fetch_watch_later()

    if not videos:
        print("😢 No videos found in your Watch Later list")
        sys.exit(1)

    print(f"🎉 Found {len(videos)} videos in your Watch Later list")

    # Prepare the selection menu
    menu_items = [video["display"] for video in videos]
    selected = rofi_prompt(menu_items)

    if not selected:
        print("❌ No video selected")
        sys.exit(0)

    # Find the selected video
    for video in videos:
        if video["display"] == selected:
            print(f"▶️ Playing: {video['title']}")
            launch_video(video)
            break


if __name__ == "__main__":
    main()
