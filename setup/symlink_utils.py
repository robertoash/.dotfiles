"""
Symlink utilities for dotfiles setup.
"""

import subprocess
from pathlib import Path


def create_symlink(source, target, description=""):
    """Create symlink, removing existing file/link if needed"""
    target = Path(target)
    source = Path(source)

    if not source.exists():
        print(f"⚠️  Source does not exist: {source}")
        return

    # Create parent directory if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing target if it exists
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            target.unlink()
        else:
            if target.is_dir():
                subprocess.run(["rm", "-rf", str(target)], check=True)
            else:
                target.unlink()

    # Create symlink
    target.symlink_to(source.resolve())
    desc = f" ({description})" if description else ""
    print(f"✅ {target} -> {source}{desc}")


def merge_common_into_machine(common_dir, machine_dir, config_root, dotfiles_dir, level=0, symlink_paths=None, progress_info=None, higher_source_dirs=None):
    """
    Populate machine_dir with symlinks to files from common_dir.
    Only creates symlinks for items that don't already exist in machine_dir.
    Recursively merges subdirectories.
    Collects all symlink paths relative to config_root for .gitignore.

    Args:
        higher_source_dirs: List of directory paths from higher-priority sources
                           at the same level in the hierarchy. Used to determine
                           whether to create real directories (for merging) or symlinks.
    """
    if higher_source_dirs is None:
        higher_source_dirs = []
    common_dir = Path(common_dir)
    machine_dir = Path(machine_dir)
    config_root = Path(config_root)

    if not common_dir.exists():
        return symlink_paths

    # Create machine_dir if it doesn't exist
    machine_dir.mkdir(parents=True, exist_ok=True)

    # Clean up broken symlinks that were created by setup.py
    # (i.e., symlinks pointing to locations within dotfiles directory)
    if machine_dir.exists():
        for item in machine_dir.iterdir():
            if item.is_symlink() and not item.exists():
                # Broken symlink - check if it points within dotfiles
                try:
                    target = item.resolve(strict=False)
                    if str(target).startswith(str(dotfiles_dir)):
                        # This was created by setup.py, safe to remove
                        item.unlink()
                        if level == 0:
                            print(f"🗑️  Removed broken symlink: {item.name}")
                except (OSError, RuntimeError):
                    pass

    if symlink_paths is None:
        symlink_paths = []

    if progress_info is None:
        progress_info = {"current": 0, "total": 0, "name": ""}

    indent = "  " * level

    # For each item in common_dir
    items = list(common_dir.iterdir())
    for common_app_item in items:
        machine_app_item = machine_dir / common_app_item.name

        # Skip .gitignore files - they should be machine-specific
        if common_app_item.name == '.gitignore':
            continue

        # Update progress counter
        if level >= 0:
            progress_info["current"] += 1
            if progress_info["name"]:
                print(f"\r🔀 Merging {progress_info['name']}... ({progress_info['current']}/{progress_info['total']} processed)", end='', flush=True)

        # Check if this item exists in any higher-priority source
        item_in_higher = any(
            (hdir / common_app_item.name).exists()
            for hdir in higher_source_dirs
        )

        # If item doesn't exist in machine_dir
        if not machine_app_item.exists() and not machine_app_item.is_symlink():
            if item_in_higher and common_app_item.is_dir():
                # Create real directory for merging (will be merged with higher-priority content)
                machine_app_item.mkdir(parents=True, exist_ok=True)
                if level == 0:
                    print(f"\n{indent}📁 {common_app_item.name} (will merge with higher sources)")
                # Recurse with higher source dirs narrowed to this subdirectory
                sub_higher_dirs = [
                    hdir / common_app_item.name
                    for hdir in higher_source_dirs
                    if (hdir / common_app_item.name).exists()
                ]
                merge_common_into_machine(common_app_item, machine_app_item, config_root, dotfiles_dir, level + 1, symlink_paths, progress_info, sub_higher_dirs)
            else:
                # Normal case: create symlink
                machine_app_item.symlink_to(common_app_item.resolve())
                if level == 0:
                    print(f"\n{indent}📎 {common_app_item.name} -> common")
                # Add relative path from config root
                # Symlinks are always tracked as files (even if they point to directories)
                symlink_paths.append(str(machine_app_item.relative_to(config_root)))
        elif machine_app_item.is_symlink():
            # Symlink already exists - add to gitignore
            if machine_app_item.resolve() == common_app_item.resolve():
                # Symlinks are always tracked as files (even if they point to directories)
                symlink_paths.append(str(machine_app_item.relative_to(config_root)))
            # Don't recurse into symlinked directories
        elif common_app_item.is_dir() and machine_app_item.is_dir() and not machine_app_item.is_symlink():
            # Both are directories and machine_app_item is not a symlink, merge recursively
            sub_higher_dirs = [
                hdir / common_app_item.name
                for hdir in higher_source_dirs
                if (hdir / common_app_item.name).exists()
            ]
            merge_common_into_machine(common_app_item, machine_app_item, config_root, dotfiles_dir, level + 1, symlink_paths, progress_info, sub_higher_dirs)

    return symlink_paths
