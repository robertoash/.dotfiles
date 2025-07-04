#!/usr/bin/env python3
"""
Test script for the application-specific Colemak system
"""

import json
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print the results"""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def check_file_content(file_path, description):
    """Check and display file content"""
    print(f"\n📄 {description}")
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            print(f"Content: '{content}'")
            return content
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def main():
    print("🚀 Testing Application-Specific Colemak System")
    print("=" * 50)
    
    # Test 1: Check current status
    print("\n1. Initial Status Check")
    run_command("python3 /home/rash/.config/scripts/kanata/colemak_app_manager.py --status", 
                "Check colemak app manager status")
    
    layout = check_file_content("/tmp/active_keyboard_layout", "Current active layout")
    
    # Test 2: Switch to Swedish if not already
    if layout != "swe":
        print("\n2. Switching to Swedish Layout")
        run_command("python3 /home/rash/.config/scripts/kanata/kanata_layer_switcher.py --action layout", 
                    "Switch to Swedish layout")
        time.sleep(0.5)
        check_file_content("/tmp/active_keyboard_layout", "Layout after switch")
    
    # Test 3: Apply Swedish to apps
    print("\n3. Apply Swedish to Applications")
    run_command("python3 /home/rash/.config/scripts/kanata/colemak_app_manager.py --apply swe", 
                "Apply Swedish to all enabled applications")
    
    # Test 4: Switch to Colemak
    print("\n4. Switch to Colemak Layout")
    run_command("python3 /home/rash/.config/scripts/kanata/kanata_layer_switcher.py --action layout", 
                "Switch to Colemak layout")
    time.sleep(0.5)
    check_file_content("/tmp/active_keyboard_layout", "Layout after switch")
    
    # Test 5: Apply Colemak to apps
    print("\n5. Apply Colemak to Applications")
    run_command("python3 /home/rash/.config/scripts/kanata/colemak_app_manager.py --apply cmk", 
                "Apply Colemak to all enabled applications")
    
    # Test 6: Final status check
    print("\n6. Final Status Check")
    run_command("python3 /home/rash/.config/scripts/kanata/colemak_app_manager.py --status", 
                "Final status check")
    
    # Test 7: Check Neovim configuration
    print("\n7. Neovim Configuration Check")
    check_file_content("/home/rash/.config/nvim/lua/custom/keyboard_layout_remaps.lua", 
                      "Neovim layout configuration (first 10 lines)")
    
    print("\n✅ Test completed!")
    print("\nNext steps:")
    print("1. Open Neovim and test typing in insert mode")
    print("2. Verify that navigation (hjkl) works as expected in normal mode")
    print("3. Test switching between Swedish and Colemak layouts")
    print("4. Enable more applications in colemak_apps.json as needed")

if __name__ == "__main__":
    main()