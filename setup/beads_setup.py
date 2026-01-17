"""
Setup beads integration (Claude Code hooks and git hooks).
"""

import subprocess
from pathlib import Path


def setup_beads_integration(dotfiles_dir):
    """Setup beads Claude Code hooks and git hooks"""
    print("\n📿 Setting up beads integration...")

    # Check if bd command exists
    bd_check = subprocess.run(["which", "bd"], capture_output=True)
    if bd_check.returncode != 0:
        print("  ⚠️  bd command not found. Skipping beads setup.")
        print("  💡 Install beads with: go install github.com/steveyegge/beads/cmd/bd@latest")
        return

    # Setup Claude Code hooks (global)
    try:
        result = subprocess.run(
            ["bd", "setup", "claude"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("  ✅ Claude Code hooks installed")
        else:
            print(f"  ⚠️  Failed to setup Claude hooks: {result.stderr.strip()}")
    except Exception as e:
        print(f"  ⚠️  Error setting up Claude hooks: {e}")

    # Setup git hooks in dotfiles repo if it has .beads directory
    beads_dir = dotfiles_dir / ".beads"
    if beads_dir.exists() and beads_dir.is_dir():
        try:
            result = subprocess.run(
                ["bd", "hooks", "install"],
                cwd=dotfiles_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print("  ✅ Git hooks installed in dotfiles repo")
            else:
                print(f"  ⚠️  Failed to install git hooks: {result.stderr.strip()}")
        except Exception as e:
            print(f"  ⚠️  Error installing git hooks: {e}")
    else:
        print("  ℹ️  No .beads directory found, skipping git hooks")
