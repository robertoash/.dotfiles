import os
import socket
from datetime import datetime, timedelta
from pathlib import Path

config.load_autoconfig()

# Tokyo Night Deep palette colors
background = "#010111"
foreground = "#ffffff"
accent = "#8bffff"
cursor = "#7dcfff"
selection_bg = "#515c7e"

# Base colors
color0 = "#363b54"  # Dark gray
color1 = "#f7768e"  # Red
color2 = "#41a6b5"  # Cyan
color3 = "#e6c100"  # Yellow
color4 = "#7aa2f7"  # Blue
color5 = "#bb9af7"  # Purple
color6 = "#7dcfff"  # Light cyan
color7 = "#b9bdcc"  # Light gray

# Bright variants
color8 = "#454c6d"  # Bright dark gray
color9 = "#ff5f8f"  # Bright red
color10 = "#00ffbb"  # Bright green
color11 = "#ffee00"  # Bright yellow
color12 = "#82aaff"  # Bright blue
color13 = "#d5a6ff"  # Bright purple
color14 = "#8bffff"  # Bright cyan
color15 = "#d0d6e3"  # Bright white

# Dark variants
color16 = "#1d1d2c"  # Very dark gray
color24 = "#0b0c19"  # Really dark gray


# === HISTORY CLEANUP ===

import sys
from qutebrowser.api import cmdutils

# Add userscripts directory to Python path for imports
# Use config file location to find userscripts (works on both Linux and macOS)
config_dir = os.path.dirname(os.path.abspath(__file__))
userscripts_dir = os.path.join(config_dir, "userscripts")
if userscripts_dir not in sys.path:
    sys.path.insert(0, userscripts_dir)

# Try to import builtin cleanup (uses qutebrowser's Python with sqlite3)
try:
    from cleanup_history_builtin import cleanup_old_history as builtin_cleanup
    HAS_SQLITE3 = True
except ImportError:
    HAS_SQLITE3 = False

if HAS_SQLITE3:
    # Use builtin cleanup (works on Nix qutebrowser with sqlite3)
    try:
        @cmdutils.register(name="history-cleanup")
        def history_cleanup_command(days: int = 30):
            """Clean up history entries older than specified days."""
            from qutebrowser.api import message
            try:
                result = builtin_cleanup(config.datadir, days)
                if result:
                    message.info(result)
            except Exception as e:
                message.error(f"History cleanup failed: {e}")
    except:
        pass
else:
    # Fall back to external script (uses system Python with sqlite3)
    import subprocess

    try:
        @cmdutils.register(name="history-cleanup")
        def history_cleanup_command(days: int = 30):
            """Clean up history entries older than specified days using external script."""
            from qutebrowser.api import message
            try:
                result = subprocess.run(
                    ["python3", os.path.join(userscripts_dir, "cleanup_history_external.py"), str(days)],
                    capture_output=True,
                    text=True,
                    env={**os.environ, "QUTE_DATA_DIR": config.datadir}
                )
                if result.returncode == 0:
                    message.info(result.stdout.strip() if result.stdout else "History cleanup completed")
                else:
                    message.error(f"History cleanup failed: {result.stderr}")
            except Exception as e:
                message.error(f"Failed to run cleanup script: {e}")
    except:
        pass

config.bind(",ch", "history-cleanup")

# Run cleanup automatically on startup
history_cleanup_command(30)

# Get the directory of the *symlink*, not the resolved file
symlink_path = os.path.abspath(__file__)

# Detect profile name based on directory structure and platform
# Linux multi-profile: ~/.config/qutebrowser/profiles/rash/config/config.py
# macOS single-profile: ~/.qutebrowser/config.py
import platform
if platform.system() == "Darwin":
    # macOS single-profile setup - use hostname
    profile_name = socket.gethostname().split('.')[0]
else:
    # Linux multi-profile setup
    profile_path = os.path.dirname(os.path.dirname(symlink_path))
    profile_name = os.path.basename(profile_path)

# === CORE BEHAVIOR ===

# Defaults
c.editor.command = ["wezterm", "start", "--", "nvim", "{}"]

# Start page and homepage
c.url.default_page = "https://startpage.com"
# Windows
c.window.title_format = f"{{current_url}} @ [qute-{profile_name}] "

