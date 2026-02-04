"""
Setup systemd-resolved configuration.
"""

import subprocess
from pathlib import Path


def setup_resolved(dotfiles_dir, hostname, machine_config):
    """Setup systemd-resolved configuration (Linux only)"""
    if not machine_config["is_linux"]:
        return

    print("\n🌐 Setting up systemd-resolved configuration...")

    # Source paths - check both machine-specific and common
    machine_source = dotfiles_dir / hostname / "etc" / "systemd" / "resolved.conf.d"
    common_source = dotfiles_dir / "common" / "etc" / "systemd" / "resolved.conf.d"
    target_dir = Path("/etc/systemd/resolved.conf.d")

    # Determine which source directory to use
    source_dir = None
    if machine_source.exists():
        source_dir = machine_source
    elif common_source.exists():
        source_dir = common_source

    if not source_dir:
        print("  ℹ️  No resolved.conf.d configuration found")
        return

    print(f"  📁 Installing resolved.conf.d files from {source_dir}")

    try:
        # Ensure target directory exists
        subprocess.run(
            ["sudo", "mkdir", "-p", str(target_dir)],
            check=True,
            capture_output=True
        )

        # Copy all .conf files
        installed_count = 0
        for conf_file in source_dir.glob("*.conf"):
            target_file = target_dir / conf_file.name

            # Read source content
            source_content = conf_file.read_text()

            # Check if file needs updating
            needs_update = True
            if target_file.exists():
                try:
                    target_content = target_file.read_text()
                    if target_content == source_content:
                        needs_update = False
                except (PermissionError, OSError):
                    pass

            if needs_update:
                # Use sudo tee to write the file
                subprocess.run(
                    ["sudo", "tee", str(target_file)],
                    input=source_content.encode(),
                    check=True,
                    capture_output=True
                )
                print(f"  ✅ Installed {conf_file.name}")
                installed_count += 1
            else:
                print(f"  ℹ️  {conf_file.name} already up to date")

        if installed_count > 0:
            print("  🔄 Reloading systemd-resolved (if running)...")
            # Only reload if systemd-resolved is active
            result = subprocess.run(
                ["systemctl", "is-active", "systemd-resolved"],
                capture_output=True
            )
            if result.returncode == 0:
                subprocess.run(
                    ["sudo", "systemctl", "restart", "systemd-resolved"],
                    check=True
                )
                print("  ✅ systemd-resolved restarted")
            else:
                print("  ℹ️  systemd-resolved not active, will use config when enabled")

    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Error setting up systemd-resolved: {e}")
    except Exception as e:
        print(f"  ⚠️  Unexpected error: {e}")
