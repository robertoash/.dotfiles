# Architecture

**Analysis Date:** 2026-02-10

## Pattern Overview

**Overall:** Multi-machine dotfiles management using a merge-and-symlink orchestration pattern with machine-specific overlays.

**Key Characteristics:**
- Modular, declarative configuration system based on YAML specification
- Hierarchical merge strategy: `common` → `linuxcommon` → `machine-specific`
- Symlink-based config distribution to system standard locations
- Plugin architecture for setup steps (each setup task is a independent module)
- Secrets management via SOPS encryption with template substitution
- Environment variable centralization with per-machine overrides

## Layers

**Orchestration Layer:**
- Purpose: Coordinates all setup steps in proper order
- Location: `setup.py`
- Contains: Main entry point, hostname detection, step sequencing
- Depends on: All setup modules, machines.py, common configuration
- Used by: CLI invocation

**Configuration Layer:**
- Purpose: Declarative system for defining merge and symlink rules
- Location: `setup/config.py`
- Contains: MERGE_DIRS specification, BACKUP_CONFIGS rules
- Depends on: Python pathlib
- Used by: symlink_setup.py, merge_setup.py, backup_setup.py

**Merge & Symlink Core:**
- Purpose: Implements the three-way merge and symlink creation logic
- Locations: `setup/merge_setup.py`, `setup/symlink_setup.py`, `setup/symlink_utils.py`
- Contains: Merge algorithms, symlink creation, gitignore generation
- Depends on: config.py, pathlib
- Used by: Orchestration layer

**Machine & Platform Layer:**
- Purpose: Detects and provides machine-specific configuration flags
- Locations: `machines.py`
- Contains: Machine definitions, platform detection
- Depends on: socket, platform stdlib
- Used by: All setup modules requiring platform/machine awareness

**Setup Modules (Domain-Specific):**
- Purpose: Handle specialized system configurations
- Locations: `setup/{ssh,systemd,crontab,pacman,security,pam,resolved,sudoers,hosts,desktop,launch_agents}_setup.py`
- Contains: Implementations for specific system areas
- Depends on: pathlib, subprocess, config.py
- Used by: Orchestration layer

**Special Setup Modules:**
- **`setup/claude_setup.py`** - Claude Code MCP server configuration with sops-encrypted secret substitution
- **`setup/env_distribution.py`** - Centralizes environment variables from `system/env_vars.yaml` to systemd and shell configs
- **`setup/dictation_setup.py`** - Voice-to-text system integration (Linux Wayland)
- **`setup/zen_windowrule_setup.py`** - Generates Hyprland window rules from JSON

**Config Directory Tree (Source):**
- Purpose: Stores application configurations that will be symlinked
- Locations: `common/config/`, `linuxmini/config/`, `workmbp/config/`, `oldmbp/config/`
- Contains: App configs (nvim, fish, hypr, kanata, etc.)
- Depends on: Nothing (data layer)
- Used by: merge_setup.py, symlink_setup.py

**System Configuration:**
- Purpose: System-level configs and secrets
- Locations: `system/`, `linuxmini/secrets/`, `linuxmini/systemd/`
- Contains: Hosts, sudoers, environment variables, encrypted secrets
- Depends on: SOPS for decryption
- Used by: Various setup modules

**Python Tools:**
- Purpose: Custom CLI utilities for machine-specific tasks
- Locations: `linuxmini/python-tools/{cjar,hypr-window-ops,kanata-tools}/`
- Contains: CLI entry points, domain logic, UI
- Depends on: Standard library
- Used by: Shell workflows, systemd services

## Data Flow

**Setup Execution Flow:**

1. **Machine Detection** (machines.py)
   - `setup.py` calls `get_machine_config(hostname)` to determine OS and machine flags
   - Returns dict with `is_macos`, `is_linux` flags

2. **Merge Phase** (merge_setup.py)
   - For each directory in MERGE_DIRS:
     - `merge_common_directories()` - Symlink items from `common/{source}` → `{hostname}/{target}`
     - For Linux machines: `merge_linuxcommon_directories()` - Symlink items from `linuxcommon/{source}` → `{hostname}/{target}`
     - `merge_machine_specific()` - Handle non-standard source/target pairs
   - Generates `.gitignore` entries for all auto-generated symlinks

