#!/usr/bin/env python3
"""
Kanata Layer Switcher Client

Connects to Kanata TCP server to switch between keyboard layouts and mod states.
Supports 4 states: SWE-MOD, SWE-NOMOD, CMK-MOD, CMK-NOMOD

Key bindings (to be configured in Hyprland):
- Hypr+å: Cycle between Swedish (SWE) and Colemak (CMK) layouts
- Hypr+ä: Toggle between MOD and NOMOD states

Usage:
    python kanata_layer_switcher.py --action layout    # Switch layout (SWE ↔ CMK)
    python kanata_layer_switcher.py --action mod       # Toggle mod state (MOD ↔ NOMOD)
    python kanata_layer_switcher.py --daemon           # Run as daemon (listens for TCP messages)
"""

import argparse
import json
import logging
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Configuration
KANATA_PORT = 5829
KANATA_HOST = "127.0.0.1"
STATUS_FILE = Path("/tmp/kanata_status.json")
STATE_FILE = Path("/tmp/kanata_layer_state.json")
ESPANSO_CONFIG_FILE = Path("/home/rash/.config/espanso/config/default.yml")

# Layer mappings - adjust these to match your Kanata config
LAYER_NAMES = {
    ("swe", "mod"): "nordic",  # Swedish with home row mods
    ("swe", "nomod"): "nordic_plain",  # Swedish without mods
    ("cmk", "mod"): "colemak",  # Colemak with home row mods
    ("cmk", "nomod"): "colemak_plain",  # Colemak without mods
}

# Espanso configuration mappings
# Note: espanso should always use nodeadkeys since kanata handles the colemak remapping
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


class KanataLayerSwitcher:
    def __init__(self):
        self.current_layout = "cmk"  # swe or cmk - this affects Kanata layer
        self.current_mod_state = "mod"  # mod or nomod
        self.setup_logging()
        self.load_state()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def load_state(self):
        """Load current state from file, or use defaults"""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                    self.current_layout = state.get("layout", "cmk")
                    self.current_mod_state = state.get("mod_state", "mod")
                    self.logger.info(
                        f"Loaded state: {self.current_layout}-{self.current_mod_state}"
                    )
            else:
                self.logger.info("No state file found, using defaults: cmk-mod")
        except Exception as e:
            self.logger.warning(f"Failed to load state: {e}. Using defaults.")

    def save_state(self):
        """Save current state to file"""
        try:
            state = {
                "layout": self.current_layout,
                "mod_state": self.current_mod_state,
            }
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def update_status_file(self):
        """Update the status file for waybar/other displays"""
        try:
            key = (self.current_layout, self.current_mod_state)
            status = STATUS_CONFIG[key]
            with open(STATUS_FILE, "w") as f:
                json.dump(status, f)
            self.logger.info(f"Updated status to: {status['text']}")
        except Exception as e:
            self.logger.error(f"Failed to update status file: {e}")

    def write_active_layout(self):
        """Write current layout to /tmp/active_keyboard_layout"""
        try:
            # Write to main status file
            with open("/tmp/active_keyboard_layout", "w") as f:
                f.write(self.current_layout)
            self.logger.info(f"Updated active layout file to: {self.current_layout}")
        except Exception as e:
            self.logger.error(f"Failed to write active layout file: {e}")

    def update_espanso_config(self):
        """Update espanso configuration based on current layout"""
        try:
            # Get new keyboard layout config
            new_config = ESPANSO_CONFIG[self.current_layout]
            
            # Update espanso config using sed
            subprocess.run([
                "sed", "-i",
                f"s/^  layout: .*/  layout: {new_config['layout']}/",
                str(ESPANSO_CONFIG_FILE)
            ], check=True)
            
            subprocess.run([
                "sed", "-i", 
                f"s/^  variant: .*/  variant: {new_config['variant']}/",
                str(ESPANSO_CONFIG_FILE)
            ], check=True)
            
            # Restart espanso to apply changes
            subprocess.run(["espanso", "restart"], check=False, capture_output=True)
            
            self.logger.info(f"Updated espanso config to {self.current_layout} layout")
            
        except Exception as e:
            self.logger.error(f"Failed to update espanso config: {e}")

    def connect_to_kanata(self, retries: int = 2) -> Optional[socket.socket]:
        """Establish TCP connection to Kanata with retry logic"""
        for attempt in range(retries + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)  # Shorter timeout to fail faster
                sock.connect((KANATA_HOST, KANATA_PORT))
                self.logger.info(f"Connected to Kanata on {KANATA_HOST}:{KANATA_PORT}")
                return sock
            except Exception as e:
                if attempt < retries:
                    self.logger.warning(
                        f"Connection attempt {attempt + 1} failed: {e}, retrying..."
                    )
                    import time

                    time.sleep(0.5)  # Brief delay before retry
                else:
                    self.logger.error(
                        f"Failed to connect to Kanata after {retries + 1} attempts: {e}"
                    )
                    if sock:
                        sock.close()
        return None

    def send_layer_change(self, layer_name: str) -> bool:
        """Send layer change command to Kanata"""
        sock = self.connect_to_kanata()
        if not sock:
            return False

        try:
            message = {"ChangeLayer": {"new": layer_name}}
            message_json = json.dumps(message) + "\n"
            sock.send(message_json.encode("utf-8"))
            self.logger.info(f"Sent layer change to: {layer_name}")

            # Give a small delay to ensure the message is processed
            import time

            time.sleep(0.1)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send layer change: {e}")
            return False
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)  # Proper connection shutdown
            except (OSError, socket.error):
                pass  # Ignore errors during shutdown (socket might already be closed)
            sock.close()

    def switch_layout(self):
        """Switch between Swedish and Colemak layouts"""
        # Cycle layout: swe -> cmk -> swe
        self.current_layout = "cmk" if self.current_layout == "swe" else "swe"

        # Get the layer name for the new state
        key = (self.current_layout, self.current_mod_state)
        layer_name = LAYER_NAMES[key]

        self.logger.info(f"Switching layout to: {self.current_layout}")

        if self.send_layer_change(layer_name):
            self.save_state()
            self.update_status_file()
            self.write_active_layout()
            self.update_espanso_config()
        else:
            # Revert on failure
            self.current_layout = "cmk" if self.current_layout == "swe" else "swe"

    def toggle_mod_state(self):
        """Toggle between mod and nomod states"""
        # Toggle mod state: mod -> nomod -> mod
        self.current_mod_state = "nomod" if self.current_mod_state == "mod" else "mod"

        # Get the layer name for the new state
        key = (self.current_layout, self.current_mod_state)
        layer_name = LAYER_NAMES[key]

        self.logger.info(f"Toggling mod state to: {self.current_mod_state}")

        if self.send_layer_change(layer_name):
            self.save_state()
            self.update_status_file()
        else:
            # Revert on failure
            self.current_mod_state = (
                "nomod" if self.current_mod_state == "mod" else "mod"
            )

    def get_current_state(self) -> Tuple[str, str]:
        """Get current layout and mod state"""
        return self.current_layout, self.current_mod_state

    def set_specific_layer(self, layout: str, mod_state: str):
        """Set specific layer combination"""
        if layout not in ["swe", "cmk"] or mod_state not in ["mod", "nomod"]:
            self.logger.error(f"Invalid layer combination: {layout}-{mod_state}")
            return False

        self.current_layout = layout
        self.current_mod_state = mod_state

        key = (layout, mod_state)
        layer_name = LAYER_NAMES[key]

        self.logger.info(f"Setting layer to: {layout}-{mod_state}")

        if self.send_layer_change(layer_name):
            self.save_state()
            self.update_status_file()
            self.write_active_layout()
            self.update_espanso_config()
            return True
        else:
            return False

    def fresh_start(self):
        """Initialize to default SWE-MOD state, useful for boot/startup"""
        self.logger.info("Initializing to default SWE-MOD state")

        # Set to CMK-MOD (Colemak with home row mods)
        self.current_layout = "cmk"
        self.current_mod_state = "mod"

        # Get the layer name and send to Kanata
        key = (self.current_layout, self.current_mod_state)
        layer_name = LAYER_NAMES[key]

        if self.send_layer_change(layer_name):
            self.save_state()
            self.update_status_file()
            self.write_active_layout()
            self.update_espanso_config()
            self.logger.info("Successfully initialized to SWE-MOD state")
            return True
        else:
            self.logger.error("Failed to initialize to SWE-MOD state")
            return False


