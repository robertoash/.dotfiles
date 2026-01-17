"""
Setup /etc/hosts entries.
"""

import subprocess
from pathlib import Path


def setup_hosts(dotfiles_dir):
    """Setup /etc/hosts entries (Linux only)"""
    print("\n🌐 Step 6: Setting up /etc/hosts entries...")
    hosts_file = dotfiles_dir / "system" / "hosts"

    if hosts_file.exists():
        # Read the hosts entries
        hosts_content = hosts_file.read_text()
        hosts_entries = []

        for line in hosts_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                hosts_entries.append(line)

        if hosts_entries:
            # Check if entries already exist in /etc/hosts
            try:
                etc_hosts = Path("/etc/hosts").read_text()
                marker = "# === DOTFILES MANAGED HOSTS ==="

                if marker not in etc_hosts:
                    print(f"  ℹ️  Found {len(hosts_entries)} host entries to add")
                    print("  🔒 Adding entries to /etc/hosts (requires sudo)...")

                    # Build the content to append
                    hosts_content_to_add = f"\n{marker}\n"
                    for entry in hosts_entries:
                        hosts_content_to_add += f"{entry}\n"
                    hosts_content_to_add += "# === END DOTFILES MANAGED HOSTS ===\n"

                    # Use sudo tee to append to /etc/hosts
                    result = subprocess.run(
                        ["sudo", "tee", "-a", "/etc/hosts"],
                        input=hosts_content_to_add,
                        text=True,
                        capture_output=True
                    )

                    if result.returncode == 0:
                        print(f"  ✅ Added {len(hosts_entries)} host entries to /etc/hosts")
                    else:
                        print(f"  ⚠️  Failed to add hosts: {result.stderr.strip()}")
                else:
                    print("  ✅ /etc/hosts entries already present")
            except (PermissionError, FileNotFoundError) as e:
                print(f"  ⚠️  Cannot access /etc/hosts: {e}")