# Tabs
c.tabs.show = "multiple"
c.tabs.position = "left"
c.tabs.width = "15%"
c.tabs.title.format = "{index}: {current_title}"
c.tabs.select_on_remove = "prev"

# Additional tab styling for better pinned tab distinction
c.tabs.padding = {"left": 5, "right": 5, "top": 3, "bottom": 3}
c.tabs.indicator.width = 2
c.tabs.favicons.scale = 1.2
# Optional: Custom format for pinned tabs to make them more distinct
c.tabs.title.format_pinned = "📌 {audio}{current_title}"

# Autosave session
c.auto_save.session = True
c.session.lazy_restore = True
c.session.default_name = "default"
# Smooth scrolling
c.scrolling.smooth = True
# Download handling
c.downloads.location.directory = "~/downloads"
c.downloads.location.prompt = False
# Notifications
c.content.notifications.enabled = False
# Dark mode (experimental)
c.colors.webpage.darkmode.enabled = True
# Disable mouse wheel tab switch
c.tabs.mousewheel_switching = False

# === PRIVACY & BLOCKING ===

# User agent
config.set(
    "content.headers.user_agent",
    "Mozilla/5.0 ({os_info}; rv:131.0) Gecko/20100101 Firefox/131.0",
    "https://accounts.google.com/*",
)
# Adblock method
c.content.blocking.method = "both"
c.content.blocking.adblock.lists = [
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
    "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/annoyances.txt",
    "https://github.com/uBlockOrigin/uAssets/raw/master/filters/filters.txt",
    "https://github.com/uBlockOrigin/uAssets/raw/master/filters/privacy.txt",
    "https://github.com/uBlockOrigin/uAssets/raw/master/filters/annoyances.txt",
    "https://github.com/uBlockOrigin/uAssets/raw/master/filters/unbreak.txt",
]
# Accept only first-party cookies
c.content.cookies.accept = "no-3rdparty"
# WebRTC IP leakage
c.content.webrtc_ip_handling_policy = "default-public-interface-only"
# Don't load images or JavaScript on unknown sites
c.content.javascript.enabled = True  # set to False for paranoia mode
c.content.images = True

# === UI & THEMING ===

# Font
c.fonts.default_family = "GeistMono Nerd Font"
c.fonts.default_size = "13pt"
# Hint styling
c.hints.chars = "asdfghjklöqweryuopånbvcxz"
c.hints.uppercase = True
c.fonts.hints = "13pt GeistMono Nerd Font"
# This is to prevent several hints from sharing chars.
# False is sequentially (aa,ab,ac...)
c.hints.scatter = True
c.hints.auto_follow = "unique-match"
c.hints.dictionary = "~/.local/share/qutebrowser/words"
c.hints.mode = "letter"
c.colors.hints.bg = "yellow"
c.colors.hints.fg = "black"
c.hints.border = "1px solid #e0af68"
c.hints.padding = {"top": 2, "bottom": 2, "left": 5, "right": 5}
# Color overrides (Tokyo Night Deep vibes)
c.colors.completion.fg = "#c0caf5"
c.colors.completion.even.bg = background
c.colors.completion.odd.bg = background
c.colors.completion.category.bg = "#1f2335"
c.colors.completion.match.fg = "#e0af68"
c.colors.statusbar.normal.bg = background
c.colors.statusbar.command.bg = "#292e42"
c.colors.statusbar.insert.bg = "#9ece6a"
c.colors.statusbar.url.fg = "#7dcfff"
c.colors.webpage.bg = background

