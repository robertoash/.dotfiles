"""
Setup pacman configuration including unofficial repositories.

This module manages:
- Chaotic-AUR repository configuration
- Other unofficial repositories as needed
"""

import subprocess
from pathlib import Path


def setup_pacman(dotfiles_dir):
    """Setup pacman configuration including Chaotic-AUR (Linux only)"""
    print("\n📦 Step 6.4: Setting up pacman configuration...")

    # Check if chaotic-keyring and chaotic-mirrorlist are installed
    keyring_check = subprocess.run(
        ["pacman", "-Q", "chaotic-keyring"],
        capture_output=True,
        text=True
    )
    mirrorlist_check = subprocess.run(
        ["pacman", "-Q", "chaotic-mirrorlist"],
        capture_output=True,
        text=True
    )

    if keyring_check.returncode != 0 or mirrorlist_check.returncode != 0:
        print("  🔑 Importing Chaotic-AUR GPG key (requires sudo)...")

        # Import the GPG key
        recv_result = subprocess.run([
            "sudo", "pacman-key", "--recv-key", "3056513887B78AEB",
            "--keyserver", "keyserver.ubuntu.com"
        ])

        if recv_result.returncode != 0:
            print("  ⚠️  Failed to receive GPG key")
            return

        # Locally sign the key
        lsign_result = subprocess.run([
            "sudo", "pacman-key", "--lsign-key", "3056513887B78AEB"
        ])

        if lsign_result.returncode != 0:
            print("  ⚠️  Failed to sign GPG key")
            return

        print("  ✅ GPG key imported and signed")

        print("  📦 Installing Chaotic-AUR keyring and mirrorlist (requires sudo)...")
        install_result = subprocess.run([
            "sudo", "pacman", "-U", "--noconfirm",
            "https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst",
            "https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst"
        ])

        if install_result.returncode != 0:
            print("  ⚠️  Failed to install Chaotic-AUR packages")
            return

        print("  ✅ Installed chaotic-keyring and chaotic-mirrorlist")

    # Check if Chaotic-AUR is already configured in pacman.conf
    pacman_conf = Path("/etc/pacman.conf")
    if not pacman_conf.exists():
        print("  ⚠️  /etc/pacman.conf not found")
        return

    pacman_conf_content = pacman_conf.read_text()

    # Check if chaotic-aur repository is already configured
    if "[chaotic-aur]" in pacman_conf_content:
        print("  ✅ Chaotic-AUR repository already configured in /etc/pacman.conf")
        # Verify it has the correct Include line
        if "Include = /etc/pacman.d/chaotic-mirrorlist" in pacman_conf_content:
            print("  ✅ Chaotic-AUR mirrorlist correctly configured")
            return
        else:
            print("  ⚠️  Chaotic-AUR section found but mirrorlist include is missing/incorrect")
            print("  ℹ️  Please manually fix /etc/pacman.conf")
            return

    # Add Chaotic-AUR configuration
    print("  📦 Adding Chaotic-AUR repository to /etc/pacman.conf (requires sudo)...")

    chaotic_aur_config = """

# Chaotic-AUR - Automated builds from AUR
# https://aur.chaotic.cx/
[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist
"""

    # Append to pacman.conf using sudo
    append_result = subprocess.run(
        ["sudo", "tee", "-a", "/etc/pacman.conf"],
        input=chaotic_aur_config,
        capture_output=True,
        text=True
    )

    if append_result.returncode == 0:
        print("  ✅ Added Chaotic-AUR repository to /etc/pacman.conf")
        print("  📝 Run 'sudo pacman -Sy' to update package databases")
    else:
        print("  ⚠️  Failed to add Chaotic-AUR repository to /etc/pacman.conf")
        print(f"     Error: {append_result.stderr}")
