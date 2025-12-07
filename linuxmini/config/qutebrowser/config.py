import os
import sqlite3
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
def cleanup_old_history(days=30):
    """Delete history entries older than specified days."""
    from qutebrowser.api import message

    try:
        # Get the data directory
        data_dir = Path(config.datadir) / "data"
        history_db = data_dir / "history.sqlite"

        if not history_db.exists():
            return

        # Calculate cutoff timestamp (qutebrowser uses milliseconds since epoch)
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_date.timestamp())

        # Connect to database
        conn = sqlite3.connect(str(history_db))
        cursor = conn.cursor()

        # Delete old entries from both tables
        cursor.execute("DELETE FROM History WHERE atime < ?", (cutoff_timestamp,))
        deleted_history = cursor.rowcount

        cursor.execute(
            "DELETE FROM CompletionHistory WHERE last_atime < ?", (cutoff_timestamp,)
        )
        deleted_completion = cursor.rowcount

        conn.commit()
        conn.close()

        if deleted_history > 0 or deleted_completion > 0:
            msg = f"History cleanup: Removed {deleted_history + deleted_completion} entries older than {days} days"
            message.info(msg)

    except Exception as e:
        message.error(f"History cleanup failed: {e}")


# Run cleanup on startup with a slight delay to ensure qutebrowser is fully initialized
from qutebrowser.api import cmdutils

# Only register if not already registered (to handle config reloads)
try:

    @cmdutils.register(name="history-cleanup")
    def history_cleanup_command(days: int = 30):
        """Clean up history entries older than specified days."""
        cleanup_old_history(days)

except:
    pass  # Command already registered, ignore on config reload


# Schedule cleanup to run after startup
from qutebrowser.misc import objects
from PyQt6.QtCore import QTimer


def run_startup_cleanup():
    cleanup_old_history(30)


# Use a timer to run cleanup after qutebrowser is fully loaded
QTimer.singleShot(1000, run_startup_cleanup)
# Get the directory of the *symlink*, not the resolved file
symlink_path = os.path.abspath(__file__)
profile_path = os.path.dirname(os.path.dirname(symlink_path))
profile_name = os.path.basename(profile_path)

# === CORE BEHAVIOR ===

# Defaults
c.editor.command = ["wezterm", "start", "--", "nvim", "{}"]
# Start page and homepage
c.url.start_pages = "https://startpage.com"
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

# Web font families - prevents fallback to weird system fonts
c.fonts.web.family.standard = "sans-serif"
c.fonts.web.family.serif = "serif"
c.fonts.web.family.sans_serif = "sans-serif"
c.fonts.web.family.fixed = "GeistMono Nerd Font"
c.fonts.web.family.cursive = "sans-serif"  # Prevent weird cursive fallback
c.fonts.web.family.fantasy = "sans-serif"  # Prevent weird fantasy fallback
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
    "aur": "https://aur.archlinux.org/packages/?K={}",
    "icons": "https://www.nerdfonts.com/cheat-sheet?q={}",
    "pj": "https://www.prisjakt.nu/search?query={}",
}

# === KEYBINDINGS ===

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
