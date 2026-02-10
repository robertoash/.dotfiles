# Codebase Structure

**Analysis Date:** 2026-02-10

## Directory Layout

```
~/.dotfiles/
├── setup.py                     # Orchestrator: detects hostname, sequences all setup steps
├── machines.py                  # Machine definitions and platform detection
├── pyrightconfig.json           # Type checking configuration
├── .sops.yaml                   # SOPS encryption config (age keys)
├── .claude/                     # Claude Code configuration (per-project)
├── .planning/                   # Planning output (GSD markdown files)
│
├── common/                      # Shared configs (merged into all machines)
│   ├── config/                  # App configs symlinked to ~/.config/
│   │   ├── fish/                # Shell functions, plugins, prompt
│   │   ├── nvim/                # Neovim configuration and plugins
│   │   ├── git/                 # Git config, aliases, hooks
│   │   ├── starship/            # Shell prompt configuration
│   │   ├── espanso/             # Text expansion templates
│   │   ├── wezterm/             # Terminal emulator config
│   │   ├── atuin/               # Shell history config
│   │   ├── bat/                 # Code viewer config
│   │   ├── broot/               # Directory browser config
│   │   ├── btop/                # System monitor config
│   │   ├── fzf/                 # Fuzzy finder configuration
│   │   └── [40+ other apps]/    # Other CLI tool configs
│   ├── ssh/                     # SSH authorized_keys, identity files
│   ├── .ttydal/                 # TTY dialog tool config
│   ├── .sqlit/                  # SQLite tool config
│   ├── config/.ttydal/          # symlink source for .ttydal
│   ├── config/.sqlit/           # symlink source for .sqlit
│   └── config/cyberdrop-dl/     # Download manager config
│
├── linuxcommon/                 # Shared Linux-only configs
│   ├── config/                  # Linux app configs (merged into linuxmini, oldmbp)
│   │   ├── hypr/                # Hyprland window manager
│   │   ├── waybar/              # Status bar
│   │   ├── dunst/               # Notification daemon
│   │   ├── foot/                # Terminal emulator
│   │   ├── kanata/              # Keyboard remapping
│   │   └── [20+ Linux tools]/   # Linux-specific CLI apps
│   ├── ssh/                     # SSH config for Linux machines
│   ├── systemd/user/            # Systemd user services (merged into machines)
│   ├── secrets/                 # Encrypted Linux secrets (SOPS)
│   └── etc/                     # /etc configs (hosts, sudoers, PAM, security)
│
├── linuxmini/                   # Desktop Linux machine configuration
│   ├── config/                  # Machine-specific app configs
│   │   ├── hypr/                # Hyprland setup for linuxmini
│   │   ├── waybar/              # Status bar customization
│   │   ├── kanata/              # Custom keyboard layout
│   │   └── [30+ apps]/          # Additional Linux tools
│   ├── scripts/                 # Shell and Python scripts
│   │   ├── _utils/              # Shared utilities (logging, cleanup)
│   │   └── backup/              # Backup job scripts
│   ├── python-tools/            # Custom Python CLI tools
│   │   ├── cjar/                # Container jar manager
│   │   ├── hypr-window-ops/     # Hyprland window management
│   │   └── kanata-tools/        # Kanata keyboard configuration
│   ├── systemd/user/            # Machine-specific systemd services
│   │   ├── _waybar/             # Waybar service definitions
│   │   ├── _mqtt/               # MQTT listener services
│   │   ├── _dunst/              # Dunst notification services
│   │   └── *.service            # Auto-symlinked from subdirs (gitignored)
│   ├── secrets/                 # Encrypted machine secrets
│   ├── ssh/                     # SSH config for linuxmini
│   ├── local/bin/               # Scripts symlinked to ~/.local/bin/
│   └── .ttydal/                 # TTY dialog state
│
├── workmbp/                     # macOS work machine configuration
│   ├── config/                  # macOS-specific app configs
│   │   ├── karabiner/           # Keyboard remapping (macOS)
│   │   ├── sketchybar/          # Menu bar customization
│   │   ├── fish/                # Work-specific fish additions
│   │   └── [apps]/              # Work tools (snowflake, etc.)
│   ├── .hammerspoon/            # Hammerspoon automation scripts
│   ├── raycast/                 # Raycast launcher scripts
│   ├── snowflake/               # Snowflake CLI configuration
│   ├── ssh/                     # SSH config for workmbp
│   ├── secrets/                 # Encrypted work secrets
│   └── home/                    # Home directory dotfiles (symlinked to ~/)
│
├── oldmbp/                      # Old macOS machine configuration
│   ├── config/                  # oldmbp-specific configs
│   │   ├── niri/                # Niri window manager (experimental)
│   │   └── [apps]/              # Other tools
│   ├── ssh/                     # SSH config
│   ├── secrets/                 # Encrypted secrets
│   └── local/bin/               # Scripts for ~/.local/bin/
│
├── system/                      # System-wide configurations
│   ├── env_vars.yaml            # Single source of truth for environment variables
│   │                             # - global: Applied to all machines
│   │                             # - machines: Machine-specific overrides/additions
│   ├── hosts                    # /etc/hosts entries (Linux only)
│   └── sudoers.d/               # sudo configuration (Linux only)
│
├── setup/                       # Setup orchestration modules
│   ├── config.py                # MERGE_DIRS: declarative merge/symlink config
│   ├── symlink_utils.py         # Core symlink & merge logic
│   ├── symlink_setup.py         # Symlink phase orchestration
│   ├── merge_setup.py           # Merge phase orchestration
│   ├── ssh_setup.py             # SSH authorized_keys and config
│   ├── systemd_setup.py         # Systemd service symlink and reload
│   ├── crontab_setup.py         # Backup crontab setup
│   ├── hosts_setup.py           # /etc/hosts entries
│   ├── sudoers_setup.py         # /etc/sudoers.d/ configuration
│   ├── security_setup.py        # /etc/security/ configuration
│   ├── pam_setup.py             # PAM configuration
│   ├── pacman_setup.py          # Pacman hooks and config (Arch Linux)
│   ├── resolved_setup.py        # systemd-resolved configuration
│   ├── claude_setup.py          # Claude Code MCP server configuration
│   ├── env_distribution.py      # Environment variable distribution
│   ├── dictation_setup.py       # Voice-to-text system setup
│   ├── beads_setup.py           # Beads file sync integration
│   ├── backup_setup.py          # Application config backups
│   ├── desktop_setup.py         # .desktop file installation
│   ├── zen_windowrule_setup.py  # Hyprland Zen window rule generation
│   └── __pycache__/             # Compiled Python (gitignored)
│
└── docs/                        # Documentation
    └── [markdown files]/
```

