"""
Apply XDG user directory configuration by running xdg-user-dirs-update.
This reads ~/.config/user-dirs.dirs and creates the actual directories.
"""

import shutil
import subprocess
from pathlib import Path


def setup_xdg_user_dirs():
    if not shutil.which("xdg-user-dirs-update"):
        print("  ⚠️  xdg-user-dirs-update not found, skipping (install xdg-user-dirs)")
        return

    user_dirs_config = Path.home() / ".config" / "user-dirs.dirs"
    if not user_dirs_config.exists():
        print("  ⚠️  ~/.config/user-dirs.dirs not found, skipping xdg-user-dirs-update")
        return

    result = subprocess.run(
        ["xdg-user-dirs-update", "--force"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  ✅ XDG user directories updated")
    else:
        print(f"  ⚠️  xdg-user-dirs-update failed: {result.stderr.strip()}")
