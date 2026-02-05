"""
Symlink configuration files to ~/.config and handle special cases.
"""

import subprocess
from pathlib import Path

from config import MERGE_DIRS
from symlinks import create_symlink


def symlink_configs(dotfiles_dir, hostname, home, machine_config):
    """Symlink all configs based on MERGE_DIRS configuration"""
    print("\n🔗 Step 2: Symlinking configs...")

    machine_dir = dotfiles_dir / hostname

    # Track warnings about existing valid symlinks
    symlink_warnings = []

    # Sort by path depth (most specific first) to handle nested configs properly
    sorted_dirs = sorted(MERGE_DIRS.items(), key=lambda x: x[0].count('/'), reverse=True)

    # Track which subdirectories are handled by more specific rules
    handled_items = set()

    # Process each directory defined in MERGE_DIRS
    for dir_name, dir_config in sorted_dirs:
        target_path = dir_config["target"]
        symlink_dest = dir_config["symlink"]
        symlink_mode = dir_config["symlink_mode"]

        # Skip if no symlink configured (handled elsewhere)
        if symlink_dest is None:
            continue

        source_dir = machine_dir / target_path
        if not source_dir.exists():
            continue

        if symlink_mode == "contents":
            # Symlink each item inside the directory
            symlink_dest.mkdir(parents=True, exist_ok=True)
            for item in source_dir.iterdir():
                if item.name == ".gitignore":
                    continue

                # Skip items handled by more specific rules
                item_target = symlink_dest / item.name
                if str(item_target) in handled_items:
                    continue

                _create_or_replace_symlink(item, item_target, hostname, symlink_warnings, dotfiles_dir)

            # Mark this symlink destination as handled for parent directory processing
            handled_items.add(str(symlink_dest))

        elif symlink_mode == "directory":
            # Symlink the entire directory
            symlink_dest.parent.mkdir(parents=True, exist_ok=True)
            _create_or_replace_symlink(source_dir, symlink_dest, dir_name, symlink_warnings, dotfiles_dir)
            handled_items.add(str(symlink_dest))

    # Handle special cases not covered by MERGE_DIRS
    _handle_special_cases(dotfiles_dir, hostname, home, machine_config)

    return symlink_warnings


def _create_or_replace_symlink(source, target, label, warnings_list, dotfiles_dir):
    """Create symlink, replacing if it points to a dotfiles location"""
    if target.is_symlink() and not target.exists():
        # Broken symlink - replace it
        create_symlink(source, target, label)
    elif target.is_symlink() and target.exists():
        if target.resolve() == source.resolve():
            # Already correctly linked
            pass
        else:
            # Check if existing symlink points within dotfiles (managed by setup.py)
            existing_target = target.resolve()
            if str(existing_target).startswith(str(dotfiles_dir)):
                # Points to dotfiles - safe to replace
                create_symlink(source, target, label)
            else:
                # Points outside dotfiles - warn but don't replace
                warnings_list.append(f"  ⚠️  {target} -> {existing_target} (not replaced)")
    elif not target.exists():
        # Doesn't exist - create it
        create_symlink(source, target, label)


def _handle_special_cases(dotfiles_dir, hostname, home, machine_config):
    """Handle special symlink cases not covered by MERGE_DIRS"""
    machine_dir = dotfiles_dir / hostname

    # Home directory dotfiles - automatically symlink everything in home/
    home_dir = machine_dir / "home"
    if home_dir.exists():
        for item in home_dir.iterdir():
            target = home / item.name
            create_symlink(item, target, "home")

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
