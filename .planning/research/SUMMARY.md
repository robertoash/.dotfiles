# Research Summary: Dotfiles Management

**Research Date:** 2026-02-10
**Project:** Dotfiles Management System
**Mode:** Brownfield (maintenance & improvement)

## Executive Summary

The existing dotfiles system is **architecturally sound and more flexible than any generic tool** (chezmoi, yadm, Nix Home Manager). No migration needed. The primary gaps are **operational tooling** (dry-run, health checks, drift detection) rather than core features.

## Key Findings

### Stack (Keep Current)
- **Python + SOPS + age + uv + symlinks** is the right stack ✓
- Current system provides arbitrary logic capability that templating-based tools lack
- Add: ruff + pre-commit for code quality (table stakes missing)
- Reject: Framework migrations (chezmoi, Nix, Ansible) - migration cost exceeds benefit

### Features (Close Table Stakes Gaps)
**P0 Gaps (All competitors have these):**
- Dry-run/preview mode
- Health check/audit command
- Diff before apply

**High-Value Differentiators:**
- Per-file templating (Jinja2) - handles single-line machine differences
- Drift detection - catches manual config changes
- Run-once scripts - progressive setup steps

**Current Strengths (Better than any tool):**
- SOPS secrets with per-machine keys
- MCP server configuration
- Env var distribution to multiple targets
- System config management (/etc/hosts, sudoers, PAM)
- Hierarchical merge architecture

### Architecture (Solid Foundation, Needs Tooling)
**Patterns to Keep:**
- Plugin architecture for setup modules ✓
- Hierarchical merge (common → linuxcommon → machine) ✓
- Python orchestration ✓
- Symlink deployment ✓

**Critical Improvements:**
1. Dry-run mode (foundational - blocks everything else)
2. State tracking (.state/ directory) - enables run-once, drift, rollback
3. Shadow detection - visibility into what machine configs override
4. Broken symlink cleanup - deployment targets need validation

**Anti-Patterns to Fix:**
- Silent merge shadowing (no visibility into overrides)
- No dependency declaration between modules
- Fire-and-forget execution (no validation before deploy)

### Pitfalls (Domain-Specific Mistakes)
**Top Risks:**
1. **Editing symlink targets** - changes lost on next setup.py run
2. **Secrets in plaintext** - SOPS path_regex must be manually extended
3. **Apps breaking symlinks** - atomic-write destroys symlinks (need BACKUP_CONFIGS)
4. **Silent merge precedence** - machine shadows common with no warning
5. **Stale symlink cleanup** - broken links left in ~/.config/

**Prevention:**
- Every new app: test symlink persistence
- Every new secret: 5-step SOPS checklist
- Config refactors: run --check-shadows diagnostic

## Roadmap Implications

### Phase Priority Order

**Phase 1: Operational Foundation** (Unblocks everything)
- Dry-run mode ← foundational
- Health check/audit
- Idempotent improvements
- Shadow detection

**Phase 2: Developer Experience** (Builds on foundation)
- Diff before apply
- Drift detection
- Run-once scripts
- Per-file templating
- Broken symlink cleanup

**Phase 3: Advanced** (Optional, after proving value)
- Rollback capability
- Bootstrap one-liner
- Selective module apply
- Package management integration

### Critical Dependencies

```
Dry-run Mode
├── Diff before apply
├── Health check
└── Validation before deploy

State Tracking (.state/)
├── Run-once scripts
├── Drift detection
└── Rollback capability

Module Refactoring
└── Selective apply
```

## Confidence Assessment

| Area | Confidence | Reason |
|------|-----------|--------|
| Stack (keep current) | HIGH | Verified versions, compared alternatives |
| Table stakes gaps | HIGH | Verified against chezmoi, yadm, stow docs |
| Architecture patterns | HIGH | Based on codebase analysis |
| Pitfalls | HIGH | Direct code analysis + community patterns |
| Priorities | MEDIUM | Dependency-based, but some judgment calls |

## Open Questions for Requirements

1. **Templating delimiter:** Jinja2 uses `{{}}` like SOPS - conflict?
2. **State format:** JSON (git-friendly) vs SQLite (concurrent-safe)?
3. **Bootstrap scope:** Dotfiles only or include OS packages?
4. **Rollback granularity:** Per-module or whole-system?
5. **Dry-run scope:** Preview changes or just validate?

## Anti-Features (Deliberately Reject)

- ❌ Migrate to chezmoi/Nix/yadm
- ❌ Real-time sync / auto-commit
- ❌ GUI/TUI
- ❌ Container-based testing
- ❌ Bash scripts for complex logic

## Next Steps

Move to **requirements definition** with this context:
- Scope: Operational foundation (dry-run, health check, shadow detection)
- Build order: Dry-run first, then everything else can build on it
- Quality: Add ruff + pre-commit early
- Pitfalls: Every phase must account for relevant risks
