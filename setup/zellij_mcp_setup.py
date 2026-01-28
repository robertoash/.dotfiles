"""
Zellij MCP Server setup - enables Claude Code to interact with Zellij sessions.

Features:
- Opens files in nvim at specific line numbers
- Runs commands in specific panes
- Manages Zellij sessions and layouts
"""

import subprocess
import sys
from pathlib import Path


def setup_zellij_mcp(dotfiles_dir, skip_install=False):
    """Setup Zellij MCP Server for Claude Code integration."""
    dotfiles_dir = Path(dotfiles_dir)
    install_dir = Path.home() / ".local" / "share" / "zellij-mcp-server"

    print("\n🖥️  Setting up Zellij MCP Server...")

    # Check if zellij is installed
    try:
        result = subprocess.run(
            ["zellij", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✓ Zellij found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ⚠️  Zellij not found. Please install zellij first.")
        print("     Arch: pacman -S zellij")
        print("     macOS: brew install zellij")
        return False

    # Check if node is installed
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✓ Node.js found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ⚠️  Node.js not found. Please install Node.js 18+ first.")
        return False

    if skip_install:
        print("  ⏩ Skipping install (skip_install=True)")
        if install_dir.exists():
            print(f"  ✓ Using existing installation at {install_dir}")
            return True
        else:
            print(f"  ⚠️  No existing installation found at {install_dir}")
            return False

    # Clone or update the repository
    if install_dir.exists():
        print(f"  📦 Updating Zellij MCP Server at {install_dir}...")
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=install_dir,
                capture_output=True,
                check=True
            )
            print("  ✓ Repository updated")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Failed to update: {e.stderr}")
            print("  ℹ️  Continuing with existing version")
    else:
        print(f"  📦 Cloning Zellij MCP Server to {install_dir}...")
        install_dir.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "git", "clone",
                    "https://github.com/GitJuhb/zellij-mcp-server.git",
                    str(install_dir)
                ],
                capture_output=True,
                check=True
            )
            print("  ✓ Repository cloned")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to clone: {e.stderr}")
            return False

    # Install dependencies
    print("  📦 Installing dependencies...")
    try:
        subprocess.run(
            ["npm", "install"],
            cwd=install_dir,
            capture_output=True,
            check=True
        )
        print("  ✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install dependencies: {e.stderr}")
        return False

    # Build the project
    print("  🔨 Building project...")
    try:
        subprocess.run(
            ["npm", "run", "build"],
            cwd=install_dir,
            capture_output=True,
            check=True
        )
        print("  ✓ Build complete")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to build: {e.stderr}")
        return False

    # Make executable
    dist_index = install_dir / "dist" / "index.js"
    if dist_index.exists():
        dist_index.chmod(0o755)
        print(f"  ✓ Made {dist_index} executable")

    print("✅ Zellij MCP Server setup complete!")
    return True


if __name__ == "__main__":
    # Allow running standalone for testing
    dotfiles_dir = Path(__file__).parent.parent
    setup_zellij_mcp(dotfiles_dir)
