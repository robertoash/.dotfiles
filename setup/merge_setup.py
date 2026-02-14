"""
Merge common directories into machine-specific directories.
"""

from collections import defaultdict
from pathlib import Path

from config import MERGE_DIRS
from symlink_utils import merge_common_into_machine


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


def merge_from_source(source_base, machine_base, dotfiles_dir, label, higher_priority_sources=None):
    """
    Merge directories from a source (common or linuxcommon) into machine-specific dirs.

    Args:
        source_base: Base path of source (e.g., dotfiles/common or dotfiles/linuxcommon)
        machine_base: Base path of machine (e.g., dotfiles/linuxmini)
        dotfiles_dir: Root dotfiles directory
        label: Label for display (e.g., "common" or "linuxcommon")
        higher_priority_sources: List of higher-priority source bases to check
    """
    if higher_priority_sources is None:
        higher_priority_sources = []

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

        # Build list of higher-priority source directories at this level
        higher_source_dirs = [
            higher_source / source_path
            for higher_source in higher_priority_sources
            if (higher_source / source_path).exists()
        ]

        all_symlink_paths = merge_common_into_machine(
            source_dir, machine_dir, machine_dir, dotfiles_dir,
            progress_info=progress_info,
            higher_source_dirs=higher_source_dirs
        )
        print()

        if all_symlink_paths:
            update_gitignore(machine_dir, all_symlink_paths, dotfiles_dir)


def merge_machine_specific(dotfiles_dir, hostname):
    """
    Handle machine-specific configs where source and target paths differ
    but no common/linuxcommon/servercommon source exists. Merges machine/source → machine/target
    so the symlink step can find the target directory.
    """
    machine_base = dotfiles_dir / hostname
    other_bases = [
        dotfiles_dir / "common",
        dotfiles_dir / "linuxcommon",
        dotfiles_dir / "servercommon",
    ]

    for dir_name, dir_config in MERGE_DIRS.items():
        source_path = dir_config["source"]
        target_path = dir_config["target"]

        if source_path == target_path:
            continue

        # Skip if any shared source already handled this
        if any((base / source_path).exists() for base in other_bases):
            continue

        machine_source = machine_base / source_path
        machine_target = machine_base / target_path

        if not machine_source.exists():
            continue

        total = count_files_to_process(machine_source, machine_target)
        if total == 0:
            continue

        progress_info = {"current": 0, "total": total, "name": f"{hostname}/{source_path}"}
        icon = _get_icon(source_path)
        print(f"{icon} Merging {hostname}/{source_path}... (0/{total} processed)", end='', flush=True)

        all_symlink_paths = merge_common_into_machine(
            machine_source, machine_target, machine_target, dotfiles_dir, progress_info=progress_info
        )
        print()

        if all_symlink_paths:
            update_gitignore(machine_target, all_symlink_paths, dotfiles_dir)


def merge_common_directories(dotfiles_dir, hostname, machine_config):
    """Merge common directories into machine-specific directories"""
    print("\n🔀 Step 1: Merging common directories into machine-specific directories...")

    common_base = dotfiles_dir / "common"
    machine_base = dotfiles_dir / hostname

    # Build list of higher-priority sources that will merge after common
    higher_priority = []
    if machine_config.get("is_linux"):
        higher_priority.append(dotfiles_dir / "linuxcommon")
    if machine_config.get("is_server"):
        higher_priority.append(dotfiles_dir / "servercommon")

    merge_from_source(common_base, machine_base, dotfiles_dir, "common", higher_priority)


def merge_linuxcommon_directories(dotfiles_dir, hostname, machine_config):
    """Merge linuxcommon directories into Linux machine-specific directories"""
    print("\n🐧 Merging linuxcommon directories into Linux machine...")

    linuxcommon_base = dotfiles_dir / "linuxcommon"
    machine_base = dotfiles_dir / hostname

    if not linuxcommon_base.exists():
        return

    # servercommon is higher priority than linuxcommon
    higher_priority = []
    if machine_config.get("is_server"):
        higher_priority.append(dotfiles_dir / "servercommon")

    merge_from_source(linuxcommon_base, machine_base, dotfiles_dir, "linuxcommon", higher_priority)


