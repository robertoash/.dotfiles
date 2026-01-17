"""
Setup backup crontab entries.
"""

import subprocess
from pathlib import Path


def setup_crontab(dotfiles_dir, hostname):
    """Setup backup crontab (Linux only)"""
    machine_dir = dotfiles_dir / hostname
    backup_crontab_file = machine_dir / "scripts" / "backup" / "crontab" / "bkup_crontab_entries.txt"

    if backup_crontab_file.exists():
        print("\n📅 Step 10: Setting up backup crontab...")

        # Check if cronie is installed
        cronie_check = subprocess.run(["which", "crontab"], capture_output=True)

        if cronie_check.returncode == 0:
            # Read crontab entries file
            crontab_content = backup_crontab_file.read_text()

            # Extract user crontab entries (before "#### Sudo Crontab")
            user_entries = []
            sudo_entries = []
            in_sudo_section = False

            for line in crontab_content.split('\n'):
                line = line.strip()
                if line.startswith("#### Sudo Crontab"):
                    in_sudo_section = True
                    continue
                if line and not line.startswith('#'):
                    if in_sudo_section:
                        # Remove 'sudo' from the command for sudo crontab
                        sudo_entries.append(line.replace('sudo ', '', 1))
                    else:
                        user_entries.append(line)

            if user_entries:
                # Get existing crontab
                existing_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                existing_crontab = existing_result.stdout if existing_result.returncode == 0 else ""

                # Check if backup entries already exist
                marker = "# === BACKUP CRONTAB ENTRIES ==="
                if marker not in existing_crontab:
                    # Append new entries
                    new_crontab = existing_crontab.rstrip()
                    if new_crontab:
                        new_crontab += "\n\n"
                    new_crontab += f"{marker}\n"
                    new_crontab += "\n".join(user_entries) + "\n"

                    # Load new crontab
                    load_result = subprocess.run(
                        ["crontab", "-"],
                        input=new_crontab,
                        text=True,
                        capture_output=True
                    )

                    if load_result.returncode == 0:
                        print(f"  ✅ Loaded {len(user_entries)} user crontab entries")
                    else:
                        print(f"  ⚠️  Failed to load crontab: {load_result.stderr.strip()}")
                else:
                    print("  ℹ️  Backup crontab entries already loaded")

            # Setup sudo crontab automatically
            if sudo_entries:
                print("\n  🔒 Setting up root crontab (requires sudo)...")

                # Get existing root crontab
                existing_result = subprocess.run(
                    ["sudo", "crontab", "-l"],
                    capture_output=True,
                    text=True
                )
                existing_root_crontab = existing_result.stdout if existing_result.returncode == 0 else ""

                # Check if backup entries already exist
                root_marker = "# === BACKUP CRONTAB ENTRIES ==="
                if root_marker not in existing_root_crontab:
                    # Append new entries
                    new_root_crontab = existing_root_crontab.rstrip()
                    if new_root_crontab:
                        new_root_crontab += "\n\n"
                    new_root_crontab += f"{root_marker}\n"
                    new_root_crontab += "\n".join(sudo_entries) + "\n"

                    # Load new root crontab
                    load_result = subprocess.run(
                        ["sudo", "crontab", "-"],
                        input=new_root_crontab,
                        text=True,
                        capture_output=True
                    )

                    if load_result.returncode == 0:
                        print(f"  ✅ Loaded {len(sudo_entries)} root crontab entries")
                    else:
                        print(f"  ⚠️  Failed to load root crontab: {load_result.stderr.strip()}")
                else:
                    print("  ℹ️  Root backup crontab entries already loaded")
        else:
            print("  ⚠️  crontab not found - install cronie package")
