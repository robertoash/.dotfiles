# Dotfiles Structure

This repository contains dotfiles for multiple machines with a shared common base to avoid code duplication.

## Directory Structure

```
~/.dotfiles/
├── config/                    # Common configs shared across all machines
│   ├── fish/                 # Shell configuration
│   ├── nvim/                 # Neovim configuration  
│   ├── git/                  # Git configuration
│   ├── starship/             # Starship prompt
│   ├── espanso/              # Text expansion
│   └── wezterm/              # Terminal emulator
├── scripts/                   # Shared scripts and utilities
├── linuxmini/                # Machine-specific configs for linuxmini
│   ├── config/               # Additional Linux configs
│   ├── hypr/                 # Hyprland window manager
│   ├── waybar/               # Status bar
│   ├── systemd/              # Systemd services
│   ├── kanata/               # Keyboard remapping
│   ├── foot/                 # Terminal emulator
│   └── sunshine/             # Game streaming
├── workmbp/                  # Machine-specific configs for workmbp  
│   ├── config/               # macOS/work-specific configs
│   │   ├── fish/             # Work-specific fish additions
│   │   ├── karabiner/        # Keyboard remapping (macOS)
│   │   ├── sketchybar/       # Status bar (macOS)
│   │   └── sunshine/         # Game streaming (macOS)
│   ├── .hammerspoon/         # Hammerspoon automation (macOS)
│   ├── raycast/              # Raycast launcher (macOS)
│   └── snowsql/              # Snowflake CLI (work)
└── oldmbp/                   # Machine-specific configs for oldmbp
    └── config/
        └── niri/             # Niri window manager
```

## Setup

Single hostname-aware setup script for all machines:

```bash
cd ~/.dotfiles
python3 setup.py
```

The script automatically detects your hostname and:
- Symlinks all common configs from `common/config/` to `~/.config/`
- Symlinks machine-specific configs from `{hostname}/config/` to `~/.config/`  
- Symlinks machine-specific directories from `{hostname}/` to `~/.config/`
- Handles special cases (macOS app locations, etc.)

## Key Features

- **DRY Principle**: Common configs (fish, nvim, git) are shared, avoiding duplication
- **Machine Flexibility**: Each machine can have specific configurations
- **Symlink Management**: Setup scripts create appropriate symlinks for each platform
- **Work Separation**: Work-specific tools (dbt, snowflake) isolated to workmbp

## Migration from NixOS

This structure replaces the previous NixOS home-manager setup with:
- ✅ No NixOS dependencies or `/nix/store` references
- ✅ No secrets tracked (private keys in gitignore)
- ✅ Functional parity maintained across all machines
- ✅ Native OS package managers instead of Nix