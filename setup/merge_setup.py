"""
Merge common directories into machine-specific directories.
"""

from collections import defaultdict
from pathlib import Path

from config import MERGE_DIRS
from symlinks import merge_common_into_machine


def count_files_to_process(common_path, machine_path):
    """Count total files that need to be processed for progress tracking"""
    count = 0
    try:
        for common_item in common_path.iterdir():
            count += 1
            machine_item = machine_path / common_item.name
            if common_item.is_dir() and machine_item.exists() and machine_item.is_dir() and not machine_item.is_symlink():
                count += count_files_to_process(common_item, machine_item)
    except (OSError, PermissionError):
        pass
    return count


def update_gitignore(machine_dir, all_symlink_paths, dotfiles_dir):
    """Update .gitignore with symlink paths, optimizing when possible"""
    if not all_symlink_paths:
        return

    gitignore_path = machine_dir / ".gitignore"

    dir_files = defaultdict(lambda: {"symlinks": set(), "all_files": set()})

    for symlink_path in all_symlink_paths:
        path = Path(symlink_path)
        parent = str(path.parent) if path.parent != Path('.') else ""
        dir_files[parent]["symlinks"].add(symlink_path)
        actual_dir = machine_dir / path.parent
        if actual_dir.exists() and actual_dir.is_dir() and not actual_dir.is_symlink():
            for item in actual_dir.iterdir():
                rel_path = str(item.relative_to(machine_dir))
                dir_files[parent]["all_files"].add(rel_path)

    gitignore_entries = []
    for parent_dir, files in sorted(dir_files.items()):
        symlinks = files["symlinks"]
        all_files = files["all_files"]
        if symlinks == all_files and len(all_files) > 0:
            if parent_dir:
                gitignore_entries.append(f"{parent_dir}/")
        else:
            gitignore_entries.extend(sorted(symlinks))

    gitignore_entries = sorted(set(gitignore_entries))

    # Preserve existing content and merge with existing auto-generated entries
    existing_content = ""
    existing_auto_entries = set()
    marker_start = "# === AUTO-GENERATED SYMLINKS (do not edit) ===\n"
    marker_end = "# === END AUTO-GENERATED SYMLINKS ===\n"

    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if marker_start in existing:
            before = existing.split(marker_start)[0]
            if marker_end in existing:
                # Extract existing auto-generated entries to merge with new ones
                auto_section = existing.split(marker_start)[1].split(marker_end)[0]
                existing_auto_entries = set(line.strip() for line in auto_section.strip().split('\n') if line.strip())
                after = existing.split(marker_end)[1]
                existing_content = before + after
            else:
                existing_content = before
        else:
            existing_content = existing

    # Merge existing auto-generated entries with new ones
    all_entries = sorted(set(gitignore_entries) | existing_auto_entries)

    gitignore_content = existing_content.rstrip() + "\n\n" if existing_content.strip() else ""
    gitignore_content += marker_start
    gitignore_content += "\n".join(all_entries) + "\n"
    gitignore_content += marker_end

    gitignore_path.write_text(gitignore_content)
    new_count = len(gitignore_entries)
    total_count = len(all_entries)
    print(f"📝 Updated {gitignore_path.relative_to(dotfiles_dir)} ({total_count} entries, {new_count} new)")


def _get_icon(dir_name):
    """Get display icon for a directory type"""
    icons = {"secrets": "🔐", "scripts": "📜", "systemd": "⚙️"}
    for key, icon in icons.items():
        if key in dir_name:
            return icon
    return "📦"


def merge_from_source(source_base, machine_base, dotfiles_dir, label):
    """
    Merge directories from a source (common or linuxcommon) into machine-specific dirs.

    Args:
        source_base: Base path of source (e.g., dotfiles/common or dotfiles/linuxcommon)
        machine_base: Base path of machine (e.g., dotfiles/linuxmini)
        dotfiles_dir: Root dotfiles directory
        label: Label for display (e.g., "common" or "linuxcommon")
    """
    for dir_name, dir_config in MERGE_DIRS.items():
        source_path = dir_config["source"]
        target_path = dir_config["target"]

        source_dir = source_base / source_path
        machine_dir = machine_base / target_path

        if not source_dir.exists():
            continue

        total = count_files_to_process(source_dir, machine_dir)
        if total == 0:
            continue

        display_name = source_path
        progress_info = {"current": 0, "total": total, "name": f"{label}/{display_name}"}
        icon = _get_icon(display_name)
        print(f"{icon} Merging {label}/{display_name}... (0/{total} processed)", end='', flush=True)

        all_symlink_paths = merge_common_into_machine(
            source_dir, machine_dir, machine_dir, dotfiles_dir, progress_info=progress_info
        )
        print()

        if all_symlink_paths:
            update_gitignore(machine_dir, all_symlink_paths, dotfiles_dir)


def merge_common_directories(dotfiles_dir, hostname):
    """Merge common directories into machine-specific directories"""
    print("\n🔀 Step 1: Merging common directories into machine-specific directories...")

    common_base = dotfiles_dir / "common"
    machine_base = dotfiles_dir / hostname

    merge_from_source(common_base, machine_base, dotfiles_dir, "common")


def merge_linuxcommon_directories(dotfiles_dir, hostname):
    """Merge linuxcommon directories into Linux machine-specific directories"""
    print("\n🐧 Merging linuxcommon directories into Linux machine...")

    linuxcommon_base = dotfiles_dir / "linuxcommon"
    machine_base = dotfiles_dir / hostname

    if not linuxcommon_base.exists():
        return

    merge_from_source(linuxcommon_base, machine_base, dotfiles_dir, "linuxcommon")
