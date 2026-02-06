"""
Setup SSH config and authorized_keys.
"""

import subprocess
from pathlib import Path

from symlink_utils import create_symlink


def setup_ssh(dotfiles_dir, hostname, home):
    """Setup SSH config and authorized_keys"""
    print("\n🔐 Step 5: Setting up SSH config and authorized_keys...")
    ssh_dir = home / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    # Symlink SSH config from dotfiles (prefer machine-specific, fall back to common)
    machine_ssh_config = dotfiles_dir / hostname / "ssh" / "config"
    common_ssh_config = dotfiles_dir / "common" / "ssh" / "config"
    ssh_config_target = ssh_dir / "config"

    if machine_ssh_config.exists():
        ssh_config_source = machine_ssh_config
        # Ensure source file has correct permissions (600)
        subprocess.run(["chmod", "600", str(ssh_config_source)], check=True)
        create_symlink(ssh_config_source, ssh_config_target, f"SSH config ({hostname})")
    elif common_ssh_config.exists():
        ssh_config_source = common_ssh_config
        # Ensure source file has correct permissions (600)
        subprocess.run(["chmod", "600", str(ssh_config_source)], check=True)
        create_symlink(ssh_config_source, ssh_config_target, "SSH config (common)")
    else:
        print(f"⚠️  SSH config not found in {machine_ssh_config} or {common_ssh_config}")

    # Symlink authorized_keys from dotfiles
    authorized_keys_source = dotfiles_dir / "common" / "ssh" / "authorized_keys"
    authorized_keys_target = ssh_dir / "authorized_keys"

    if authorized_keys_source.exists():
        # Ensure source file has correct permissions (600)
        subprocess.run(["chmod", "600", str(authorized_keys_source)], check=True)
        create_symlink(authorized_keys_source, authorized_keys_target, "SSH authorized_keys")
    else:
        print(f"⚠️  SSH authorized_keys source not found: {authorized_keys_source}")
