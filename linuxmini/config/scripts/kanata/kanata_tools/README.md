# Kanata Tools

Unified tooling for managing Kanata keyboard remapper with smart state persistence.

## Features

- **Layer Switching**: Switch between Swedish (SWE) and Colemak (CMK) layouts
- **Mod State Toggle**: Toggle between MOD (home row mods) and NOMOD states
- **Smart State Persistence**: Automatically detects reboots vs keyboard reconnects
  - On reboot: Loads default state (SWE-MOD)
  - On keyboard reconnect: Restores last saved state
- **Status Monitoring**: Real-time monitoring of Kanata layer changes
- **Integration**: Updates Waybar status, Espanso config, and other system components

## Installation

Using uv:

```bash
cd ~/.config/scripts/kanata
uv pip install -e .
```

Or use the install script:

```bash
./install.sh
```

## Usage

### Switch layouts or mod states

```bash
# Switch between SWE and CMK layouts
kanata-tools switch --layout

# Toggle between MOD and NOMOD states
kanata-tools switch --mod

# Set specific state
kanata-tools set --layout cmk --mod nomod
```

### Initialize on startup

```bash
# Smart initialization (detects reboot vs reconnect)
kanata-tools init

# Force default state
kanata-tools init --fresh-start
```

### Status monitoring

```bash
# Show current status
kanata-tools status

# Run status listener daemon
kanata-tools listen
```

## System Integration

### Systemd Service

The package includes a systemd service for the status listener that monitors Kanata's layer changes.

### Hyprland Keybindings

Configure in your Hyprland config:

```
bind = $mainMod, å, exec, kanata-tools switch --layout
bind = $mainMod, ä, exec, kanata-tools switch --mod
```

## State Persistence

The tool maintains state in multiple locations:

- `/tmp/kanata_layer_state.json` - Current session state
- `~/.config/kanata/last_state.json` - Persistent state across reconnects
- `/tmp/kanata_last_boot_time` - Boot time tracking for reboot detection