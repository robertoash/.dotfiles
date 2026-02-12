# Roadmap: Dotfiles Management

## Overview

The dotfiles system is architecturally sound but lacks operational tooling for safe deployment, visibility, and quality assurance. This roadmap closes table-stakes gaps (dry-run, health checks, drift detection) that every competing tool already has, then adds developer experience improvements that build on that foundation. Phase 2 is optional scope, pursued only if phases 1-2 prove their value.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

No phases defined yet.

## Phase Details

No phases defined yet.

### Phase 1: idle_detection_reliability

**Goal:** Fix crashed MQTT services, eliminate paho-mqtt API incompatibility, harden systemd restart policies so the idle detection system reliably communicates with Home Assistant
**Depends on:** Phase 0
**Plans:** 2 plans

Plans:
- [ ] 01-01-PLAN.md — Fix paho-mqtt 1.6.x compatibility and reconnection logic in both MQTT scripts
- [ ] 01-02-PLAN.md — Harden all idle detection systemd service units with restart policies
