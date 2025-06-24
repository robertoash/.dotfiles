import os

config.load_autoconfig()
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
# Tabs and windows
c.tabs.show = "multiple"
c.tabs.position = "left"
c.tabs.width = "15%"
c.tabs.title.format = "{index}: {current_title}"
c.window.title_format = f"{{current_url}} @ [qute-{profile_name}] "
# Autosave session
c.auto_save.session = True
c.session.lazy_restore = False
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
config.bind("<Alt-h>", "config-cycle tabs.show always never")
# Duplicate tab
config.bind("D", "tab-clone")

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

PASTE_DELAY = 500
rofi_dcli_script = "/home/rash/.config/scripts/qutebrowser/rofi_dcli.py"
run_with_paste_script = "/home/rash/.config/qutebrowser/userscripts/run_with_paste.py"

# = Rofi password manager
run_with_paste_cmd = f"spawn --userscript run_with_paste.py --script {rofi_dcli_script} --paste-delay {PASTE_DELAY}"

config.bind("<Alt-p>u", f"{run_with_paste_cmd} username", mode="insert")
config.bind("<Alt-p>p", f"{run_with_paste_cmd} password", mode="insert")
config.bind("<Alt-p>o", f"{run_with_paste_cmd} otp", mode="insert")

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

# === PER-SITE HINT CUSTOMIZATION ===

# hint_mapping = {
#     "https://mail.google.com/*": {
#         "hints.mode": "word",
#         "colors.hints.bg": "yellow",
#         "colors.hints.fg": "black",
#     },
#     "https://*.linkedin.com/*": {
#         "hints.mode": "number",
#         "colors.hints.bg": "yellow",
#         "colors.hints.fg": "black",
#     },
# }
#
# for domain, settings in hint_mapping.items():
#     for setting, value in settings.items():
#         config.set(setting, value, domain)
