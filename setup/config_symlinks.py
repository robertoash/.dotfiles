"""
Symlink configuration files to ~/.config and handle special cases.
"""

import subprocess
from pathlib import Path

from symlinks import create_symlink


def symlink_configs(dotfiles_dir, hostname, home, machine_config):
    """Symlink all configs to ~/.config"""
    print("\n🔗 Step 2: Symlinking configs to ~/.config...")

    config_dir = home / ".config"
    config_dir.mkdir(exist_ok=True)

    machine_config_dir = dotfiles_dir / hostname / "config"
    common_config_dir = dotfiles_dir / "common" / "config"

    # Track warnings about existing valid symlinks
    symlink_warnings = []

    # Symlink machine-specific configs (which now contain merged common + machine files)
    if machine_config_dir.exists():
        for item in machine_config_dir.iterdir():
            if item.name == ".gitignore":
                continue  # Skip .gitignore - handled in Step 3 from machine directory
            if item.is_dir() or item.is_file():
                target = config_dir / item.name
                create_symlink(item, target, f"{hostname}")

    # Symlink common configs that don't have machine-specific versions
    if common_config_dir.exists():
        for item in common_config_dir.iterdir():
            target = config_dir / item.name
            # Check if machine-specific version exists
            machine_version = machine_config_dir / item.name if machine_config_dir.exists() else None

            # Skip if machine-specific version exists (it takes precedence)
            if machine_version and machine_version.exists():
                continue

            # Only symlink if not already linked from machine-specific
            if target.is_symlink() and not target.exists():
                # Broken symlink - replace it
                create_symlink(item, target, "common")
            elif target.is_symlink() and target.exists():
                # Check if pointing to machine-specific version (which takes precedence)
                if machine_version and machine_version.exists() and target.resolve() == machine_version.resolve():
                    # Correctly pointing to machine version, no warning needed
                    pass
                elif target.resolve() != item.resolve():
                    # Valid symlink pointing elsewhere - warn but don't replace
                    symlink_warnings.append(f"  ⚠️  {target} -> {target.resolve()} (not replaced)")
            elif not target.exists():
                # Doesn't exist - create it
                create_symlink(item, target, "common")

    # Step 3: Symlink machine directories directly (not in config/)
    machine_dir = dotfiles_dir / hostname
    if machine_dir.exists():
        for item in machine_dir.iterdir():
            if item.name == "config":
                continue  # Already handled above
            if item.is_dir() or item.is_file():
                target = config_dir / item.name
                # Only create if doesn't exist or is a broken symlink
                if target.is_symlink() and not target.exists():
                    # Broken symlink - replace it
                    create_symlink(item, target, f"{hostname} direct")
                elif target.is_symlink() and target.exists():
                    # Check if already pointing to this machine's version
                    if target.resolve() == item.resolve():
                        # Already correctly linked, no warning needed
                        pass
                    else:
                        # Valid symlink pointing elsewhere - warn but don't replace
                        symlink_warnings.append(f"  ⚠️  {target} -> {target.resolve()} (not replaced)")
                elif not target.exists():
                    # Doesn't exist - create it
                    create_symlink(item, target, f"{hostname} direct")

    # Handle special cases
    _handle_special_cases(dotfiles_dir, hostname, home, machine_config)

    return symlink_warnings


def _handle_special_cases(dotfiles_dir, hostname, home, machine_config):
    """Handle special symlink cases"""
    machine_dir = dotfiles_dir / hostname
    config_dir = home / ".config"

    # Home directory dotfiles - automatically symlink everything in home/
    home_dir = machine_dir / "home"
    if home_dir.exists():
        for item in home_dir.iterdir():
            target = home / item.name
            create_symlink(item, target, "home")

    # Secrets directory - symlink merged secrets to ~/secrets
    machine_secrets_dir = machine_dir / "secrets"
    if machine_secrets_dir.exists():
        secrets_target = home / "secrets"
        create_symlink(machine_secrets_dir, secrets_target, "secrets")

    # Machine-specific scripts - symlink if they exist
    scripts_dir = machine_dir / "scripts"
    if scripts_dir.exists():
        create_symlink(scripts_dir, config_dir / "scripts", "scripts")

    # Machine-specific local/bin directory - symlink individual files
    local_bin_dir = machine_dir / "local" / "bin"
    if local_bin_dir.exists():
        local_bin_target = home / ".local" / "bin"
        local_bin_target.mkdir(parents=True, exist_ok=True)
        for script in local_bin_dir.iterdir():
            if script.is_file():
                target = local_bin_target / script.name
                create_symlink(script, target, f"local/bin/{script.name}")

                # For run_bkup_script, also symlink to /usr/local/bin for root access
                if script.name == "run_bkup_script" and machine_config["is_linux"]:
                    usr_local_bin_target = Path("/usr/local/bin") / script.name
                    if not usr_local_bin_target.exists():
                        print(f"\n  🔒 Creating system-wide symlink for {script.name} (requires sudo)...")
                        result = subprocess.run(
                            ["sudo", "ln", "-sf", str(target), str(usr_local_bin_target)],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            print(f"  ✅ Symlinked to /usr/local/bin/{script.name}")
                        else:
                            print(f"  ⚠️  Failed to create system symlink: {result.stderr.strip()}")
