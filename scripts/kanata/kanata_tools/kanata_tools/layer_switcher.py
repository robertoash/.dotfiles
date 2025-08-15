"""Layer switching functionality for Kanata."""

import json
import logging
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

from .config import (
    ACTIVE_LAYOUT_FILE,
    ESPANSO_CONFIG,
    ESPANSO_CONFIG_FILE,
    KANATA_HOST,
    KANATA_PORT,
    LAYER_NAMES,
    STATE_FILE,
    STATUS_CONFIG,
    STATUS_FILE,
)
from .state_manager import StateManager


class KanataLayerSwitcher:
    """Handles layer switching and state management for Kanata."""
    
    def __init__(self):
        self.current_layout = "swe"
        self.current_mod_state = "mod"
        self.setup_logging()
        self.state_manager = StateManager(self.logger)
        self.load_state()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
    
    def load_state(self):
        """Load current state from file, or use defaults."""
        try:
            # First try temp state file
            state = self.state_manager.load_temp_state()
            if state:
                self.current_layout = state.get("layout", "swe")
                self.current_mod_state = state.get("mod_state", "mod")
                self.logger.info(f"Loaded state: {self.current_layout}-{self.current_mod_state}")
            else:
                # Fallback to active layout file
                try:
                    if ACTIVE_LAYOUT_FILE.exists():
                        layout_content = ACTIVE_LAYOUT_FILE.read_text().strip()
                        if layout_content in ["swe", "cmk"]:
                            self.current_layout = layout_content
                            self.logger.info(f"Using layout from active_keyboard_layout: {self.current_layout}-mod")
                    else:
                        self.logger.info("No state file found, using defaults: swe-mod")
                except Exception as e:
                    self.logger.warning(f"Failed to read active_keyboard_layout: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to load state: {e}. Using defaults.")
    
    def save_state(self):
        """Save current state to both temp and persistent storage."""
        self.state_manager.save_temp_state(self.current_layout, self.current_mod_state)
        self.state_manager.save_persistent_state(self.current_layout, self.current_mod_state)
    
    def update_status_file(self):
        """Update the status file for waybar/other displays."""
        try:
            key = (self.current_layout, self.current_mod_state)
            status = STATUS_CONFIG[key]
            with open(STATUS_FILE, "w") as f:
                json.dump(status, f)
            self.logger.info(f"Updated status to: {self.current_layout}-{self.current_mod_state}")
        except Exception as e:
            self.logger.error(f"Failed to update status file: {e}")
    
    def write_active_layout(self):
        """Write current layout to /tmp/active_keyboard_layout."""
        try:
            with open(ACTIVE_LAYOUT_FILE, "w") as f:
                f.write(self.current_layout)
            self.logger.info(f"Updated active layout file to: {self.current_layout}")
        except Exception as e:
            self.logger.error(f"Failed to write active layout file: {e}")
    
    def update_espanso_config(self):
        """Update espanso configuration based on current layout."""
        try:
            new_config = ESPANSO_CONFIG[self.current_layout]
            
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
            
            subprocess.run(["espanso", "restart"], check=False, capture_output=True)
            
            self.logger.info(f"Updated espanso config to {self.current_layout} layout")
            
        except Exception as e:
            self.logger.error(f"Failed to update espanso config: {e}")
    
    def connect_to_kanata(self, retries: int = 2) -> Optional[socket.socket]:
        """Establish TCP connection to Kanata with retry logic."""
        for attempt in range(retries + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                sock.connect((KANATA_HOST, KANATA_PORT))
                self.logger.info(f"Connected to Kanata on {KANATA_HOST}:{KANATA_PORT}")
                return sock
            except Exception as e:
                if attempt < retries:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(0.5)
                else:
                    self.logger.error(f"Failed to connect to Kanata after {retries + 1} attempts: {e}")
        return None
    
    def send_layer_change(self, layer_name: str) -> bool:
        """Send layer change command to Kanata."""
        sock = self.connect_to_kanata()
        if not sock:
            return False
        
        try:
            message = {"ChangeLayer": {"new": layer_name}}
            message_json = json.dumps(message) + "\n"
            sock.send(message_json.encode("utf-8"))
            self.logger.info(f"Sent layer change to: {layer_name}")
            time.sleep(0.1)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send layer change: {e}")
            return False
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except (OSError, socket.error):
                pass
            sock.close()
    
    def switch_layout(self):
        """Switch between Swedish and Colemak layouts."""
        self.current_layout = "cmk" if self.current_layout == "swe" else "swe"
        
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
        """Toggle between mod and nomod states."""
        self.current_mod_state = "nomod" if self.current_mod_state == "mod" else "mod"
        
        key = (self.current_layout, self.current_mod_state)
        layer_name = LAYER_NAMES[key]
        
        self.logger.info(f"Toggling mod state to: {self.current_mod_state}")
        
        if self.send_layer_change(layer_name):
            self.save_state()
            self.update_status_file()
        else:
            # Revert on failure
            self.current_mod_state = "nomod" if self.current_mod_state == "mod" else "mod"
    
    def set_specific_layer(self, layout: str, mod_state: str) -> bool:
        """Set specific layer combination."""
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
    
    def initialize_on_start(self) -> bool:
        """Initialize Kanata with appropriate state based on reboot detection."""
        state = self.state_manager.get_initial_state()
        
        self.current_layout = state["layout"]
        self.current_mod_state = state["mod_state"]
        
        key = (self.current_layout, self.current_mod_state)
        layer_name = LAYER_NAMES[key]
        
        if self.send_layer_change(layer_name):
            self.save_state()
            self.update_status_file()
            self.write_active_layout()
            self.update_espanso_config()
            self.logger.info(f"Successfully initialized to {self.current_layout}-{self.current_mod_state}")
            return True
        else:
            self.logger.error(f"Failed to initialize to {self.current_layout}-{self.current_mod_state}")
            return False
    
    def get_current_state(self) -> Tuple[str, str]:
        """Get current layout and mod state."""
        return self.current_layout, self.current_mod_state