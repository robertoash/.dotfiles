"""
Setup /etc/vconsole.conf for console keyboard layout.
"""

import subprocess
from pathlib import Path


def setup_vconsole(dotfiles_dir, hostname, machine_config):
    """Setup /etc/vconsole.conf (Linux only)"""
    print("\n⌨️  Step: Setting up console keyboard layout...")

    vconsole_file = dotfiles_dir / hostname / "vconsole.conf"

    if not vconsole_file.exists():
        print("  ℹ️  No vconsole.conf found for this machine")
        return

    # Read the vconsole configuration
    vconsole_content = vconsole_file.read_text()

    try:
        # Check current /etc/vconsole.conf
        etc_vconsole = Path("/etc/vconsole.conf")
        current_content = etc_vconsole.read_text() if etc_vconsole.exists() else ""

        # Check if our configuration is already in place
        if vconsole_content.strip() in current_content:
            print("  ✅ /etc/vconsole.conf already configured")
            return

        print("  🔒 Updating /etc/vconsole.conf (requires sudo)...")

        # Use sudo tee to write to /etc/vconsole.conf
        result = subprocess.run(
            ["sudo", "tee", "/etc/vconsole.conf"],
            input=vconsole_content,
            text=True,
            capture_output=True
        )

        if result.returncode == 0:
            print("  ✅ Updated /etc/vconsole.conf")
            print("  ℹ️  Keyboard layout will be applied on next boot")
            print("  💡 To apply immediately in console, run: sudo loadkeys <keymap>")
        else:
            print(f"  ⚠️  Failed to update vconsole.conf: {result.stderr.strip()}")

    except (PermissionError, FileNotFoundError) as e:
        print(f"  ⚠️  Cannot access /etc/vconsole.conf: {e}")
