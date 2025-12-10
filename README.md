# Dotfiles Structure

This repository contains dotfiles for multiple machines with a shared common base to avoid code duplication.

## Directory Structure

```
~/.dotfiles/
├── common/                    # Common configs shared across all machines
│   ├── config/               # Standard app configs
│   │   ├── fish/             # Shell configuration
│   │   ├── nvim/             # Neovim configuration
│   │   ├── git/              # Git configuration
│   │   ├── starship/         # Starship prompt
│   │   ├── espanso/          # Text expansion
│   │   └── wezterm/          # Terminal emulator
│   └── ssh/                  # SSH authorized keys
├── linuxmini/                # Machine-specific configs for linuxmini
│   ├── config/               # Application configs → ~/.config/
│   │   ├── hypr/             # Hyprland window manager
│   │   ├── waybar/           # Status bar
│   │   ├── foot/             # Terminal emulator
│   │   ├── kanata/           # Keyboard remapping
│   │   ├── rofimoji/         # Emoji picker
│   │   ├── sunshine/         # Game streaming
│   │   └── [50+ other apps]  # CLI tools, utilities, etc.
│   ├── scripts/              # Executable scripts (not configs)
│   ├── systemd/user/         # Systemd user services
│   │   ├── _waybar/          # Waybar-related services
│   │   ├── _mqtt/            # MQTT-related services
│   │   ├── _dunst/           # Dunst notification services
│   │   └── *.service         # Auto-generated symlinks (gitignored)
│   ├── python-tools/         # Custom Python CLI tools
│   └── secrets/              # Encrypted secrets (SOPS)
├── workmbp/                  # Machine-specific configs for workmbp
│   ├── config/               # macOS/work-specific configs
│   │   ├── fish/             # Work-specific fish additions
│   │   ├── karabiner/        # Keyboard remapping (macOS)
│   │   ├── sketchybar/       # Status bar (macOS)
│   │   └── sunshine/         # Game streaming (macOS)
│   ├── .hammerspoon/         # Hammerspoon automation (macOS)
│   ├── raycast/              # Raycast launcher (macOS)
│   └── snowflake/            # Snowflake CLI (work)
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
1. **Merges common configs** into machine-specific directories within the repo
2. **Symlinks configs** from `{hostname}/config/` to `~/.config/`
3. **Symlinks scripts** from `{hostname}/scripts/` to `~/.config/scripts/`
4. **Sets up systemd services** (Linux only):
   - Creates symlinks from `systemd/user/_*/` subdirectories to top-level
   - Reloads systemd user daemon
5. **Handles special cases** (macOS app locations, SSH keys, etc.)

## Key Features

- **DRY Principle**: Common configs (fish, nvim, git) are shared, avoiding duplication
- **Machine Flexibility**: Each machine can have specific configurations
- **Systemd Service Management**: Organized services in subdirectories (`_waybar/`, `_mqtt/`, etc.) with auto-symlink creation
- **Clean Structure**: App configs in `config/`, executables in `scripts/`, services in `systemd/`
- **Work Separation**: Work-specific tools (snowflake) isolated to workmbp

## Systemd Services (Linux)

Services are organized in subdirectories under `systemd/user/`:
- `_waybar/` - Waybar and related status scripts
- `_mqtt/` - MQTT listeners and reporters
- `_dunst/` - Notification daemon services

The `setup.py` script automatically creates symlinks from these subdirectories to the top-level `systemd/user/` directory, allowing systemd to discover them. Symlinks are gitignored while actual service files in subdirectories are tracked.