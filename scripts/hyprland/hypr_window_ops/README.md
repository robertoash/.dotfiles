# Hypr Window Ops

A utility for managing windows and workspaces in Hyprland, with functionality for launching applications in predefined layouts and moving groups of windows between workspaces.

## Features

- **Application Launcher**: Launch applications in predefined workspaces with proper window placement (master/stack)
- **Move Windows**: Move all windows from the current workspace to a target workspace in one command

## Installation

```bash
cd ~/.config/scripts/hyprland/hypr_window_ops
./install.sh
```

## Usage

### Launch Applications

To launch applications based on the default profile:

```bash
hypr-window-ops launch-apps
```

To specify a different profile:

```bash
hypr-window-ops launch-apps --profile jobhunt
```

Enable debug logging:

```bash
hypr-window-ops launch-apps --debug
```

### Move Windows

To move all windows from the current workspace to workspace 2:

```bash
hypr-window-ops move-windows 2
```

To move all windows to a special workspace:

```bash
hypr-window-ops move-windows stash
```

## Configuration

Configuration is stored in `~/.config/hypr/launch_apps.json`. Here's an example structure:

```json
{
  "personal": {
    "1": [
      {
        "name": "Terminal",
        "command": "kitty --detach",
        "is_master": true
      },
      {
        "name": "File Manager",
        "command": "pcmanfm",
        "is_master": false
      }
    ],
    "2": [
      {
        "name": "Browser",
        "command": "vivaldi",
        "is_master": true
      }
    ]
  },
  "jobhunt": {
    "1": [
      {
        "name": "Terminal",
        "command": "kitty --detach",
        "is_master": true
      }
    ],
    "2": [
      {
        "name": "Browser",
        "command": "vivaldi --new-window https://linkedin.com",
        "is_master": true
      }
    ]
  }
}
```

Each profile contains workspace numbers as keys, with arrays of applications to launch in those workspaces. For each application, specify:

- `name`: A descriptive name for the application
- `command`: The command to launch the application
- `is_master`: Whether this application should be the master window in the workspace

## Integration with Hyprland Config

Add to your `launch.conf`:

```conf
# Startup Apps
exec-once = hypr-window-ops launch-apps
```

Add keybindings in `keybinds.conf`:

```conf
# Move all windows to workspace
bindd = $HYPER, 1, Move all windows to ws 1, exec, hypr-window-ops move-windows 1
bindd = $HYPER, 2, Move all windows to ws 2, exec, hypr-window-ops move-windows 2
# Add more bindings for other workspaces...
```
