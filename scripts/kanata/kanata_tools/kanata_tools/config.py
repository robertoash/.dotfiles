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

# Layer mappings - simplified for new config (no home row mods in base layers)
LAYER_NAMES = {
    ("cmk", "base"): "colemak",  # Colemak (default)
    ("qwe", "base"): "qwerty",   # QWERTY
}

# Reverse mapping from Kanata layer names to our format
LAYER_TO_STATE = {
    "colemak": ("cmk", "base"),
    "qwerty": ("qwe", "base"),
}

# Espanso configuration mappings
ESPANSO_CONFIG = {
    "qwe": {
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
    ("cmk", "base"): {
        "text": '<span color="#a855f7">COLEMAK</span>',
        "class": "colemak",
        "tooltip": "Kanata: Colemak layout",
    },
    ("qwe", "base"): {
        "text": '<span color="#ffffff">QWERTY</span>',
        "class": "qwerty",
        "tooltip": "Kanata: QWERTY layout",
    },
}

# Default state after reboot (Colemak as default)
DEFAULT_STATE = {
    "layout": "cmk",
    "mod_state": "base"
}