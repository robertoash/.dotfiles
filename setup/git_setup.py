import subprocess
from pathlib import Path

from config import GIT_ASSUME_UNCHANGED


def apply_git_index_flags(dotfiles_dir: Path):
    """Apply git index flags for files that generate spurious changes."""
    if not GIT_ASSUME_UNCHANGED:
        return

    print("\n🔧 Applying git index flags...")
    for path in GIT_ASSUME_UNCHANGED:
        result = subprocess.run(
            ["git", "update-index", "--assume-unchanged", path],
            cwd=dotfiles_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  ✅ assume-unchanged: {path}")
        else:
            print(f"  ⚠️  Failed for {path}: {result.stderr.strip()}")
