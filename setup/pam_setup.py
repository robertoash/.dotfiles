"""
Setup PAM (Pluggable Authentication Modules) configuration.

WARNING: PAM configuration errors can lock you out of your system!
This script validates configurations before installing.
"""

import subprocess
from pathlib import Path


def setup_pam(dotfiles_dir):
    """Setup PAM configuration (Linux only)"""
    print("\n🔐 Step 6.3: Setting up PAM configuration...")
    print("    ⚠️  WARNING: PAM misconfigurations can lock you out!")

    pam_source_paths = [
        dotfiles_dir / "common" / "etc" / "pam.d",
    ]

    pam_target_dir = Path("/etc/pam.d")

    found_files = False
    for pam_source_dir in pam_source_paths:
        if not pam_source_dir.exists():
            continue

        pam_files = list(pam_source_dir.glob("*"))

        if pam_files:
            found_files = True
            for pam_file in pam_files:
                if pam_file.name.startswith('.') or not pam_file.is_file():
                    continue

                target_file = pam_target_dir / pam_file.name

                # Check if file already exists and is identical
                needs_update = True
                if target_file.exists():
                    source_content = pam_file.read_text()
                    target_content = target_file.read_text()
                    if source_content == target_content:
                        needs_update = False
                        print(f"  ✅ {pam_file.name} is already up to date")

                if needs_update:
                    print(f"  🔐 Installing {pam_file.name} to /etc/pam.d/ (requires sudo)...")
                    print(f"     Validating PAM syntax...")

                    # Basic validation: check for common issues
                    source_content = pam_file.read_text()

                    # Check for required pam_unix.so entries
                    if 'pam_unix.so' not in source_content:
                        print(f"  ❌ CRITICAL: {pam_file.name} missing pam_unix.so - REFUSING to install")
                        print(f"     This would likely lock you out of the system!")
                        continue

                    # Warn about requisite/required changes
                    if 'requisite' in source_content and 'pam_faillock.so' in source_content:
                        print(f"     Note: Using 'requisite' for faillock will show lock messages immediately")

                    print(f"     Installing to /etc/pam.d/...")

                    # Backup existing file first
                    if target_file.exists():
                        backup_cmd = subprocess.run(
                            ["sudo", "cp", str(target_file), f"{target_file}.backup"]
                        )
                        if backup_cmd.returncode == 0:
                            print(f"     Backed up existing file to {target_file}.backup")

                    # Copy file to /etc/pam.d/ with correct permissions (0644)
                    copy_result = subprocess.run(
                        ["sudo", "install", "-m", "0644", str(pam_file), str(target_file)]
                    )

                    if copy_result.returncode == 0:
                        print(f"  ✅ Installed {pam_file.name} to /etc/pam.d/")
                        print(f"     If you get locked out, restore with: sudo cp {target_file}.backup {target_file}")
                    else:
                        print(f"  ⚠️  Failed to install {pam_file.name}")

    if not found_files:
        print("  ℹ️  No PAM config files found")