## Directory Purposes

**setup.py (Root):**
- Purpose: Main orchestrator and CLI entry point
- Execution order: Merge → Symlink → Environment → Secrets → System setup
- Responsibilities: Hostname detection, step sequencing, error handling

**machines.py (Root):**
- Purpose: Machine definitions and platform abstraction
- Responsibilities: Define MACHINES dict, provide `get_machine_config()` function
- Used by: All setup modules requiring platform/machine awareness

**setup/ (Setup Modules):**
- Purpose: Modular setup implementations
- Pattern: Each file implements a single `setup_*()` function
- Lifecycle: Imported by setup.py, called in sequence during orchestration

**setup/config.py:**
- Purpose: Single source of truth for merge and symlink rules
- Structure: MERGE_DIRS dict maps logical names to source/target/symlink paths
- Used by: merge_setup.py, symlink_setup.py, backup_setup.py
- Maintainability: Add new entry to MERGE_DIRS to enable auto-merge+symlink for a directory

**setup/symlink_utils.py:**
- Purpose: Core algorithms for merging and symlinking
- Key functions: `create_symlink()`, `merge_common_into_machine()`
- Used by: symlink_setup.py, merge_setup.py, all domain-specific setup modules

**common/:**
- Purpose: Cross-machine shared configurations
- Merged into: All machine directories during merge phase
- Git-tracked: All files (source of truth)
- Contents: Common app configs, SSH authorized_keys, universal settings

**linuxcommon/:**
- Purpose: Cross-Linux shared configurations
- Merged into: linuxmini, oldmbp (Linux machines only)
- Git-tracked: All files
- Contents: Hyprland, systemd, Linux-specific tools

