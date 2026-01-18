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

                # Build a map of managed entries by their identifier
                managed_entries = {}
                for entry in user_entries:
                    if "# managed:dotfiles:" in entry:
                        # Extract identifier from comment
                        identifier = entry.split("# managed:dotfiles:")[-1].strip()
                        managed_entries[identifier] = entry

                # Process existing crontab: update managed entries, keep others
                lines = existing_crontab.split('\n')
                new_lines = []
                updated_identifiers = set()

                for line in lines:
                    if "# managed:dotfiles:" in line:
                        # Extract identifier from existing line
                        identifier = line.split("# managed:dotfiles:")[-1].strip()
                        if identifier in managed_entries:
                            # Replace with updated entry
                            new_lines.append(managed_entries[identifier])
                            updated_identifiers.add(identifier)
                        else:
                            # Entry no longer in source, skip it
                            pass
                    else:
                        # Keep non-managed entries
                        new_lines.append(line)

                # Add new managed entries that weren't in existing crontab
                for identifier, entry in managed_entries.items():
                    if identifier not in updated_identifiers:
                        new_lines.append(entry)

                new_crontab = '\n'.join(new_lines).strip() + "\n"

                # Load new crontab
                load_result = subprocess.run(
                    ["crontab", "-"],
                    input=new_crontab,
                    text=True,
                    capture_output=True
                )

                if load_result.returncode == 0:
                    print(f"  ✅ Loaded {len(managed_entries)} user crontab entries")
                else:
                    print(f"  ⚠️  Failed to load crontab: {load_result.stderr.strip()}")

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

                # Build a map of managed entries by their identifier
                managed_root_entries = {}
                for entry in sudo_entries:
                    if "# managed:dotfiles:" in entry:
                        # Extract identifier from comment
                        identifier = entry.split("# managed:dotfiles:")[-1].strip()
                        managed_root_entries[identifier] = entry

                # Process existing crontab: update managed entries, keep others
                lines = existing_root_crontab.split('\n')
                new_lines = []
                updated_identifiers = set()

                for line in lines:
                    if "# managed:dotfiles:" in line:
                        # Extract identifier from existing line
                        identifier = line.split("# managed:dotfiles:")[-1].strip()
                        if identifier in managed_root_entries:
                            # Replace with updated entry
                            new_lines.append(managed_root_entries[identifier])
                            updated_identifiers.add(identifier)
                        else:
                            # Entry no longer in source, skip it
                            pass
                    else:
                        # Keep non-managed entries
                        new_lines.append(line)

                # Add new managed entries that weren't in existing crontab
                for identifier, entry in managed_root_entries.items():
                    if identifier not in updated_identifiers:
                        new_lines.append(entry)

                new_root_crontab = '\n'.join(new_lines).strip() + "\n"

                # Load new root crontab
                load_result = subprocess.run(
                    ["sudo", "crontab", "-"],
                    input=new_root_crontab,
                    text=True,
                    capture_output=True
                )

                if load_result.returncode == 0:
                    print(f"  ✅ Loaded {len(managed_root_entries)} root crontab entries")
                else:
                    print(f"  ⚠️  Failed to load root crontab: {load_result.stderr.strip()}")
        else:
            print("  ⚠️  crontab not found - install cronie package")
