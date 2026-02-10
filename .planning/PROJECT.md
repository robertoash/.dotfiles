# Dotfiles Management System

## What This Is

A multi-machine dotfiles management system that declares and backs up configuration from all machines with heavy focus on reusability for consistent experience everywhere. Deployed to any machine with a single command: `uv run setup.py`.

## Core Value

Any machine can be configured identically with one command. All configuration is declarative and versioned - no manual fixes, no drift.

## Requirements

### Validated

<!-- Existing functionality from brownfield codebase -->

- ✓ Multi-machine config management with hierarchical merge (common → linuxcommon → machine-specific) — existing
- ✓ Symlink-based deployment to standard system locations (~/.config, ~/.local/bin, etc.) — existing
- ✓ Secrets management via SOPS encryption with template substitution — existing
- ✓ Environment variable centralization with per-machine overrides — existing
- ✓ SSH config and authorized_keys management — existing
- ✓ Systemd service and timer installation (Linux) — existing
- ✓ Crontab management (user and root) — existing
- ✓ System configuration (/etc/hosts, sudoers.d, PAM, resolved) — existing
- ✓ Desktop files and launch agents (Linux/macOS) — existing
- ✓ Claude Code MCP server configuration with encrypted secrets — existing
- ✓ Beads integration with hooks — existing
- ✓ Application config backup for symlink-breaking apps — existing
- ✓ Pacman/AUR repository configuration (Arch Linux) — existing

### Active

<!-- Ongoing maintenance scope -->

- [ ] Add new tools and configs as discovered
- [ ] Fix issues and inconsistencies as they arise
- [ ] Improve setup.py reliability and coverage

### Out of Scope

- Manual configuration steps outside setup.py
- Machine-specific changes not integrated back to dotfiles repo

## Context

**Existing System:**
- Sophisticated brownfield codebase with modular plugin architecture
- Supports multiple machines: linuxmini (Arch Linux), oldmbp (macOS), others
- Uses git for version control and beads for issue tracking
- Active integration with Claude Code for AI-assisted maintenance

**Usage Pattern:**
- Continuous maintenance project
- New tools integrated as they're adopted
- Issues fixed as they're discovered
- GSD PROJECT.md prevents Claude from choosing wrong approaches

## Constraints

- **Language**: Python preferred for all scripts (setup.py, local/bin/, anywhere in dotfiles) - exceptions: fish functions and really simple wrappers only
- **Shell**: Fish shell compatibility required - scripts must work with fish, not assume bash
- **Deployment**: Everything via `uv run setup.py` - no manual configuration steps
- **Architecture**: Fully declarative - all changes must be permanently integrated into setup.py system
- **Hierarchy**: common/ applies to all machines, machine-specific overrides take precedence (most specific always wins)
- **Secrets**: Use SOPS encryption for sensitive data, template substitution via tools.yaml
- **Version Control**: All planning docs committed to git (commit_docs: true)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python-based setup system | Type safety, modularity, cross-platform | ✓ Good - robust and maintainable |
| Merge + symlink architecture | Reuse common configs, override when needed | ✓ Good - balances consistency and flexibility |
| SOPS for secrets | Encrypted in git, decrypted on deploy | ✓ Good - secure and version-controlled |
| Plugin architecture for setup modules | Each concern isolated (ssh, systemd, etc.) | ✓ Good - easy to extend |

---
*Last updated: 2026-02-10 after initialization*
