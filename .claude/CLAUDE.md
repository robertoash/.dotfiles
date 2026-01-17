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
