"""
Setup systemd services and reload daemon.
"""

import subprocess
from pathlib import Path


def symlink_systemd_services(source_dir, target_dir, label):
    """Symlink systemd service files from source to target directory"""
    if not source_dir.exists():
        return 0

    # If target_dir resolves to source_dir (e.g., via symlink), skip to avoid circular symlinks
    try:
        if source_dir.resolve() == target_dir.resolve():
            return 0
    except OSError:
        pass

    count = 0
    target_dir.mkdir(parents=True, exist_ok=True)

    for service_file in source_dir.glob("*.service"):
        target_file = target_dir / service_file.name

        # Skip if target already points to source correctly
        if target_file.is_symlink() and target_file.resolve() == service_file.resolve():
            continue

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
    machine_systemd = dotfiles_dir / hostname / "systemd" / "user"

    # If ~/.config/systemd points to the machine's systemd dir, skip symlinking
    # (the merge step already handles bringing in linuxcommon files)
    try:
        config_systemd_parent = Path.home() / ".config" / "systemd"
        if config_systemd_parent.is_symlink():
            resolved = config_systemd_parent.resolve()
            if str(resolved).startswith(str(dotfiles_dir)):
                print("  ℹ️  ~/.config/systemd is symlinked to dotfiles, skipping individual symlinks")
                subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
                print("  🔄 Systemd user daemon reloaded")
                return
    except OSError:
        pass

    # Symlink linuxcommon systemd services (for all Linux machines)
    linuxcommon_systemd = dotfiles_dir / "linuxcommon" / "systemd" / "user"
    count = symlink_systemd_services(linuxcommon_systemd, systemd_config_dir, "linuxcommon")

    # Symlink machine-specific systemd services
    count += symlink_systemd_services(machine_systemd, systemd_config_dir, hostname)

    if count > 0:
        # Reload systemd daemon
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        print("  🔄 Systemd user daemon reloaded")
