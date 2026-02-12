# Roadmap: Dotfiles Management

## Overview

The dotfiles system is architecturally sound but lacks operational tooling for safe deployment, visibility, and quality assurance. This roadmap closes table-stakes gaps (dry-run, health checks, drift detection) that every competing tool already has, then adds developer experience improvements that build on that foundation. Phase 3 is optional scope, pursued only if phases 1-2 prove their value.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Operational Foundation** - Safe deployment preview, system health validation, and code quality tooling
- [ ] **Phase 2: Developer Experience** - Change visibility, drift detection, and automated cleanup

## Phase Details

### Phase 1: Operational Foundation
**Goal**: Users can preview and validate deployments before applying changes, with enforced code quality
**Depends on**: Nothing (first phase)
**Requirements**: DRY-01, HEALTH-01, SHADOW-01, QUALITY-01
**Success Criteria** (what must be TRUE):
  1. Running `setup.py --dry-run` prints every file operation (symlink, copy, system config change) that would occur, without modifying the filesystem
  2. Running `setup.py --health-check` reports whether current symlinks are intact, point to correct targets, and required files exist
  3. Running `setup.py --check-shadows` lists every machine-specific config that overrides a common config, with both file paths shown
  4. `ruff check` and `ruff format --check` pass on all Python files in the repo, enforced by a pre-commit hook
  5. All existing setup.py functionality still works identically (no regressions)
**Plans**: TBD

Plans:
- [ ] 01-01: Dry-run mode and health check infrastructure
- [ ] 01-02: Shadow detection and code quality tooling

### Phase 2: Developer Experience
**Goal**: Users have full visibility into what changes during deployment, can detect configuration drift, and stale state is automatically cleaned
**Depends on**: Phase 1 (dry-run infrastructure)
**Requirements**: DIFF-01, DRIFT-01, CLEANUP-01, RUNONCE-01
**Success Criteria** (what must be TRUE):
  1. Before applying changes, `setup.py` shows a diff of every file that would be modified or replaced, and waits for confirmation (or proceeds with `--yes`)
  2. Running `setup.py --check-drift` identifies files in deployment targets that have been modified since last setup.py run (content differs from dotfiles source)
  3. After setup completes, broken symlinks in deployment targets that previously pointed to dotfiles are automatically removed
  4. Scripts in a designated run-once directory execute only on first setup (tracked via `.state/` directory), and are skipped on subsequent runs
  5. A `.state/` directory persists deployment metadata (timestamps, checksums) between setup.py runs
**Plans**: TBD

Plans:
- [ ] 02-01: Diff-before-apply and state tracking infrastructure
- [ ] 02-02: Drift detection and broken symlink cleanup
- [ ] 02-03: Run-once script execution
