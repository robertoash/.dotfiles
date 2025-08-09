#!/usr/bin/env python3
"""
Hyprland Keybind Translation Script
Translates keybinds between Swedish (swe) and Colemak (cmk) layouts
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

# Configuration
SOURCE_CONFIG = Path.home() / ".config" / "hypr" / "keybinds_source.conf"
TARGET_CONFIG = Path.home() / ".config" / "hypr" / "active_keybinds.conf"
LAYOUT_FILE = Path("/tmp/active_keyboard_layout")
LAST_LAYOUT_FILE = Path("/tmp/last_translated_layout")

# Swedish (swe) to Colemak (cmk) key mapping
SWEDISH_TO_COLEMAK = {
    # Comprehensive mapping based on your exact layout:
    # QWERTY: q w e r t y u i o p å
    # COLEMAK: q w f p g j l u y ö å
    
    # TOP ROW - Only keys that moved
    "e": "f",     # e -> f
    "r": "p",     # r -> p  
    "t": "g",     # t -> g
    "y": "j",     # y -> j
    "u": "l",     # u -> l
    "i": "u",     # i -> u
    "o": "y",     # o -> y
    "p": "ö",     # p -> ö
    
    # MIDDLE ROW - Only keys that moved
    # QWERTY: a s d f g h j k l ö ä
    # COLEMAK: a r s t d h n e i o ä
    "s": "r",     # s -> r
    "d": "s",     # d -> s
    "f": "t",     # f -> t
    "g": "d",     # g -> d
    # h -> h (stays same)
    "j": "n",     # j -> n
    "k": "e",     # k -> e
    "l": "i",     # l -> i
    "ö": "o",     # ö -> o
    
    # BOTTOM ROW - Only keys that moved
    # QWERTY: z x c v b n m
    # COLEMAK: z x c v b k m
    "n": "k",     # n -> k
    # m -> m (stays same)
}


def log(message: str):
    """Log message with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\033[32m[{timestamp}]\033[0m {message}", file=sys.stderr)


def error(message: str):
    """Log error message"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\033[31m[{timestamp}] ERROR:\033[0m {message}", file=sys.stderr)


def warn(message: str):
    """Log warning message"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\033[33m[{timestamp}] WARNING:\033[0m {message}", file=sys.stderr)


def get_current_layout() -> str:
    """Get current layout from file"""
    try:
        if LAYOUT_FILE.exists():
            layout = LAYOUT_FILE.read_text().strip()
            # Layout should be either 'swe' or 'cmk'
            if layout in ["cmk"]:
                return "cmk"
            else:
                return "swe"
        return "swe"
    except Exception as e:
        error(f"Failed to read layout file: {e}")
        return "swe"


def translate_key(key: str, layout: str) -> str:
    """Translate a single key based on layout"""
    if layout == "cmk":
        return SWEDISH_TO_COLEMAK.get(key, key)
    return key


def process_keybind_line(line: str, layout: str) -> str:
    """Process a single keybind line"""
    # Skip empty lines and comments (except @POSITIONAL markers)
    if not line.strip() or (line.strip().startswith('#') and '@POSITIONAL' not in line):
        return line
    
    # Check if line has @POSITIONAL marker
    if '@POSITIONAL' in line:
        # Extract the key part from bindd line
        # Format: bindd = MODIFIERS, KEY, description, action
        match = re.match(r'^(\s*)bindd\s*=\s*([^,]+),\s*([^,]+),\s*(.*)$', line)
        if match:
            indent = match.group(1)
            modifiers = match.group(2)
            key = match.group(3).strip()
            rest = match.group(4)
            
            # Translate the key
            translated_key = translate_key(key, layout)
            
            # Remove the @POSITIONAL marker from the rest
            rest = re.sub(r'\s*#\s*@POSITIONAL\s*$', '', rest)
            
            # Rebuild the line
            return f"{indent}bindd = {modifiers}, {translated_key}, {rest}"
        else:
            # If parsing failed, return original line without @POSITIONAL marker
            return re.sub(r'\s*#\s*@POSITIONAL\s*$', '', line)
    else:
        # Non-positional line, return as-is
        return line


def translate_keybinds(layout: str) -> bool:
    """Main translation function"""
    log(f"Translating keybinds for layout: {layout}")
    
    # Check if source file exists
    if not SOURCE_CONFIG.exists():
        error(f"Source config file not found: {SOURCE_CONFIG}")
        return False
    
    # Create target directory if it doesn't exist
    TARGET_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    
    # Process the file
    line_count = 0
    translated_count = 0
    
    try:
        with open(SOURCE_CONFIG, 'r') as source, open(TARGET_CONFIG, 'w') as target:
            for line in source:
                line_count += 1
                line = line.rstrip('\n\r')  # Remove line endings but preserve content
                
                # Check if line will be translated
                if '@POSITIONAL' in line:
                    translated_count += 1
                
                # Process and write the line
                processed_line = process_keybind_line(line, layout)
                target.write(processed_line + '\n')
        
        log(f"Translation complete: {line_count} lines processed, {translated_count} lines translated")
        log(f"Generated config: {TARGET_CONFIG}")
        return True
        
    except Exception as e:
        error(f"Failed to translate keybinds: {e}")
        return False


def check_layout_change() -> bool:
    """Check if layout file has changed"""
    current_layout = get_current_layout()
    
    if LAST_LAYOUT_FILE.exists():
        try:
            last_layout = LAST_LAYOUT_FILE.read_text().strip()
            if current_layout == last_layout:
                return False  # No change
        except Exception:
            pass
    
    # Write current layout for next check
    try:
        LAST_LAYOUT_FILE.write_text(current_layout)
    except Exception as e:
        warn(f"Failed to write last layout file: {e}")
    
    return True  # Changed


def validate_config() -> bool:
    """Validate configuration"""
    if not SOURCE_CONFIG.exists():
        error(f"Source configuration file not found: {SOURCE_CONFIG}")
        return False
    
    if not SOURCE_CONFIG.is_file():
        error(f"Source configuration is not a file: {SOURCE_CONFIG}")
        return False
    
    return True


def reload_hyprland() -> bool:
    """Reload Hyprland configuration"""
    try:
        result = subprocess.run(['hyprctl', 'reload'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log("Hyprland config reloaded successfully")
            return True
        else:
            warn(f"Failed to reload Hyprland config: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        warn("Hyprland reload timed out")
        return False
    except FileNotFoundError:
        warn("hyprctl not found, cannot reload Hyprland config")
        return False
    except Exception as e:
        warn(f"Failed to reload Hyprland config: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Hyprland Keybind Translation Script")
    parser.add_argument('-f', '--force', action='store_true',
                       help='Force translation even if layout hasn\'t changed')
    parser.add_argument('--no-reload', action='store_true',
                       help='Don\'t reload Hyprland after translation')
    
    args = parser.parse_args()
    
    # Validate configuration
    if not validate_config():
        return 1
    
    # Check if we need to translate
    if args.force or check_layout_change():
        current_layout = get_current_layout()
        
        if translate_keybinds(current_layout):
            # Reload Hyprland config unless disabled
            if not args.no_reload:
                reload_hyprland()
            return 0
        else:
            return 1
    else:
        log("Layout unchanged, skipping translation")
        return 0


if __name__ == "__main__":
    sys.exit(main())