# Tab bar background
c.colors.tabs.bar.bg = background
# Regular tabs (unselected)
c.colors.tabs.odd.bg = color16  # Very dark gray background
c.colors.tabs.odd.fg = color7  # Light gray text
c.colors.tabs.even.bg = color0  # Dark gray background
c.colors.tabs.even.fg = color7  # Light gray text
# Regular tabs (selected)
c.colors.tabs.selected.odd.bg = accent  # Bright cyan background
c.colors.tabs.selected.odd.fg = background  # Dark text for contrast
c.colors.tabs.selected.even.bg = accent  # Bright cyan background
c.colors.tabs.selected.even.fg = background  # Dark text for contrast
# Pinned tabs (unselected) - Using purple theme for distinction
c.colors.tabs.pinned.odd.bg = color5  # Purple background
c.colors.tabs.pinned.odd.fg = background  # Dark text for contrast
c.colors.tabs.pinned.even.bg = color5  # Purple background
c.colors.tabs.pinned.even.fg = background  # Dark text for contrast
# Pinned tabs (selected) - Using accent cyan for active pinned tabs
c.colors.tabs.pinned.selected.odd.bg = accent  # Bright cyan background
c.colors.tabs.pinned.selected.odd.fg = background  # Dark text for contrast
c.colors.tabs.pinned.selected.even.bg = accent  # Bright cyan background
c.colors.tabs.pinned.selected.even.fg = background  # Dark text for contrast
# Tab indicators
c.colors.tabs.indicator.start = color4  # Blue gradient start
c.colors.tabs.indicator.stop = color6  # Light cyan gradient end
c.colors.tabs.indicator.error = color1  # Red for errors

# === POWER TOOLS ===

# Block autoplay globally
c.content.autoplay = False
# PDF handling
c.content.pdfjs = True
# Enable clipboard access for hinting
c.content.javascript.clipboard = "access-paste"
# Custom search engines
c.url.searchengines = {
    "DEFAULT": "https://startpage.com/do/dsearch?query={}",
    "g": "https://www.google.com/search?q={}",
    "yt": "https://www.youtube.com/results?search_query={}",
    "nix": "https://search.nixos.org/packages?query={}",
    "hm": "https://search.nixos.org/options?query={}",
    "icons": "https://www.nerdfonts.com/cheat-sheet?q={}",
    "pj": "https://www.prisjakt.nu/search?query={}",
}

# === KEYBINDINGS ===

# Smart HTTPS: default to https unless explicitly http://
from qutebrowser.completion.models import urlmodel

@cmdutils.register()
@cmdutils.argument('win_id', value=cmdutils.Value.win_id)
@cmdutils.argument('url', completion=urlmodel.url)
def open_smart(url: str = "", tab: bool = False, bg: bool = False, private: bool = False, win_id=None):
    """Open URL with smart HTTPS defaulting."""
    from qutebrowser.commands import runners

    # If URL explicitly starts with http://, respect it
    if url.startswith("http://"):
        cmd = "open"
    # If URL starts with https:// or a scheme, use it as-is
    elif url.startswith("https://") or "://" in url:
        cmd = "open"
    # If it looks like a URL (has dots and no spaces), force HTTPS
    elif url and "." in url and " " not in url and not url.startswith("!"):
        cmd = "open -s"
    else:
        # Otherwise, let qutebrowser's auto_search handle it (search query)
        cmd = "open"

    # Add flags
    if private:
        cmd += " -p"
    if bg:
        cmd += " -b"
    elif tab:
        cmd += " -t"

    # Add URL if provided
    if url:
        cmd += f" {url}"

    # Execute the command
    commandrunner = runners.CommandRunner(win_id)
    commandrunner.run_safely(cmd)

# Bind keys to use smart HTTPS
config.bind("o", "cmd-set-text -s :open-smart ")
config.bind("O", "cmd-set-text -s :open-smart --tab ")
config.bind("go", "cmd-set-text :open-smart {url:pretty}")
config.bind("gO", "cmd-set-text :open-smart --tab {url:pretty}")

# Update P to use smart HTTPS for private browsing
config.bind("P", "cmd-set-text -s :open-smart --private ")

# In command mode, Tab appends protocol+domain, Ctrl+Tab appends full current URL
config.bind("<Tab>", "cmd-set-text --append {url:scheme}://{url:host}", mode="command")
config.bind("<Ctrl-Tab>", "cmd-set-text --append {url:pretty}", mode="command")

# Vim-style navigation
config.bind("j", "cmd-repeat 15 scroll down")
config.bind("k", "cmd-repeat 15 scroll up")
config.bind("<Ctrl-j>", "scroll-page 0 1")
config.bind("<Ctrl-k>", "scroll-page 0 -1")
config.bind("<Ctrl-h>", "scroll-page -1 0")
config.bind("<Ctrl-l>", "scroll-page 1 0")
config.bind("J", "tab-next")
config.bind("K", "tab-prev")
config.bind("<Ctrl-Shift-j>", "tab-move +")
config.bind("<Ctrl-Shift-k>", "tab-move -")

