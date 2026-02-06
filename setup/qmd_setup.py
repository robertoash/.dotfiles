"""
qmd setup - Local semantic search for markdown files and knowledge bases.

Features:
- BM25 full-text search via SQLite FTS5
- Vector semantic search using embeddings
- Hybrid query mode with LLM re-ranking
- Query expansion and reciprocal rank fusion
"""

import subprocess
import sys
from pathlib import Path


def check_command_exists(command):
    """Check if a command exists in PATH"""
    try:
        subprocess.run(
            ["which", command],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_command_version(command):
    """Get version of a command"""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def check_bun_installed():
    """Check if Bun is installed with correct version"""
    if not check_command_exists("bun"):
        print("  ⚠️  Bun not found. Please install Bun first.")
        print("     Visit: https://bun.sh")
        print("     Or run: curl -fsSL https://bun.sh/install | bash")
        return False

    version = get_command_version("bun")
    print(f"  ✓ Bun found: {version}")

    # Check version >= 1.0.0
    try:
        version_num = version.split()[0] if version else "0"
        major = int(version_num.split('.')[0])
        if major < 1:
            print(f"  ⚠️  Bun version {version_num} is too old. Please upgrade to >= 1.0.0")
            return False
    except (ValueError, IndexError):
        print(f"  ⚠️  Could not parse Bun version: {version}")
        return False

    return True


def check_sqlite_installed():
    """Check if SQLite is installed"""
    if check_command_exists("sqlite3"):
        version = get_command_version("sqlite3")
        print(f"  ✓ SQLite found: {version}")
        return True

    print("  ⚠️  SQLite not found. Please install SQLite first.")
    print("     Arch: pacman -S sqlite")
    print("     Debian/Ubuntu: apt install sqlite3")
    return False


def is_qmd_installed():
    """Check if qmd is already installed"""
    return check_command_exists("qmd")


def install_qmd():
    """Install qmd via Bun"""
    print("  📦 Installing qmd...")
    try:
        result = subprocess.run(
            ["bun", "install", "-g", "github:tobi/qmd"],
            capture_output=True,
            text=True,
            check=True
        )
        print("  ✓ qmd installed successfully")

        # Verify installation
        if check_command_exists("qmd"):
            print("  ✓ qmd command available")
            return True
        else:
            print("  ⚠️  qmd installed but command not found in PATH")
            print("     Make sure ~/.bun/bin is in your PATH")
            return False

    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to install qmd: {e.stderr}")
        return False


def update_qmd():
    """Update qmd to latest version"""
    print("  📦 Updating qmd...")
    try:
        subprocess.run(
            ["bun", "update", "-g", "github:tobi/qmd"],
            capture_output=True,
            text=True,
            check=True
        )
        print("  ✓ qmd updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to update qmd: {e.stderr}")
        print("  ℹ️  Continuing with existing version")
        return False


def setup_qmd(dotfiles_dir, skip_install=False, force_update=False):
    """
    Setup qmd - local semantic search for markdown files.

    Args:
        dotfiles_dir: Path to dotfiles directory
        skip_install: Skip installation/update if True
        force_update: Force update even if already installed

    Returns:
        bool: True if setup succeeded, False otherwise
    """
    print("\n🔍 Setting up qmd (Query Markup Documents)...")

    # Check Bun
    if not check_bun_installed():
        return False

    # Check SQLite
    if not check_sqlite_installed():
        return False

    if skip_install:
        print("  ⏩ Skipping install (skip_install=True)")
        if is_qmd_installed():
            print("  ✓ Using existing qmd installation")
            return True
        else:
            print("  ⚠️  qmd not found")
            return False

    # Install or update qmd
    qmd_exists = is_qmd_installed()

    if qmd_exists and not force_update:
        print("  ✓ qmd already installed")
        print("     Run with force_update=True to update")
    elif qmd_exists and force_update:
        if not update_qmd():
            return False
    else:
        if not install_qmd():
            return False

    # Print usage information
    print("\n✅ qmd setup complete!")
    print("\n💡 Next steps:")
    print("   1. Add a collection:    qmd collection add ~/notes")
    print("   2. Add context:         qmd collection context <name> 'Description of collection'")
    print("   3. Generate embeddings: qmd embed")
    print("   4. Search your notes:   qmd query 'your search query'")
    print("\n   Commands:")
    print("   - qmd search <term>     Fast keyword search (BM25)")
    print("   - qmd vsearch <term>    Vector semantic search")
    print("   - qmd query <question>  Hybrid search with re-ranking")
    print("   - qmd collection list   List all collections")
    print("\n   Note: Models (~2GB) will be downloaded on first search")
    print("   Cache location: ~/.cache/qmd/models/")

    return True


if __name__ == "__main__":
    # Allow running standalone for testing
    dotfiles_dir = Path(__file__).parent.parent
    setup_qmd(dotfiles_dir, force_update="--update" in sys.argv)
