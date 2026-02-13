# Roadmap: Dotfiles Management

## Overview

The dotfiles system is architecturally sound but lacks operational tooling for safe deployment, visibility, and quality assurance. This roadmap closes table-stakes gaps (dry-run, health checks, drift detection) that every competing tool already has, then adds developer experience improvements that build on that foundation. Phase 2 is optional scope, pursued only if phases 1-2 prove their value.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

| # | Name | Status | Completed |
|---|------|--------|-----------|
| 1 | idle_detection_reliability | ✓ Complete | 2026-02-12 |
| 2 | fish +Tab autocomplete robustness | ○ Pending | - |

## Phase Details

### Phase 1: idle_detection_reliability ✓

**Goal:** Fix crashed MQTT services, eliminate paho-mqtt API incompatibility, harden systemd restart policies so the idle detection system reliably communicates with Home Assistant
**Depends on:** Phase 0
**Plans:** 2 plans
**Status:** Complete
**Completed:** 2026-02-12

Plans:
- [x] 01-01-PLAN.md — Fix paho-mqtt 1.6.x compatibility and reconnection logic in both MQTT scripts
- [x] 01-02-PLAN.md — Harden all idle detection systemd service units with restart policies

### Phase 2: fish +Tab autocomplete robustness

**Goal:** Refactor Tab completion into a unified, context-aware system that: (1) merges all sources (zoxide, fish completions, fre, history, fd) with smart prioritization based on command intent, (2) achieves extreme speed, (3) supports remote path completion via SSH, (4) uses only Tab/Shift+Tab keybinds with intelligent context switching, (5) is well-tested across all scenarios, and (6) is implemented in the fastest technology (fish/Python/Rust)
**Depends on:** Phase 1
**Plans:** 4 plans

Plans:
- [ ] 02-01-PLAN.md — Command categorization config and multi-source completion candidate engine
- [ ] 02-02-PLAN.md — Remote path completion via SSH for scp/rsync/sftp
- [ ] 02-03-PLAN.md — Smart Tab handler rewrite + Shift+Tab frecency picker + keybindings
- [ ] 02-04-PLAN.md — Legacy code cleanup and comprehensive interactive verification
