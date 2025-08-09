#!/usr/bin/env python3
"""
Kanata Status Listener Daemon

Listens to Kanata's TCP server for LayerChange messages and automatically
writes the correct status files for waybar and other tools to consume.

This eliminates the need for state management in the layer switcher script
and ensures the status files always reflect Kanata's actual current state.
"""

import json
import logging
import socket
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

# Configuration
KANATA_HOST = "127.0.0.1"
KANATA_PORT = 5829
STATUS_FILE = Path("/tmp/kanata_status.json")
ACTIVE_LAYOUT_FILE = Path("/tmp/active_keyboard_layout")

# Reverse mapping from Kanata layer names to our format
LAYER_TO_STATE = {
    "nordic": ("swe", "mod"),         # Swedish with home row mods
    "nordic_plain": ("swe", "nomod"), # Swedish without mods  
    "colemak": ("cmk", "mod"),        # Colemak with home row mods
    "colemak_plain": ("cmk", "nomod"), # Colemak without mods
}

# Status display mappings with Pango markup
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

class KanataStatusListener:
    def __init__(self):
        self.setup_logging()
        self.current_layout = "swe"
        self.current_mod_state = "mod"
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("/tmp/kanata_status_listener.log")
            ]
        )
        self.logger = logging.getLogger("KanataStatusListener")
        
    def parse_layer_change(self, message: dict) -> Optional[Tuple[str, str]]:
        """Parse LayerChange message and return (layout, mod_state) tuple"""
        try:
            if "LayerChange" in message and "new" in message["LayerChange"]:
                layer_name = message["LayerChange"]["new"]
                if layer_name in LAYER_TO_STATE:
                    return LAYER_TO_STATE[layer_name]
                else:
                    self.logger.warning(f"Unknown layer name: {layer_name}")
                    return None
            return None
        except Exception as e:
            self.logger.error(f"Failed to parse LayerChange message: {e}")
            return None
            
    def update_status_files(self, layout: str, mod_state: str):
        """Update both status files based on current state"""
        try:
            # Update waybar status file
            key = (layout, mod_state)
            status = STATUS_CONFIG[key]
            with open(STATUS_FILE, "w") as f:
                json.dump(status, f)
                
            # Update active keyboard layout file
            with open(ACTIVE_LAYOUT_FILE, "w") as f:
                f.write(layout)
                
            
        except Exception as e:
            self.logger.error(f"Failed to update status files: {e}")
            
    def connect_to_kanata(self) -> Optional[socket.socket]:
        """Connect to Kanata TCP server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((KANATA_HOST, KANATA_PORT))
            self.logger.info(f"Connected to Kanata TCP server at {KANATA_HOST}:{KANATA_PORT}")
            return sock
        except Exception as e:
            self.logger.error(f"Failed to connect to Kanata TCP server: {e}")
            return None
            
    def listen_for_messages(self):
        """Main listening loop"""
        while True:
            sock = self.connect_to_kanata()
            if not sock:
                self.logger.error("Could not connect to Kanata, retrying in 5 seconds...")
                time.sleep(5)
                continue
                
            # Write initial state immediately upon successful connection
            self.update_status_files(self.current_layout, self.current_mod_state)
            self.logger.info(f"Initialized with default state: {self.current_layout}-{self.current_mod_state}")
                
            try:
                # Set up for receiving messages
                buffer = ""
                
                while True:
                    data = sock.recv(1024).decode('utf-8')
                    if not data:
                        self.logger.warning("Connection closed by Kanata")
                        break
                        
                    buffer += data
                    
                    # Process complete JSON messages (one per line)
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            try:
                                message = json.loads(line)
                                
                                # Parse layer change
                                state = self.parse_layer_change(message)
                                if state:
                                    layout, mod_state = state
                                    if layout != self.current_layout or mod_state != self.current_mod_state:
                                        self.logger.info(f"Layer changed: {self.current_layout}-{self.current_mod_state} → {layout}-{mod_state}")
                                        self.current_layout = layout
                                        self.current_mod_state = mod_state
                                        self.update_status_files(layout, mod_state)
                                        
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Invalid JSON received: {line} - {e}")
                                
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                
            finally:
                if sock:
                    sock.close()
                    
            # Reconnect after a delay
            self.logger.info("Reconnecting in 5 seconds...")
            time.sleep(5)

def main():
    listener = KanataStatusListener()
    
    try:
        listener.logger.info("Starting Kanata status listener daemon...")
        listener.listen_for_messages()
    except KeyboardInterrupt:
        listener.logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        listener.logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()