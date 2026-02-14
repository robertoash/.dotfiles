"""
Setup nftables firewall configuration.

WARNING: Firewall misconfigurations can lock you out of your system!
This script validates configurations before installing.
"""

import subprocess
from pathlib import Path


def setup_nftables(dotfiles_dir, hostname):
    """Setup nftables configuration (Linux only)"""
    print("\n🔥 Step 6.8: Setting up nftables configuration...")
    print("    ⚠️  WARNING: Firewall misconfigurations can lock you out!")

    nftables_source_paths = [
        dotfiles_dir / hostname / "etc" / "nftables.conf",
        dotfiles_dir / "common" / "etc" / "nftables.conf",
    ]

    nftables_target_file = Path("/etc/nftables.conf")

    found_file = False
    for nftables_source_file in nftables_source_paths:
        if not nftables_source_file.exists():
            continue

        found_file = True

        # Check if file already exists and is identical
        needs_update = True
        if nftables_target_file.exists():
            source_content = nftables_source_file.read_text()
            target_content = nftables_target_file.read_text()
            if source_content == target_content:
                needs_update = False
                print(f"  ✅ nftables.conf is already up to date")

        if needs_update:
            print(f"  🔥 Installing nftables.conf to /etc/ (requires sudo)...")
            print(f"     Validating nftables syntax...")

            # Validate nftables syntax
            validate_result = subprocess.run(
                ["sudo", "nft", "-c", "-f", str(nftables_source_file)],
                capture_output=True,
                text=True
            )

            if validate_result.returncode != 0:
                print(f"  ❌ CRITICAL: nftables.conf has syntax errors - REFUSING to install")
                print(f"     Error: {validate_result.stderr}")
                print(f"     This would likely break your firewall!")
                break

            print(f"     Syntax validation passed ✓")
            print(f"     Installing to /etc/nftables.conf...")

            # Backup existing file first
            if nftables_target_file.exists():
                backup_cmd = subprocess.run(
                    ["sudo", "cp", str(nftables_target_file), f"{nftables_target_file}.backup"]
                )
                if backup_cmd.returncode == 0:
                    print(f"     Backed up existing file to {nftables_target_file}.backup")

            # Copy file to /etc/ with correct permissions (0644)
            copy_result = subprocess.run(
                ["sudo", "install", "-m", "0644", str(nftables_source_file), str(nftables_target_file)]
            )

            if copy_result.returncode == 0:
                print(f"  ✅ Installed nftables.conf to /etc/")

                # Reload nftables
                print(f"     Reloading nftables rules...")
                reload_result = subprocess.run(
                    ["sudo", "nft", "-f", str(nftables_target_file)],
                    capture_output=True,
                    text=True
                )

                if reload_result.returncode == 0:
                    print(f"  ✅ Reloaded nftables rules successfully")
                else:
                    print(f"  ⚠️  Failed to reload nftables rules")
                    print(f"     Error: {reload_result.stderr}")
                    print(f"     If you get locked out, restore with: sudo cp {nftables_target_file}.backup {nftables_target_file}")
            else:
                print(f"  ⚠️  Failed to install nftables.conf")

        break  # Only use first found file

    if not found_file:
        print("  ℹ️  No nftables.conf found")