def main():
    parser = argparse.ArgumentParser(description="Kanata Layer Switcher Client")
    parser.add_argument(
        "--action",
        choices=["layout", "mod", "status", "waybar", "toggle"],
        help="Action to perform: layout (switch layout), mod (toggle mod state), "
        "status (show current), waybar (status with fallback), toggle (mod for waybar click)",
    )
    parser.add_argument(
        "--set-layer",
        metavar="LAYOUT",
        choices=["swe", "cmk"],
        help="Set specific layout (swe or cmk)",
    )
    parser.add_argument(
        "--set-mod",
        metavar="MOD_STATE",
        choices=["mod", "nomod"],
        help="Set specific mod state (mod or nomod)",
    )
    parser.add_argument(
        "--fresh-start",
        action="store_true",
        help="Initialize to default SWE-MOD state (useful for boot/startup)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (not implemented yet)",
    )

    args = parser.parse_args()

    switcher = KanataLayerSwitcher()

    if args.action == "layout":
        switcher.switch_layout()
    elif args.action == "mod":
        switcher.toggle_mod_state()
    elif args.action == "status":
        layout, mod_state = switcher.get_current_state()
        key = (layout, mod_state)
        status = STATUS_CONFIG[key]
        print(json.dumps(status))
    elif args.action == "waybar":
        # Waybar-optimized status with fallback for when Kanata is not running
        # Suppress all stderr output for waybar
        import os
        stderr_fd = os.dup(2)  # Save stderr
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)  # Redirect stderr to /dev/null
        
        try:
            layout, mod_state = switcher.get_current_state()
            key = (layout, mod_state)
            status = STATUS_CONFIG[key]
        except Exception:
            # Fallback when Kanata/TCP is not available
            status = {
                "text": '<span color="#ffffff">NORM</span>',
                "class": "normal",
                "tooltip": "Kanata: Nordic mode (home row mods active)",
            }
        finally:
            # Restore stderr
            os.dup2(stderr_fd, 2)
            os.close(devnull)
            os.close(stderr_fd)
        
        print(json.dumps(status))
    elif args.action == "toggle":
        # Toggle mod state - useful for waybar click
        switcher.toggle_mod_state()
    elif args.fresh_start:
        # Initialize to default SWE-MOD state
        if not switcher.fresh_start():
            sys.exit(1)
    elif args.set_layer and args.set_mod:
        switcher.set_specific_layer(args.set_layer, args.set_mod)
    elif args.daemon:
        print("Daemon mode not implemented yet")
        sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
