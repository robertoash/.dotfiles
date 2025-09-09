"""Status listener daemon for Kanata layer changes."""

import json
import logging
import socket
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from .config import (
    ACTIVE_LAYOUT_FILE,
    KANATA_HOST,
    KANATA_PORT,
    LAYER_TO_STATE,
    STATUS_CONFIG,
    STATUS_FILE,
)
from .state_manager import StateManager


class KanataStatusListener:
    """Listens to Kanata's TCP server for layer changes."""
    
    def __init__(self):
        self.setup_logging()
        self.current_layout = "qwe"
        self.current_mod_state = "base"
        self.state_manager = StateManager(self.logger)
    
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
        """Parse LayerChange message and return (layout, mod_state) tuple."""
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
        """Update both status files based on current state."""
        try:
            # Update waybar status file
            key = (layout, mod_state)
            status = STATUS_CONFIG[key]
            with open(STATUS_FILE, "w") as f:
                json.dump(status, f)
            
            # Update active keyboard layout file
            with open(ACTIVE_LAYOUT_FILE, "w") as f:
                f.write(layout)
            
            # Save persistent state
            self.state_manager.save_persistent_state(layout, mod_state)
            
        except Exception as e:
            self.logger.error(f"Failed to update status files: {e}")
    
    def connect_to_kanata(self) -> Optional[socket.socket]:
        """Connect to Kanata TCP server."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((KANATA_HOST, KANATA_PORT))
            self.logger.info(f"Connected to Kanata TCP server at {KANATA_HOST}:{KANATA_PORT}")
            return sock
        except Exception as e:
            self.logger.error(f"Failed to connect to Kanata TCP server: {e}")
            return None
    
    def listen_for_messages(self):
        """Main listening loop."""
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
                                        self.logger.info(
                                            f"Layer changed: {self.current_layout}-{self.current_mod_state} "
                                            f"→ {layout}-{mod_state}"
                                        )
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
    
    def run(self):
        """Run the status listener daemon."""
        try:
            self.logger.info("Starting Kanata status listener daemon...")
            self.listen_for_messages()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            sys.exit(1)