# Requirements: Dotfiles Management

**Project:** Dotfiles Management System
**Created:** 2026-02-10
**Status:** Active

## Problem Statement

The dotfiles system works but lacks operational tooling that makes it reliable and debuggable. Key pain points:
- No way to preview changes before applying
- No visibility into which configs override others
- No detection of configuration drift
- Missing quality tooling (linting, formatting)

## Goals

### Primary
1. **Safe deployment** - Preview and validate before applying changes
2. **Visibility** - Understand what's being overridden and why
3. **Quality** - Consistent code style and automated checks
4. **Reliability** - Detect when configs drift from dotfiles source

### Secondary
5. **Flexibility** - Run-once scripts for progressive setup
6. **Efficiency** - Per-file templating to reduce duplication

## In Scope

### Phase 1: Operational Foundation
- **Dry-run mode** - Preview what would change without applying
- **Health check command** - Validate current system state
- **Shadow detection** - Show what machine configs override common
- **Code quality tooling** - Add ruff + pre-commit

### Phase 2: Developer Experience
- **Diff before apply** - Show changes before deployment
- **Drift detection** - Find configs modified outside dotfiles
- **Broken symlink cleanup** - Remove stale symlinks in deployment targets
- **Run-once scripts** - Execute setup steps only on first run

### Phase 3: Advanced (Optional)
- **Per-file templating** - Jinja2 for machine-specific variations
- **Rollback capability** - Undo deployment changes
- **Bootstrap improvements** - Streamline new machine setup

## Out of Scope

- ❌ Framework migration (chezmoi, Nix, yadm, Ansible)
- ❌ Real-time sync or auto-commit
- ❌ GUI/TUI interfaces
- ❌ Container-based testing
- ❌ Rewriting in different language

## Constraints

### Technical
- **Language:** Python for all logic (exceptions: fish functions, simple wrappers)
- **Deployment:** Everything via `uv run setup.py`
- **Architecture:** Fully declarative, no manual steps
- **Compatibility:** Fish shell support required
- **Merge:** Most specific always wins (machine > linuxcommon > common)

### Operational
- **Zero disruption:** Must not break existing setup.py usage
- **Backward compatible:** Existing machines continue working
- **Incremental:** Can deploy phases independently
- **Safe:** Dry-run validates before any changes

## Success Criteria

### Phase 1
- [ ] `setup.py --dry-run` shows what would change
- [ ] `setup.py --health-check` validates current state
- [ ] `setup.py --check-shadows` shows override visibility
- [ ] ruff enforces code style on commit
- [ ] All existing functionality still works

### Phase 2
- [ ] Setup shows diff before applying changes
- [ ] Drift detection identifies manual config edits
- [ ] Stale symlinks automatically cleaned
- [ ] Run-once scripts execute only when needed
- [ ] State tracked in `.state/` directory

### Phase 3
- [ ] Jinja2 templates reduce config duplication
- [ ] Rollback reverts deployment changes
- [ ] Bootstrap process streamlined

## Non-Goals

- Real-time config synchronization (introduces race conditions)
- Multi-user dotfiles (personal configs only)
- Package management (handled by OS tools)
- Application installation (dotfiles configure, don't install)

## Open Decisions

1. **Templating delimiter:** Use `{{}}` (SOPS conflict) or `{%  %}` or `[[]]`?
   - **Recommendation:** `{%  %}` to avoid SOPS collision

2. **State format:** JSON vs SQLite for `.state/` directory?
   - **Recommendation:** JSON (simpler, git-friendly)

3. **Bootstrap scope:** Just dotfiles or include OS packages?
   - **Recommendation:** Start with dotfiles only, expand if needed

4. **Rollback granularity:** Per-module or whole-system?
   - **Recommendation:** Whole-system (simpler, sufficient for personal use)

## Dependencies

```
Dry-run Mode (Phase 1)
├── Diff before apply (Phase 2)
├── Health check (Phase 1)
└── Validation (Phase 1)

State Tracking (Phase 2)
├── Run-once scripts (Phase 2)
├── Drift detection (Phase 2)
└── Rollback (Phase 3)

Code Quality (Phase 1)
└── Pre-commit hooks
```

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Breaking existing setup | Extensive dry-run testing |
| SOPS template conflict | Use different delimiter for Jinja2 |
| State file corruption | Validate JSON schema on read |
| Symlink destruction | Test every app before adding to BACKUP_CONFIGS |
| Secret exposure | Pre-commit hook validates encryption |

## Timeline

**Phase 1:** Operational foundation - priority to unlock other work
**Phase 2:** Developer experience - builds on dry-run infrastructure
**Phase 3:** Advanced features - only if phases 1-2 prove valuable

## Acceptance

Work is done when:
- All success criteria met for completed phases
- No regressions in existing functionality
- Documentation updated (CLAUDE.md, setup module docstrings)
- Changes committed and tested on all active machines
