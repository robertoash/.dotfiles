# Dotfiles Project Instructions

## Dotfiles Management (CRITICAL)

**NEVER directly modify:**
- ~/.config/*
- ~/.local/bin/*
- ~/.ssh/config
- /etc/hosts
- /etc/sudoers.d/*
- systemd units
- crontab

**ALWAYS:**
1. Modify source files in `~/.dotfiles/{hostname}/` or `~/.dotfiles/common/`
2. Run `cd ~/.dotfiles && python setup.py` to apply changes
3. The repo uses symlinks - changes must be to source files, not symlinked targets

**Exceptions require:**
- Clear justification why dotfiles approach won't work
- Explicit user approval before proceeding

**Example workflow:**
```bash
# ❌ WRONG: vim ~/.config/nvim/init.lua
# ✅ RIGHT:
vim ~/.dotfiles/common/config/nvim/init.lua
cd ~/.dotfiles && python setup.py
```

## Environment Variable Propagation (linuxmini)

Env vars flow through two layers. Full details in `system/env_vars.yaml`.

1. **systemd user env** — `environment.d/env_vars.conf` (global vars) + `sops-secrets.service` (secrets). Used by systemd services and imported by fish (`00_environment.fish`).
2. **Hyprland process env** — `start-session.sh` wrapper (called by greetd) imports secrets + systemd env before exec'ing Hyprland. All keybind-launched processes inherit automatically.

**Do NOT use `hyprctl keyword env` at runtime** — it doesn't propagate to child processes ([hyprwm/Hyprland#8403](https://github.com/hyprwm/Hyprland/issues/8403)). If Hyprland children need new env vars, add them to the wrapper or systemd env.

Scripts launched from Hyprland keybinds should never need to load secrets themselves — they inherit from Hyprland's process environment.
