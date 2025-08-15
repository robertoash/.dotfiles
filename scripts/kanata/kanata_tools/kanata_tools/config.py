"""Configuration for Kanata Tools."""

from pathlib import Path

# Network configuration
KANATA_HOST = "127.0.0.1"
KANATA_PORT = 5829

# File paths
STATUS_FILE = Path("/tmp/kanata_status.json")
STATE_FILE = Path("/tmp/kanata_layer_state.json")
PERSISTENT_STATE_FILE = Path("/home/rash/.config/kanata/last_state.json")
BOOT_TIME_FILE = Path("/tmp/kanata_last_boot_time")
ACTIVE_LAYOUT_FILE = Path("/tmp/active_keyboard_layout")
ESPANSO_CONFIG_FILE = Path("/home/rash/.config/espanso/config/default.yml")

# Layer mappings - adjust these to match your Kanata config
LAYER_NAMES = {
    ("swe", "mod"): "nordic",  # Swedish with home row mods
    ("swe", "nomod"): "nordic_plain",  # Swedish without mods
    ("cmk", "mod"): "colemak",  # Colemak with home row mods
    ("cmk", "nomod"): "colemak_plain",  # Colemak without mods
}

# Reverse mapping from Kanata layer names to our format
LAYER_TO_STATE = {
    "nordic": ("swe", "mod"),
    "nordic_plain": ("swe", "nomod"),
    "colemak": ("cmk", "mod"),
    "colemak_plain": ("cmk", "nomod"),
}

# Espanso configuration mappings
ESPANSO_CONFIG = {
    "swe": {
        "layout": "se",
        "variant": "nodeadkeys",
        "model": "pc105",
    },
    "cmk": {
        "layout": "se",
        "variant": "nodeadkeys",
        "model": "pc105",
    },
}

# Status display mappings with Pango markup for multi-colored text
STATUS_CONFIG = {
    ("swe", "mod"): {
        "text": (
            '<span color="#ffffff">SWE</span>'
            '<span color="#ffffff">-</span>'
            '<span color="#ffffff">MOD</span>'
        ),
        "class": "normal",
        "tooltip": "Kanata: Swedish with home row mods",
    },
    ("swe", "nomod"): {
        "text": (
            '<span color="#ffffff">SWE</span>'
            '<span color="#ffffff">-</span>'
            '<span color="#ff0000">NOMOD</span>'
        ),
        "class": "plain",
        "tooltip": "Kanata: Swedish without mods",
    },
    ("cmk", "mod"): {
        "text": (
            '<span color="#a855f7">CMK</span>'
            '<span color="#ffffff">-</span>'
            '<span color="#ffffff">MOD</span>'
        ),
        "class": "colemak",
        "tooltip": "Kanata: Colemak with home row mods",
    },
    ("cmk", "nomod"): {
        "text": (
            '<span color="#a855f7">CMK</span>'
            '<span color="#ffffff">-</span>'
            '<span color="#ff0000">NOMOD</span>'
        ),
        "class": "colemak-plain",
        "tooltip": "Kanata: Colemak without mods",
    },
}

# Default state after reboot
DEFAULT_STATE = {
    "layout": "swe",
    "mod_state": "mod"
}