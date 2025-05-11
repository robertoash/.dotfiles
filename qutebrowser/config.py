import os

# This just quiets the linter errors
try:
    config  # type: ignore
except NameError:
    from types import SimpleNamespace

    config = SimpleNamespace(bind=lambda *a, **k: None, load_autoconfig=lambda: None)
    c = SimpleNamespace()


# Load default settings first
config.load_autoconfig()

# Retrieve the base directory from the environment variable
profile_path = os.environ.get("QUTE_BASEDIR", "")

# Extract the profile name from the base directory path
profile_name = os.path.basename(profile_path)


# === 1. CORE BEHAVIOR ===

# Start page and homepage
c.url.start_pages = "https://startpage.com"
c.url.default_page = "https://startpage.com"

# Tabs and windows
c.tabs.show = "multiple"
c.tabs.position = "left"
c.tabs.width = "15%"
c.tabs.title.format = "{index}: {current_title}"

# Smooth scrolling
c.scrolling.smooth = True

# Download handling
c.downloads.location.directory = "~/downloads"
c.downloads.location.prompt = False

# Notifications
c.content.notifications.enabled = False

# Dark mode (experimental)
c.colors.webpage.darkmode.enabled = True

# === 2. PRIVACY & BLOCKING ===

# Adblock method
c.content.blocking.method = "both"
c.content.blocking.adblock.lists = [
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
    "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/annoyances.txt",
]

# Accept only first-party cookies
c.content.cookies.accept = "no-3rdparty"

# WebRTC IP leakage
c.content.webrtc_ip_handling_policy = "default-public-interface-only"

# Don't load images or JavaScript on unknown sites
c.content.javascript.enabled = True  # set to False for paranoia mode
c.content.images = True

# === 3. UI & THEMING ===

# Font
c.fonts.default_family = "FiraCode Nerd Font"
c.fonts.default_size = "10pt"

# Hint styling
c.hints.border = "1px solid #e0af68"
c.hints.padding = {"top": 2, "bottom": 2, "left": 5, "right": 5}

# Color overrides (Tokyo Night Deep vibes)
c.colors.completion.fg = "#c0caf5"
c.colors.completion.even.bg = "#1a1b26"
c.colors.completion.odd.bg = "#1a1b26"
c.colors.completion.category.bg = "#1f2335"
c.colors.completion.match.fg = "#e0af68"
c.colors.statusbar.normal.bg = "#1a1b26"
c.colors.statusbar.command.bg = "#292e42"
c.colors.statusbar.insert.bg = "#9ece6a"
c.colors.statusbar.url.fg = "#7dcfff"
c.colors.tabs.bar.bg = "#1a1b26"
c.colors.tabs.odd.bg = "#1a1b26"
c.colors.tabs.even.bg = "#1a1b26"
c.colors.tabs.selected.odd.bg = "#7aa2f7"
c.colors.tabs.selected.even.bg = "#7aa2f7"
c.colors.webpage.bg = "#1a1b26"

# === 4. KEYBINDINGS ===

# Vim-style navigation
config.bind("J", "tab-prev")
config.bind("K", "tab-next")
config.bind("<Ctrl-j>", "scroll-page 0 0.5")
config.bind("<Ctrl-k>", "scroll-page 0 -0.5")
config.bind("<Ctrl-h>", "scroll-page -0.5 0")
config.bind("<Ctrl-l>", "scroll-page 0.5 0")

# mpv integration
config.bind(",m", "spawn --detach mpv {url}")
config.bind(",M", "hint links spawn --detach mpv {hint-url}")

# External editing (e.g., Neovim)
config.bind(",e", "edit-url")

# Yank current URL/title
config.bind(",y", "yank")
config.bind(",Y", "yank title")

# Open URL from clipboard
config.bind(",p", "open -- {clipboard}")

# Toggle dark mode
config.bind(",d", "config-cycle colors.webpage.darkmode.enabled")

# Paste & go
config.bind("P", "open -- {primary}")

# Close tab fast
config.bind("x", "tab-close")

# === 5. PER-PROFILE BEHAVIOR ===

if profile_name == "rash":
    c.url.start_pages = "https://www.reddit.com"
    c.content.autoplay = True
    c.content.notifications.enabled = True
    c.tabs.title.format = "[rash] {index}: {title}"

elif profile_name == "jobhunt":
    c.url.start_pages = "https://www.linkedin.com"
    c.content.autoplay = False
    c.content.cookies.accept = "no-3rdparty"
    c.tabs.title.format = "[jobhunt] {index}: {title}"
    c.content.headers.user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

# === 6. POWER TOOLS ===

# Block autoplay globally
c.content.autoplay = False

# PDF handling
c.content.pdfjs = True

# Enable clipboard access for hinting
c.content.javascript.clipboard = "access-paste"

# Custom search engines
c.url.searchengines = {
    "DEFAULT": "https://startpage.com/?q={}",
    "g": "https://www.google.com/search?q={}",
    "gh": "https://github.com/search?q={}",
    "yt": "https://www.youtube.com/results?search_query={}",
    "aur": "https://aur.archlinux.org/packages/?K={}",
}
