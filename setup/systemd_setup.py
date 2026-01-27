"""
Setup systemd services and reload daemon.
"""

import subprocess
from pathlib import Path


def symlink_systemd_services(source_dir, target_dir, label):
    """Symlink systemd service files from source to target directory"""
    if not source_dir.exists():
        return 0

    count = 0
    target_dir.mkdir(parents=True, exist_ok=True)

    for service_file in source_dir.glob("*.service"):
        target_file = target_dir / service_file.name

        # Remove existing symlink or file
        if target_file.exists() or target_file.is_symlink():
            target_file.unlink()

        # Create symlink
        target_file.symlink_to(service_file.resolve())
        print(f"  ✅ Symlinked {service_file.name} ({label})")
        count += 1

    return count


def reload_systemd_daemon(dotfiles_dir, hostname, machine_config):
    """Setup systemd services and reload daemon (Linux only)"""
    print("\n⚙️  Step 9: Setting up systemd services...")

    systemd_config_dir = Path.home() / ".config" / "systemd" / "user"

    # Symlink linuxcommon systemd services (for all Linux machines)
    linuxcommon_systemd = dotfiles_dir / "linuxcommon" / "systemd" / "user"
    count = symlink_systemd_services(linuxcommon_systemd, systemd_config_dir, "linuxcommon")

    # Symlink machine-specific systemd services
    machine_systemd = dotfiles_dir / hostname / "systemd" / "user"
    count += symlink_systemd_services(machine_systemd, systemd_config_dir, hostname)

    if count > 0:
        # Reload systemd daemon
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        print("  🔄 Systemd user daemon reloaded")
