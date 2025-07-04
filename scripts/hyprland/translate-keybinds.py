#!/usr/bin/env python3
"""
Hyprland Keybind Translation Script
Translates keybinds between Swedish and Swedish Colemak layouts
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

# Swedish to Swedish Colemak key mapping
SWEDISH_TO_COLEMAK = {
    # Navigation cluster (hjkl) - most important
    "h": "m",     # Swedish h -> Swedish m (Colemak position)
    "j": "n",     # Swedish j -> Swedish n (Colemak position)
    "k": "e",     # Swedish k -> Swedish e (Colemak position)  
    "l": "i",     # Swedish l -> Swedish i (Colemak position)
    
    # Additional positional keys commonly used in navigation
    "n": "k",     # Swedish n -> Swedish k (Colemak position)
    "m": "h",     # Swedish m -> Swedish h (Colemak position)
    "e": "f",     # Swedish e -> Swedish f (Colemak position)
    "i": "l",     # Swedish i -> Swedish l (Colemak position)
    "f": "t",     # Swedish f -> Swedish t (Colemak position)
    "t": "g",     # Swedish t -> Swedish g (Colemak position)
    "r": "p",     # Swedish r -> Swedish p (Colemak position)
    "s": "r",     # Swedish s -> Swedish r (Colemak position)
    "p": ";",     # Swedish p -> Swedish ; (Colemak position)
    "y": "j",     # Swedish y -> Swedish j (Colemak position)
    "u": "o",     # Swedish u -> Swedish o (Colemak position)
    "o": "y",     # Swedish o -> Swedish y (Colemak position)
    "d": "s",     # Swedish d -> Swedish s (Colemak position)
    "g": "d",     # Swedish g -> Swedish d (Colemak position)
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
            # Normalize layout names
            if layout in ["cmk", "swedish-colemak"]:
                return "swedish-colemak"
            else:
                return "swedish"
        return "swedish"
    except Exception as e:
        error(f"Failed to read layout file: {e}")
        return "swedish"


def translate_key(key: str, layout: str) -> str:
    """Translate a single key based on layout"""
    if layout in ["swedish-colemak", "cmk"]:
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