3. **Symlink Phase** (symlink_setup.py)
   - For each directory in MERGE_DIRS:
     - If `symlink_mode == "contents"`: Symlink each item inside to destination
     - If `symlink_mode == "directory"`: Symlink entire directory
   - `_handle_special_cases()` for non-standard locations (home/, local/bin/)
   - Validates existing symlinks (won't replace symlinks pointing outside dotfiles)

4. **Environment Distribution** (env_distribution.py)
   - Reads `system/env_vars.yaml`
   - Generates `~/.config/environment.d/env_vars.conf` for systemd user environment
   - Machine-specific merging: machine vars prepended to global vars (for PATH)
   - Generates `{machine}/config/hypr/env.conf` for Hyprland

5. **Secrets & Claude Setup** (claude_setup.py)
   - Reads `{machine}/secrets/tools.yaml`
   - Decrypts sops-encrypted values
   - Substitutes `{{key}}` placeholders with decrypted secrets
   - Generates `~/.config/Claude/claude_config.json`
   - Optionally runs install/update hooks for MCP servers

6. **System Setup** (machine & platform-specific)
   - SSH: Merges authorized_keys from `{machine}/ssh/`
   - Systemd: Symlinks services from `{machine}/systemd/user/` subdirectories
   - Linux-only: Hosts, sudoers, PAM, security configs
   - Crontab: Sets up backup jobs
   - Desktop files: Rsync .desktop files for app launcher integration

**State Management:**
- **Temporary State**: Files in `{machine}/config/` are built during merge phase (symlinks created, gitignore updated)
- **Persistent State**: Only `common/`, `linuxmini/`, `{hostname}/` source trees are git-tracked
- **Runtime State**: Auto-generated symlinks in `{machine}/systemd/user/` and entries in `.gitignore` are git-ignored
- **Secret State**: Encrypted via SOPS in `{machine}/secrets/`

## Key Abstractions

**MERGE_DIRS Configuration:**
- Purpose: Declaratively specify which directories follow the merge+symlink pattern
- Location: `setup/config.py`
- Structure: Dictionary with keys defining source, target, symlink destination, and symlink mode
- Pattern: "Convention over configuration" - one entry in MERGE_DIRS triggers all steps automatically

**Merge Operation:**
- Purpose: Populate machine directory with symlinks to common files
- Function: `merge_common_into_machine()` in `setup/symlink_utils.py`
- Pattern: Recursive traversal, only creates symlinks for items not present in machine dir
- Cleans up broken symlinks (detected as pointing to dotfiles directory)

**Symlink Creation:**
- Purpose: Link resolved source files to standard system locations
- Function: `create_symlink()` in `setup/symlink_utils.py`
- Pattern: Two modes - "contents" (symlink items individually) vs "directory" (symlink entire directory)

**Environment Variable Distribution:**
- Purpose: Single source of truth for all env vars across systems
- Source: `system/env_vars.yaml`
- Targets: `~/.config/environment.d/env_vars.conf` (systemd), `{machine}/config/hypr/env.conf` (Wayland)
- Pattern: Global + machine-specific scopes, PATH merging strategy

**Secrets Substitution:**
- Purpose: Inject decrypted secrets into config templates without committing plaintext
- Process: Read YAML with `{{key}}` placeholders → Decrypt with SOPS → Substitute placeholders
- Location: `setup/claude_setup.py`
- Used by: Claude Code MCP server configuration

**Setup Modules:**
- Purpose: Encapsulate domain-specific setup logic
- Pattern: Each module defines a single `setup_*()` function taking `dotfiles_dir`, optional machine/hostname args
- Examples: `setup_ssh()`, `setup_systemd()`, `setup_sudoers()`

## Entry Points

**CLI Entry:**
- Location: `setup.py`
- Triggers: `cd ~/.dotfiles && python3 setup.py`
- Responsibilities: Detect hostname, sequence all setup steps, print progress

**Per-Module Entry:**
- Each setup module exposes a single entry function imported by `setup.py`
- Examples: `setup_ssh()`, `setup_beads_integration()`, `setup_dictation()`

## Error Handling

**Strategy:** Fail-safe approach with non-blocking warnings for most operations.

**Patterns:**
- **Symlink validation**: Won't replace symlinks pointing outside dotfiles (safety check)
- **Secret decryption failure**: Warns with stderr but continues (Claude setup can retry)
- **Permission errors**: Subprocess calls with error capture, optional sudo for system symlinks
- **Missing prerequisites**: Individual setup modules skip if dependencies not available
- **Broken symlinks**: Automatically cleaned up during merge phase if they point to dotfiles

## Cross-Cutting Concerns

**Logging:**
- Approach: Emoji-based status indicators printed to stdout
- No persistent log file (design choice: output is realtime feedback)
- Verbose mode available in `env_distribution.py`

**Validation:**
- Pre-execution: Machine detection (MACHINES dict or platform fallback)
- Post-execution: .gitignore entries verified, symlinks tested
- Existing state: Won't replace symlinks pointing outside dotfiles (safe)

**Authentication:**
- SSH: Authorized keys merged from `{machine}/ssh/`
- Secrets: SOPS with age encryption, key file at `~/.config/sops/age/keys.txt`
- Sudo: Used only for system-wide symlinks and /usr/local/bin operations

**Configuration Activation:**
- systemd user: Reloads daemon after service setup
- Shell: Fish configs auto-sourced on startup (standard XDG locations)
- Hyprland: Env vars loaded via `env.conf` sourced in hyprland.conf
- Claude: Reads claude_config.json on next restart

---

*Architecture analysis: 2026-02-10*
