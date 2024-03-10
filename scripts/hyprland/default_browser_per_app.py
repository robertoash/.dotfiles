#! /usr/bin/env python3

import json
import subprocess
import time


def get_active_window_info():
    """Get the active window class and title."""
    output = subprocess.run("hyprctl activewindow -j", shell=True, capture_output=True)
    output_json = json.loads(output.stdout)
    window_class = output_json.get("class", "")
    window_title = output_json.get("title", "")
    return window_class, window_title


def get_browser(window_class, window_title, browser_map):
    """Determine the browser based on window class and title."""
    for (map_class, title_substr), browser in browser_map.items():
        if map_class == window_class and (
            title_substr == "*" or title_substr in window_title
        ):
            return browser
    # Fallback to global default
    return browser_map[("default", "*")]


def set_default_browser(browser):
    """Set system default web browser."""
    subprocess.call(f"xdg-settings set default-web-browser {browser}", shell=True)
    print("Correctly set xdg-settings")


def set_gh_browser(browser):
    """Set GitHub CLI browser."""
    gh_browser = browser.split(".")[
        0
    ]  # Assuming the .desktop filename without extension
    subprocess.call(f"gh config set browser {gh_browser}", shell=True)
    print("Correctly set gh browser")


def main():
    # Browser mappings
    browser_map = {
        # Format: (window_class, string_to_search_for_in_window_title): 'browser.desktop'
        ("default", "*"): "vivaldi.desktop",
        ("Code", " Work "): "chromium.desktop",
        ("Code", "*"): "vivaldi.desktop",
        ("code-insiders-url-handler", " Work "): "chromium.desktop",
        ("code-insiders-url-handler", "*"): "vivaldi.desktop",
        ("chromium", "*"): "chromium.desktop",
        ("Slack", "*"): "chromium.desktop",
    }

    last_selected_browser = None

    while True:
        window_class, window_title = get_active_window_info()
        selected_browser = get_browser(window_class, window_title, browser_map)

        if selected_browser != last_selected_browser:
            set_default_browser(selected_browser)
            set_gh_browser(selected_browser)
            last_selected_browser = selected_browser

        print(f"Set default browser to {selected_browser}")
        time.sleep(1)


if __name__ == "__main__":
    main()
