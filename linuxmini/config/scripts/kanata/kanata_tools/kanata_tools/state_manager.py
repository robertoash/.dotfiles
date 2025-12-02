"""State persistence and reboot detection for Kanata."""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from .config import (
    BOOT_TIME_FILE,
    DEFAULT_STATE,
    PERSISTENT_STATE_FILE,
    STATE_FILE,
)


class StateManager:
    """Manages Kanata state persistence and reboot detection."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
    def get_system_boot_time(self) -> float:
        """Get system boot time in seconds since epoch."""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])
            boot_time = time.time() - uptime_seconds
            return boot_time
        except Exception as e:
            self.logger.error(f"Failed to get system boot time: {e}")
            return time.time()
    
    def detect_reboot(self) -> bool:
        """
        Detect if this is a fresh boot or just a keyboard reconnect.
        Returns True if it's a reboot, False if it's a reconnect.
        """
        current_boot_time = self.get_system_boot_time()
        
        if BOOT_TIME_FILE.exists():
            try:
                with open(BOOT_TIME_FILE, "r") as f:
                    last_boot_time = float(f.read().strip())
                
                # If boot times differ by more than 60 seconds, it's a new boot
                time_diff = abs(current_boot_time - last_boot_time)
                is_reboot = time_diff > 60
                
                if is_reboot:
                    self.logger.info(f"Detected system reboot (boot time diff: {time_diff:.1f}s)")
                else:
                    self.logger.info(f"Detected keyboard reconnect (boot time diff: {time_diff:.1f}s)")
                    
            except Exception as e:
                self.logger.warning(f"Failed to read last boot time: {e}")
                is_reboot = True
        else:
            self.logger.info("No previous boot time found, treating as fresh boot")
            is_reboot = True
        
        # Update boot time file
        try:
            BOOT_TIME_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BOOT_TIME_FILE, "w") as f:
                f.write(str(current_boot_time))
        except Exception as e:
            self.logger.error(f"Failed to write boot time: {e}")
        
        return is_reboot
    
    def save_persistent_state(self, layout: str, mod_state: str):
        """Save state to persistent storage."""
        try:
            state = {"layout": layout, "mod_state": mod_state}
            PERSISTENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PERSISTENT_STATE_FILE, "w") as f:
                json.dump(state, f)
            self.logger.debug(f"Saved persistent state: {state}")
        except Exception as e:
            self.logger.error(f"Failed to save persistent state: {e}")
    
    def load_persistent_state(self) -> Optional[dict]:
        """Load state from persistent storage."""
        try:
            if PERSISTENT_STATE_FILE.exists():
                with open(PERSISTENT_STATE_FILE, "r") as f:
                    state = json.load(f)
                self.logger.debug(f"Loaded persistent state: {state}")
                return state
        except Exception as e:
            self.logger.error(f"Failed to load persistent state: {e}")
        return None
    
    def save_temp_state(self, layout: str, mod_state: str):
        """Save current state to temp file."""
        try:
            state = {"layout": layout, "mod_state": mod_state}
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            self.logger.error(f"Failed to save temp state: {e}")
    
    def load_temp_state(self) -> Optional[dict]:
        """Load current state from temp file."""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load temp state: {e}")
        return None
    
    def get_initial_state(self) -> dict:
        """
        Determine initial state based on reboot detection.
        Returns the state that should be applied on Kanata start.
        """
        is_reboot = self.detect_reboot()
        
        if is_reboot:
            self.logger.info("System rebooted - using default state")
            return DEFAULT_STATE
        else:
            # Try to restore last persistent state
            state = self.load_persistent_state()
            if state:
                self.logger.info(f"Keyboard reconnected - restoring state: {state}")
                return state
            else:
                self.logger.info("No persistent state found - using default")
                return DEFAULT_STATE