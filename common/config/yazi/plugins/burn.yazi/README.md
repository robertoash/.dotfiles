# burn.yazi

Burn ISO files to USB devices from Yazi file manager.

## Features

- Lists USB devices connected to your system
- Burns ISO files using `dd` with `pv` for progress
- Confirms before burning to prevent accidents
- Shows desktop notifications on completion/failure

## Requirements

- `lsblk` - for listing USB devices (usually pre-installed on Linux)
- `pv` - for progress monitoring during burn
- `dd` - for writing the ISO (usually pre-installed)
- `pkexec` - for sudo elevation (polkit)
- `notify-send` - for desktop notifications

Install missing dependencies:
```bash
# Arch Linux
sudo pacman -S pv libnotify

# Debian/Ubuntu
sudo apt install pv libnotify-bin
```

## Usage

1. Navigate to an ISO file in Yazi
2. Press the configured keybind (e.g., `b` for burn)
3. Select the target USB device from the list
4. Type `yes` to confirm
5. Enter your sudo password when prompted
6. Wait for the burn to complete (notification will appear)

## Keybindings

Within the device selection dialog:
- `j`/`k` or `↓`/`↑` - Navigate
- `Enter` or `l`/`→` - Burn to selected device
- `q` or `Esc` - Cancel

## Configuration

Add to your `~/.config/yazi/keymap.toml`:

```toml
[[manager.prepend_keymap]]
on = [ "b" ]
run = "plugin burn"
desc = "Burn ISO to USB"
```

## Safety

- The plugin requires `pkexec` (polkit) for sudo elevation
- Confirmation prompt requires typing "yes" to proceed
- **WARNING**: Burning will permanently erase all data on the target USB device
