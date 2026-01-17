"""
Setup systemd services and reload daemon.
"""

import subprocess
from pathlib import Path


def reload_systemd_daemon(dotfiles_dir, hostname):
    """Reload systemd daemon (Linux only)"""
    machine_dir = dotfiles_dir / hostname
    systemd_user_dir = machine_dir / "systemd" / "user"

    if systemd_user_dir.exists():
        print("\n⚙️  Step 9: Reloading systemd user daemon...")
        # Reload systemd daemon
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        print("  🔄 Systemd user daemon reloaded")
