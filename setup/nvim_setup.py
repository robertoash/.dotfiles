"""Neovim dependency checker for dotfiles setup."""

import shutil


def check_nvim_dependencies():
    """Check for tools required by Neovim plugins and LSPs."""

    print("\n🔍 Checking Neovim dependencies...")

    missing = []
    optional_missing = []

    # Core tools needed by nvim-treesitter and Mason
    core_tools = {
        "gcc": "Required by nvim-treesitter to compile parsers",
        "git": "Required for plugin management",
        "unzip": "Required for Mason to install LSPs/formatters",
        "tar": "Required for Mason to extract packages",
        "gzip": "Required for Mason to extract packages",
        "curl": "Required for downloading plugins and tools",
    }

    # Tools for specific Mason packages
    mason_tools = {
        "npm": "Required for installing pyright, prettier, and other Node-based LSPs",
        "cargo": "Optional: for installing Rust-based tools via Mason",
        "go": "Optional: for installing Go-based tools via Mason",
    }

    # Check core tools
    for tool, description in core_tools.items():
        if not shutil.which(tool):
            missing.append(f"  ❌ {tool:<10} - {description}")

    # Check optional Mason tools
    for tool, description in mason_tools.items():
        if not shutil.which(tool):
            optional_missing.append(f"  ⚠️  {tool:<10} - {description}")

    # Check for neovim itself
    nvim_path = shutil.which("nvim")
    if not nvim_path:
        missing.append("  ❌ nvim       - Neovim not installed")
    else:
        print(f"  ✅ nvim found at {nvim_path}")

    # Report findings
    if missing:
        print("\n🔴 Missing required dependencies:")
        for item in missing:
            print(item)

        # Build pacman install command
        packages = []
        for line in missing:
            if "nvim" not in line:
                tool = line.split()[1]
                packages.append(tool)

        if packages:
            print("\n💡 Install with: sudo pacman -S " + " ".join(packages))

    if optional_missing:
        print("\n🟡 Missing optional dependencies:")
        for item in optional_missing:
            print(item)
        print("\n💡 Install with: sudo pacman -S " + " ".join([
            line.split()[1] for line in optional_missing
        ]))

    if not missing and not optional_missing:
        print("  ✅ All Neovim dependencies satisfied!")

    # Provide Mason installation reminder
    if nvim_path and (missing or optional_missing):
        print("\n📝 After installing missing tools, run in Neovim:")
        print("   :MasonInstall pyright stylua black")

    return len(missing) == 0
