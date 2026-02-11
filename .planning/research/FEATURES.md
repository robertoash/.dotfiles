# Features: Dotfiles Management

**Research Date:** 2026-02-10
**Confidence:** HIGH

## Table Stakes Gaps

Features that competitors (chezmoi, yadm, stow) all provide but this system lacks:

| Feature | Complexity | Dependency | Priority |
|---------|-----------|------------|----------|
| **Dry-run/preview mode** | LOW | None | P0 |
| **Health check/audit** | MEDIUM | Dry-run | P0 |
| **Selective apply** | MEDIUM | Module refactor | P1 |
| **Diff before apply** | MEDIUM | Dry-run | P1 |
| **Idempotent improvements** | MEDIUM | Code review | P1 |

**Rationale:** The current fire-and-forget model creates friction. Dry-run and health check are foundational - everything else builds on them.

## Differentiators

Advanced capabilities that would set this apart:

| Feature | Complexity | Dependency | Value |
|---------|-----------|------------|-------|
| **Per-file templating (Jinja2)** | HIGH | None | HIGH |
| **Drift detection** | MEDIUM | State tracking | HIGH |
| **Run-once scripts** | LOW | State tracking | MEDIUM |
| **Timing/performance reporting** | LOW | None | MEDIUM |
| **Rollback capability** | HIGH | State tracking | MEDIUM |

**Rationale:** Templating handles single-line differences without file duplication. Drift detection catches manual changes. Run-once scripts enable progressive setup steps.

## Anti-Features (Deliberately Avoid)

| Feature | Why NOT |
|---------|---------|
| **Migrate to chezmoi/Nix/yadm** | Current system more flexible, migration cost exceeds benefit |
| **Real-time sync/auto-commit** | Race conditions, conflicts, loss of control |
| **GUI/TUI** | Complexity, maintenance burden, `setup.py` simplicity is strength |
| **Container testing** | Overkill, real machines are the test environment |

## Current System Strengths

What this system does better than any generic tool:

- **SOPS secrets with per-machine key scoping**
- **MCP server configuration for Claude Code**
- **Env var distribution to multiple targets** (systemd, hyprland, shell)
- **System config management** (/etc/hosts, sudoers, PAM, resolved)
- **Hierarchical merge** (common → linuxcommon → machine)
- **Modular plugin architecture** for setup steps

## Feature Dependencies

```
State Tracking (.state/ directory)
├── Run-once scripts
├── Rollback capability
└── Drift detection

Dry-run Mode
├── Diff before apply
├── Health check
└── Better error messages

Module Refactoring
└── Selective apply
```

## Phase Recommendations

**Phase 1 - Operational Foundation:**
- Dry-run mode (foundational)
- Health check/audit
- Idempotent improvements

**Phase 2 - Developer Experience:**
- Diff before apply
- Drift detection
- Run-once scripts
- Per-file templating
- Timing reporting

**Phase 3 - Advanced (Optional):**
- Rollback capability
- Bootstrap one-liner
- Selective apply
- Package management integration

## Open Questions

- **Templating delimiter:** Jinja2 uses `{{}}` like SOPS placeholders - conflict?
- **State format:** JSON (git-friendly) vs SQLite (concurrent-safe)?
- **Bootstrap scope:** Dotfiles only or include OS package installation?
- **Rollback granularity:** Per-module or whole-system?
