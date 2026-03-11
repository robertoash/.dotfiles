"""
Setup Samba configuration.
"""

import subprocess
from pathlib import Path


def setup_samba(dotfiles_dir, hostname):
    """Install smb.conf and reload Samba (Linux only)"""
    print("\n🗂️  Setting up Samba configuration...")

    source_paths = [
        dotfiles_dir / hostname / "etc" / "samba" / "smb.conf",
        dotfiles_dir / "common" / "etc" / "samba" / "smb.conf",
    ]

    target_file = Path("/etc/samba/smb.conf")

    source_file = next((p for p in source_paths if p.exists()), None)
    if not source_file:
        print("  ℹ️  No smb.conf found, skipping")
        return

    # Check if already up to date
    if target_file.exists():
        try:
            result = subprocess.run(
                ["sudo", "diff", str(source_file), str(target_file)],
                capture_output=True
            )
            if result.returncode == 0:
                print("  ✅ smb.conf already up to date")
                return
        except Exception:
            pass

    # Validate config before installing
    validate = subprocess.run(
        ["testparm", "-s", str(source_file)],
        capture_output=True,
        text=True
    )
    if validate.returncode != 0:
        print(f"  ❌ smb.conf failed validation — refusing to install")
        print(f"     {validate.stderr}")
        return
    print("  ✓  Config validated")

    # Ensure target directory exists
    subprocess.run(["sudo", "mkdir", "-p", str(target_file.parent)], check=True, capture_output=True)

    # Install
    result = subprocess.run(
        ["sudo", "install", "-m", "0644", str(source_file), str(target_file)]
    )
    if result.returncode != 0:
        print("  ⚠️  Failed to install smb.conf")
        return

    print("  ✅ Installed smb.conf")

    # Reload Samba if running
    for service in ("smb", "smbd"):
        check = subprocess.run(["systemctl", "is-active", service], capture_output=True)
        if check.returncode == 0:
            subprocess.run(["sudo", "systemctl", "reload", service], capture_output=True)
            print(f"  🔄 Reloaded {service}")
            break
