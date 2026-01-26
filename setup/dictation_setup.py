"""
System-wide voice dictation setup using hyprwhspr.
Fast, accurate, and private speech-to-text for Linux with Wayland/Hyprland.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def check_command_exists(command):
    """Check if a command exists in PATH"""
    try:
        subprocess.run(
            ["which", command],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_wayland():
    """Check if running Wayland"""
    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE")

    return wayland_display or xdg_session_type == "wayland"


def check_hyprwhspr_installed():
    """Check if hyprwhspr is installed"""
    system = platform.system().lower()

    if system != "linux":
        print(f"⚠️  hyprwhspr only supports Linux, not {system}")
        return False

    # Check if Wayland
    if not check_wayland():
        print("⚠️  Wayland session not detected. hyprwhspr requires Wayland.")
        print("   Current session type:", os.environ.get("XDG_SESSION_TYPE", "unknown"))
        return False

    # Check if hyprwhspr command exists
    if check_command_exists("hyprwhspr"):
        print("✅ hyprwhspr is installed")
        return True

    # Not installed - provide instructions
    print("⚠️  hyprwhspr not found")

    # Detect Linux distribution for install instructions
    try:
        with open("/etc/os-release") as f:
            os_release = f.read().lower()
    except FileNotFoundError:
        os_release = ""

    print("\n   Please install hyprwhspr:")
    if "arch" in os_release:
        print("   → yay -S hyprwhspr")
    else:
        print("   → curl -fsSL https://raw.githubusercontent.com/goodroot/hyprwhspr/main/scripts/install-deps.sh | bash")
        print("   → git clone https://github.com/goodroot/hyprwhspr.git ~/hyprwhspr")
        print("   → cd ~/hyprwhspr && ./bin/hyprwhspr setup")

    print("\n   Then re-run: cd ~/.dotfiles && python setup.py")
    return False



def run_hyprwhspr_setup():
    """Run hyprwhspr interactive setup"""
    home = Path.home()
    config_dir = home / ".config" / "hyprwhspr"

    # Check if already configured
    if (config_dir / "config.json").exists():
        print("✅ hyprwhspr already configured")
        return True

    print("🔧 Running hyprwhspr setup...")
    print("   This will open an interactive configuration wizard.")
    print("   Recommended: Choose 'base' model for good balance of speed/accuracy")

    try:
        # Try to run hyprwhspr setup
        if check_command_exists("hyprwhspr"):
            subprocess.run(["hyprwhspr", "setup"], check=True)
        else:
            # Try from source installation
            home = Path.home()
            install_dir = home / "hyprwhspr"
            if (install_dir / "bin" / "hyprwhspr").exists():
                subprocess.run([str(install_dir / "bin" / "hyprwhspr"), "setup"], check=True)
            else:
                print("⚠️  hyprwhspr command not found. Please run manually:")
                print("   cd ~/hyprwhspr && ./bin/hyprwhspr setup")
                return False

        print("✅ hyprwhspr setup complete")
        return True

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error running hyprwhspr setup: {e}")
        return False


def create_default_config():
    """Create a sensible default configuration for hyprwhspr"""
    home = Path.home()
    config_dir = home / ".config" / "hyprwhspr"
    config_file = config_dir / "config.json"

    # Don't overwrite existing config
    if config_file.exists():
        print("✅ hyprwhspr config already exists")
        return True

    config_dir.mkdir(parents=True, exist_ok=True)

    # Default configuration with good settings
    default_config = {
        "primary_shortcut": "SUPER+ALT+D",
        "recording_mode": "toggle",
        "model": "base",
        "transcription_backend": "local",
        "use_hypr_bindings": True,
        "grab_keys": False,
        "mic_osd_enabled": True,
        "audio_feedback": True,
        "symbol_replacements": True,
        "clipboard_behavior": False,
        "paste_mode": "ctrl_shift"
    }

    with open(config_file, "w") as f:
        json.dump(default_config, f, indent=2)

    print(f"✅ Created default config at {config_file}")
    print("   Edit with: hyprwhspr config")
    return True


def setup_dictation(skip_install=False, skip_setup=False):
    """
    Setup system-wide voice dictation for Linux.

    Args:
        skip_install: Skip checking if hyprwhspr is installed
        skip_setup: Skip interactive setup (use defaults)

    Returns:
        bool: True if setup succeeded, False otherwise
    """
    print("\n🎤 Setting up system-wide voice dictation (hyprwhspr)...")

    # Check platform
    if platform.system().lower() != "linux":
        print("⚠️  Voice dictation setup only supports Linux")
        return False

    # Check Wayland
    if not check_wayland():
        print("⚠️  Wayland session required for hyprwhspr")
        return False

    # Step 1: Check if hyprwhspr is installed (if not skipped)
    if not skip_install:
        if not check_hyprwhspr_installed():
            return False
    else:
        print("⏭️  Skipping installation check (skip_install=True)")

    # Step 2: Run setup wizard or create default config
    if not skip_setup:
        if not run_hyprwhspr_setup():
            print("⚠️  Setup wizard failed, creating default config...")
            create_default_config()
    else:
        print("⏭️  Skipping interactive setup, using defaults...")
        create_default_config()

    print("\n✅ Voice dictation configuration complete!")
    print("\n💡 Next steps:")
    print("   1. Add keybinding to ~/.dotfiles/linuxmini/config/hypr/hyprland.conf:")
    print("      bindd = SUPER ALT, D, Speech-to-text, exec, hyprwhspr record")
    print("   2. Reload Hyprland: hyprctl reload")
    print("   3. Log out and back in (for input group permissions)")
    print("   4. Press Super+Alt+D to start/stop dictation")
    print("\n   Commands: hyprwhspr status | hyprwhspr config | hyprwhspr test")

    return True


if __name__ == "__main__":
    # Allow running directly for testing
    setup_dictation()
