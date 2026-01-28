"""
Configuration for dotfiles merge and symlink system.

To add a new directory to the merge system:
1. Add an entry to MERGE_DIRS below
2. Run setup.py - it will automatically:
   - Merge common/{source} -> linuxcommon/{source} -> machine/{target}
   - Create symlinks to the specified destination
   - Update .gitignore for auto-generated symlinks
"""

from pathlib import Path

# Directories that follow the merge pattern: common -> linuxcommon -> machine
# Each entry defines how a directory should be merged and symlinked.
#
# Keys:
#   source: Path relative to common/ or linuxcommon/ (where shared files live)
#   target: Path relative to machine dir (where merged result lives)
#   symlink: Absolute path where symlink should point (None = no symlink, handled elsewhere)
#   symlink_mode: How to create symlinks
#       - "contents": Symlink each item inside the directory to symlink/{item}
#       - "directory": Symlink the entire directory to symlink path
#
MERGE_DIRS = {
    "config": {
        "source": "config",
        "target": "config",
        "symlink": Path.home() / ".config",
        "symlink_mode": "contents",
    },
    "secrets": {
        "source": "secrets",
        "target": "secrets",
        "symlink": Path.home() / "secrets",
        "symlink_mode": "directory",
    },
    "scripts": {
        "source": "scripts",
        "target": "scripts",
        "symlink": Path.home() / ".config" / "scripts",
        "symlink_mode": "directory",
    },
    "systemd/user": {
        "source": "systemd/user",
        "target": "systemd/user",
        "symlink": None,  # Handled specially: ~/.config/systemd -> machine/systemd
        "symlink_mode": None,
    },
}