# Arrow key navigation (for kanata vim-nav layer)
config.bind("<Down>", "cmd-repeat 15 scroll down")
config.bind("<Up>", "cmd-repeat 15 scroll up")
config.bind("<Left>", "scroll-page -1 0")
config.bind("<Right>", "scroll-page 1 0")
config.bind("<Ctrl-Down>", "scroll-page 0 1")
config.bind("<Ctrl-Up>", "scroll-page 0 -1")
config.bind("<PgDown>", "scroll-page 0 1")
config.bind("<PgUp>", "scroll-page 0 -1")
config.bind("<Home>", "scroll-to-perc 0")
config.bind("<End>", "scroll-to-perc 100")
# mpv integration
config.bind(",m", "spawn --detach mpv {url}")
config.bind(",M", "hint links spawn --detach mpv {hint-url}")
# External editing (e.g., Neovim)
config.bind(",e", "edit-url")
# Yank
config.bind("ys", "yank selection")
config.bind("<Ctrl-c>", "yank selection")
# Toggle dark mode
config.bind(",d", "config-cycle colors.webpage.darkmode.enabled")
# Toggle tab list
config.bind("<Alt-h>", "config-cycle tabs.show never always")
# Duplicate tab
config.bind("D", "tab-clone")
# Unbind existing bindings
config.unbind("pP")
config.unbind("Pp")
config.unbind("PP")

# Reorganize clipboard bindings
config.bind("pp", "open -- {clipboard}")  # clipboard -> current tab
config.bind("pP", "open -t -- {clipboard}")  # clipboard -> new tab

# Add P for prefill private browsing
config.bind("P", "cmd-set-text -s :open -p ")

# Rofi Domain History Browser Bindings
# Ctrl+o: Domain-only history, open in current tab
config.bind("<Ctrl+o>", "spawn --userscript rofi_domain_history.py current")
# Ctrl+Shift+o: Domain-only history, open in new tab
config.bind("<Ctrl+Shift+o>", "spawn --userscript rofi_domain_history.py new")

# = Hint Keybinds =
# Remove defaults
config.unbind(";i")
# General hinting modes
config.bind(";f", "hint --mode=letter all")  # Default letter hints
config.bind(";1", "hint --mode=number all")  # Number mode with text filtering
config.bind(";w", "hint --mode=word all")  # Word mode (human-readable labels)
# Links
config.bind(";ll", "hint links")  # Clickable links
config.bind(";ly", "hint links yank")  # Copy link URL
config.bind(";lt", "hint links tab")  # Open link in new tab
config.bind(";lb", "hint links tab-bg")  # Open in background tab
# Inputs / Forms
config.bind(";ii", "hint inputs")  # Focus input fields
config.bind(";iI", "hint inputs --first")  # Jump to first input
config.bind(";if", "hint inputs fill")  # Fill input with clipboard
# Images
config.bind(";mm", "hint images")  # Select image
config.bind(";mM", "hint images download")  # Download image
config.bind(";mv", "hint images spawn mpv {hint-url}")  # View image in mpv
# Media
config.bind(";v", "hint images spawn --detach mpv {hint-url}")  # Watch video via mpv
# Downloads
config.bind(";D", "hint links download")  # Download linked file
# Example custom hint group (requires c.hints.selectors["your-group"])
# config.bind(";e", "hint reddit-expand")  # e.g. Reddit media expando

# === ALIASES ===

c.aliases["cs"] = "config-source"

# === USERSCRIPTS ===

# Path to scripts
# Note: userscripts are now accessed via "spawn --userscript" which automatically
# looks in the profile's userscripts directory (symlinked to the main one)


# === PER-PROFILE BEHAVIOR ===

if profile_name == "rash":
    c.url.start_pages = "https://www.startpage.com"
    c.content.autoplay = True
    c.content.notifications.enabled = True
    c.content.cookies.accept = "no-3rdparty"
elif profile_name == "jobhunt":
    c.url.start_pages = "https://www.linkedin.com"
    c.content.autoplay = False
    c.content.cookies.accept = "no-3rdparty"
else:
    # Default profile (macOS single-profile setup)
    c.url.start_pages = "https://www.startpage.com"
    c.content.autoplay = True
    c.content.notifications.enabled = True
    c.content.cookies.accept = "no-3rdparty"