def merge_servercommon_directories(dotfiles_dir, hostname):
    """Merge servercommon directories into server machine-specific directories"""
    print("\n🖥️  Merging servercommon directories into server machine...")

    servercommon_base = dotfiles_dir / "servercommon"
    machine_base = dotfiles_dir / hostname

    if not servercommon_base.exists():
        return

    merge_from_source(servercommon_base, machine_base, dotfiles_dir, "servercommon")


def prepare_hierarchical_merge(dotfiles_dir, hostname, machine_config):
    """
    Prepare for hierarchical merge by removing symlinks that would block higher-priority sources.

    Hierarchy: common < linuxcommon < servercommon < machine-specific

    If an item exists in a higher-priority source, we need to remove any symlink
    created by a lower-priority source so the higher-priority content can be merged.
    """
    machine_base = dotfiles_dir / hostname

    # Build list of sources in priority order (lowest to highest)
    sources = [("common", dotfiles_dir / "common")]

    if machine_config.get("is_linux"):
        sources.append(("linuxcommon", dotfiles_dir / "linuxcommon"))

    if machine_config.get("is_server"):
        sources.append(("servercommon", dotfiles_dir / "servercommon"))

    # For each MERGE_DIR, check if it exists in multiple sources
    for dir_name, dir_config in MERGE_DIRS.items():
        source_path = dir_config["source"]
        target_path = dir_config["target"]
        machine_dir = machine_base / target_path

        # Find which sources have this directory
        existing_sources = []
        for source_name, source_base in sources:
            source_dir = source_base / source_path
            if source_dir.exists():
                existing_sources.append((source_name, source_base, source_dir))

        # If multiple sources have it, we need real directories for merging
        if len(existing_sources) > 1:
            _remove_blocking_symlinks(machine_dir, existing_sources, dotfiles_dir)


def _remove_blocking_symlinks(machine_dir, sources, dotfiles_dir):
    """
    Remove symlinks in machine_dir that would prevent higher-priority sources from merging.

    Args:
        machine_dir: Machine-specific target directory
        sources: List of (name, base_path, source_dir) tuples that have content
        dotfiles_dir: Root dotfiles directory
    """
    if not machine_dir.exists():
        return

    # Collect all items from all sources
    all_items = set()
    for source_name, source_base, source_dir in sources:
        if source_dir.exists():
            for item in source_dir.iterdir():
                all_items.add(item.name)

    # For each item that exists in multiple sources, remove symlinks
    for item_name in all_items:
        machine_item = machine_dir / item_name

        # Count how many sources have this item
        item_count = sum(1 for _, _, src_dir in sources if (src_dir / item_name).exists())

        # If multiple sources have it and machine has a symlink, remove the symlink
        if item_count > 1 and machine_item.is_symlink():
            # Verify it points within dotfiles (safety check)
            try:
                target = machine_item.resolve(strict=False)
                if str(target).startswith(str(dotfiles_dir)):
                    machine_item.unlink()
                    print(f"  🗑️  Removed symlink {item_name} (will be merged from multiple sources)")
            except (OSError, RuntimeError):
                pass

        # Recurse into subdirectories
        if machine_item.is_dir() and not machine_item.is_symlink():
            # Collect subdirectory sources
            sub_sources = []
            for source_name, source_base, source_dir in sources:
                sub_item = source_dir / item_name
                if sub_item.exists() and sub_item.is_dir():
                    sub_sources.append((source_name, source_base, sub_item))

            if len(sub_sources) > 1:
                _remove_blocking_symlinks(machine_item, sub_sources, dotfiles_dir)
