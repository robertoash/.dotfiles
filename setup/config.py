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
#   mixed_mode_dirs: List of subdirectory names that should be created as real directories
#                    with their contents symlinked (allows runtime files alongside config)
#
MERGE_DIRS = {
    "config": {
        "source": "config",
        "target": "config",
        "symlink": Path.home() / ".config",
        "symlink_mode": "contents",
    },
    ".ttydal": {
        "source": "config/.ttydal",
        "target": ".ttydal",
        "symlink": Path.home() / ".ttydal",
        "symlink_mode": "contents",
    },
    "config/cyberdrop-dl": {
        "source": "config/cyberdrop-dl",
        "target": "config/cyberdrop-dl",
        "symlink": Path.home() / ".config" / "cyberdrop-dl",
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

# Configs that get overwritten by applications (breaking symlinks)
# These are backed up from home directory to machine/bkup with secrets masked
# target is relative to machine directory (e.g., workmbp/bkup/.sqlit)
BACKUP_CONFIGS = {
    ".sqlit": {
        "source": Path.home() / ".sqlit",
        "target": "bkup/.sqlit",  # Relative to machine dir (workmbp/bkup/.sqlit)
        "secrets_mask": {
            "connections.json": [
                {
                    "json_path": "connections[*].options.private_key_file_pwd",
                    "placeholder": "{{SNOWFLAKE_KEY_PWD}}"
                }
            ]
        }
    },
}
