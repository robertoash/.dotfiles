"""
Build and install Rust tools from the tools/ directory.
Compiles with cargo and installs binaries to ~/.local/bin/.
"""

import shutil
import subprocess
from pathlib import Path


def needs_rebuild(tool_dir: Path, binary: Path) -> bool:
    if not binary.exists():
        return True
    binary_mtime = binary.stat().st_mtime
    for src in [tool_dir / "Cargo.toml", tool_dir / "Cargo.lock"]:
        if src.exists() and src.stat().st_mtime > binary_mtime:
            return True
    src_dir = tool_dir / "src"
    if src_dir.exists():
        for rs in src_dir.rglob("*.rs"):
            if rs.stat().st_mtime > binary_mtime:
                return True
    return False


def setup_tools(dotfiles_dir: Path):
    print("\n🦀 Step: Building Rust tools...")

    tools_dir = dotfiles_dir / "tools"
    if not tools_dir.exists():
        print("  ℹ️  No tools/ directory found, skipping")
        return

    if not shutil.which("cargo"):
        print("  ⚠️  cargo not found in PATH, skipping Rust tools")
        return

    local_bin = Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)

    for tool_dir in sorted(tools_dir.iterdir()):
        if not (tool_dir / "Cargo.toml").exists():
            continue

        name = tool_dir.name
        binary = tool_dir / "target" / "release" / name
        dest = local_bin / name

        if needs_rebuild(tool_dir, binary):
            print(f"  🔨 Building {name}...")
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=tool_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"  ❌ Build failed for {name}:")
                print(result.stderr[-500:] if result.stderr else "(no output)")
                continue
            print(f"  ✅ Built {name}")
        else:
            print(f"  ✅ {name} source unchanged")

        if not dest.exists() or binary.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(binary, dest)
            dest.chmod(0o755)
            print(f"  📦 Installed {name} → {dest}")
