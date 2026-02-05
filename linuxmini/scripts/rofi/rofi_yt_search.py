#!/usr/bin/env python3

import subprocess
import sys

# --- CONFIG ---
MAX_RESULTS = 20
ROFI_CMD = [
    "rofi",
    "-dmenu",
    "-theme",
    "~/.config/rofi/current_theme_single_column.rasi",
    "-p",
    "YouTube 🔎",
]
LAUNCH_CMD = [
    "mpv"
]  # Title with channel name]  # Change to ["mpv"] if you want to play directly

# --- FUNCTIONS ---


def rofi_prompt(prompt_text):
    """Prompt user for input via Rofi."""
    result = subprocess.run(
        ROFI_CMD,
        input=(prompt_text + "\n").encode(),  # force prefilled first entry
        stdout=subprocess.PIPE,
    )
    output = result.stdout.decode().strip()
    if output == prompt_text:
        return ""  # User didn't type anything new
    return output


def fetch_youtube_results(query, max_results):
    """Fetch YouTube search results quickly using yt-dlp flat playlist."""
    try:
        output = subprocess.check_output(
            [
                "yt-dlp",
                "--flat-playlist",
                f"ytsearch{max_results}:{query}",
                "--print",
                "%(channel)s|||%(title)s|||%(duration_string)s|||%(is_live)s|||"
                "https://www.youtube.com/watch?v=%(id)s",
                "--no-warnings",
                "--cookies-from-browser",
                "brave:app",
            ]
        )
        lines = output.decode().strip().split("\n")
        results = []
        for line in lines:
            if not line.strip():
                continue
            uploader, title, duration, is_live, url = line.split("|||")
            prefix = "🔴 Live - " if is_live.lower() == "true" else ""
            suffix = f" [{duration}]" if duration else ""
            results.append(
                {
                    "display": f"{prefix}{uploader} - {title}{suffix}",
                    "title": title,
                    "url": url,
                }
            )
        return results
    except subprocess.CalledProcessError:
        return []


def select_result(results):
    """Show results in Rofi and return selected item."""
    menu = "\n".join(item["display"] for item in results)
    selected = rofi_prompt(menu)
    for item in results:
        if item["display"] == selected:
            return item
    return None


def launch_url(url, title):
    """Open URL with the configured launcher."""
    full_cmd = LAUNCH_CMD + [f"--title=rofi_ytsearch - {title}", "--ytdl-raw-options=cookies-from-browser=brave:app", url]
    subprocess.Popen(full_cmd)


# --- MAIN ---


def main():
    query = rofi_prompt("Search YouTube above...")
    if not query:
        sys.exit(0)

    results = fetch_youtube_results(query, MAX_RESULTS)
    if not results:
        subprocess.run(["notify-send", "No results found 😞"])
        sys.exit(1)

    choice = select_result(results)
    if not choice:
        sys.exit(0)

    launch_url(choice["url"], choice["title"])


if __name__ == "__main__":
    main()