**{linuxmini,workmbp,oldmbp}/:**
- Purpose: Machine-specific configuration overlays
- Structure: Mirrors repository structure (config/, systemd/, secrets/, ssh/, etc.)
- Git-tracked: Source files in machine directories
- Ignored: Auto-generated symlinks in config/ subdirectories
- Responsibilities: Store machine-specific overrides and additions

**{machine}/systemd/user/:**
- Purpose: Systemd user services (managed by systemd_setup.py)
- Organization: Subdirectories for logical grouping (_waybar/, _mqtt/, _dunst/)
- Git-tracked: Service files in subdirectories
- Ignored: Top-level symlinks created by setup.py
- Activation: Symlinked to `~/.config/systemd/user/` by systemd_setup.py

**{machine}/scripts/:**
- Purpose: Shell and Python scripts for various tasks
- Organization: _utils/ for shared utilities, backup/ for backup jobs, etc.
- Git-tracked: All scripts
- Used by: Backup crontab, manual invocation, shell workflows

**{machine}/python-tools/:**
- Purpose: Custom Python CLI packages (Python package structures)
- Organization: Each subdirectory is a complete Python package
- Git-tracked: Setup.py and package files
- Installation: `pip install -e` during setup phase
- Used by: Manually from CLI, systemd services

**{machine}/secrets/:**
- Purpose: Encrypted sensitive configurations
- Format: SOPS-encrypted YAML files (plaintext names visible, contents encrypted)
- Decryption: setup.py and individual setup modules decrypt on demand
- Key file: `~/.config/sops/age/keys.txt` (local machine key)

**system/:**
- Purpose: System-wide configurations across all machines
- env_vars.yaml: Single source of truth for environment variables
  - Global section: Applied to all machines
  - machines section: Machine-specific overrides
  - Distribution: Generates ~/.config/environment.d/env_vars.conf and per-WM configs
- hosts: /etc/hosts entries
- sudoers.d/: sudo configuration rules

## Key File Locations

**Entry Points:**
- `setup.py` - Main orchestrator CLI
- `setup/config.py` - Configuration center (MERGE_DIRS, BACKUP_CONFIGS)

**Configuration:**
- `system/env_vars.yaml` - Environment variable definitions
- `setup/config.py` - Merge and symlink rules
- `machines.py` - Machine definitions

**Core Logic:**
- `setup/symlink_utils.py` - Merge and symlink algorithms
- `setup/merge_setup.py` - Merge phase orchestration
- `setup/symlink_setup.py` - Symlink phase orchestration

**Testing/Validation:**
- No automated test suite (design: integration tests only during manual setup.py runs)
- Validation via symlink checks, error handling for broken symlinks

**Application Configs (Shared):**
- `common/config/fish/` - Shell configuration
- `common/config/nvim/` - Neovim setup
- `common/config/git/` - Git configuration

**Application Configs (Machine-Specific):**
- `linuxmini/config/hypr/` - Hyprland setup
- `workmbp/config/karabiner/` - Keyboard remapping (macOS)

**Systemd Services:**
- `linuxmini/systemd/user/_waybar/` - Waybar service definitions
- `linuxmini/systemd/user/_mqtt/` - MQTT services
- `linuxmini/systemd/user/_dunst/` - Dunst services

**Scripts:**
- `linuxmini/scripts/_utils/` - Shared Python utilities
- `linuxmini/scripts/backup/` - Backup job scripts

**Python Tools:**
- `linuxmini/python-tools/cjar/` - Container jar CLI
- `linuxmini/python-tools/hypr-window-ops/` - Hyprland window management
- `linuxmini/python-tools/kanata-tools/` - Keyboard configuration

## Naming Conventions

**Files:**
- Setup modules: `{component}_setup.py` (e.g., `ssh_setup.py`, `systemd_setup.py`)
- Main orchestrator: `setup.py`
- Configuration utilities: `config.py`, `symlink_utils.py`
- Shell scripts: lowercase with underscores (e.g., `bkup_buku.py`)
- Python modules: PEP 8 - lowercase with underscores
- Python packages: lowercase, no underscores (e.g., `cjar`, `hypr_window_ops`)

**Directories:**
- Machine names: lowercase (linuxmini, workmbp, oldmbp)
- Config app names: lowercase (nvim, fish, git, hypr, kanata)
- Systemd subdirectories: prefix with underscore and category name (\_waybar/, \_mqtt/, \_dunst/)
- Utility modules: prefix with underscore (\_utils/)
- Backup directories: bkup/ for backed-up configs

**Functions (Python):**
- Setup functions: `setup_{component}(dotfiles_dir, ...)` (e.g., `setup_ssh()`)
- Utility functions: `{action}_{subject}()` (e.g., `merge_common_into_machine()`)
- Private functions: prefix with underscore (e.g., `_handle_special_cases()`)

**Types (Python):**
- None (project doesn't use type annotations extensively)

## Where to Add New Code

**New Application Configuration:**
1. Create `common/config/{appname}/` if shared across all machines
2. Or create `{machine}/config/{appname}/` for machine-specific config
3. If merging required: Add entry to MERGE_DIRS in `setup/config.py`
4. Run `cd ~/.dotfiles && python setup.py` to apply

**New Systemd Service (Linux):**
1. Create service file in `linuxmini/systemd/user/_category/{service}.service`
2. Example: `linuxmini/systemd/user/_mqtt/mqtt-listener.service`
3. systemd_setup.py automatically symlinks subdirectories to top level
4. Run setup.py to activate

**New Environment Variable:**
1. Add to `system/env_vars.yaml` under appropriate scope:
   - `global:` for all machines
   - `machines.{hostname}:` for machine-specific
2. Run setup.py to generate ~/.config/environment.d/env_vars.conf

**New Secrets Configuration:**
1. Create or edit `{machine}/secrets/{tool}.yaml`
2. Use `{{placeholder}}` syntax for values to substitute
3. Encrypt with SOPS: `sops {machine}/secrets/{tool}.yaml`
4. setup.py decrypts and substitutes during claude_setup phase

**New Setup Module:**
1. Create `setup/{component}_setup.py` with function `setup_{component}(dotfiles_dir, [hostname], [machine_config])`
2. Import and call from setup.py in appropriate sequence
3. Follow error handling pattern: capture exceptions, print warnings, continue

**New Python Tool:**
1. Create `linuxmini/python-tools/{tool_name}/` directory
2. Follow Python package structure: `setup.py`, `{tool_name}/__init__.py`, `{tool_name}/{module}.py`
3. Entry point in `{tool_name}/__init__.py` via `__main__.py`
4. Install via `pip install -e` during setup phase or manually

**New Shell Script:**
1. Create in `{machine}/scripts/{category}/{script_name}.py` or `.sh`
2. Add utility imports if shared: `from _utils.logging_utils import get_logger`
3. Scripts in `scripts/` are symlinked to `~/.config/scripts/`

## Special Directories

**{machine}/config/ (During Setup):**
- Purpose: Build area for merge+symlink process
- Generated: Symlinks created from common/ and linuxcommon/ during merge phase
- Committed: Machine-specific overrides and new configs
- Ignored: Auto-generated symlinks (tracked in .gitignore with markers)
- Lifecycle: Can be safely deleted; setup.py will rebuild

**{machine}/systemd/user/ (Services):**
- Purpose: Organize systemd services by category
- Generated: Subdirectories contain actual service files (tracked)
- Committed: Service files in subdirectories
- Ignored: Top-level symlinks (auto-created by systemd_setup.py, gitignored)
- Lifecycle: Symlinks regenerated each setup.py run

**{machine}/secrets/ (Encrypted):**
- Purpose: Store encrypted sensitive data
- Format: SOPS-encrypted YAML (filenames visible, contents encrypted)
- Committed: Encrypted files (safe to check in)
- Ignored: Decrypted versions (never written to disk)
- Decryption: On-demand during setup phases requiring secrets

**.planning/codebase/ (GSD Output):**
- Purpose: Architecture and structure analysis by GSD mapper
- Format: Markdown documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Committed: Yes (helpful for code review, onboarding)
- Generated: By /gsd:map-codebase command
- Usage: Referenced by /gsd:plan-phase to understand codebase patterns

---

*Structure analysis: 2026-02-10*
