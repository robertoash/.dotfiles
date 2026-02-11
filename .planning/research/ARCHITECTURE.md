# Architecture: Dotfiles Management

**Research Date:** 2026-02-10
**Confidence:** HIGH

## Current Architecture Assessment

**Pattern:** Hierarchical merge + symlink orchestration with modular plugin architecture

**Strengths:**
- Clean separation of concerns (each setup module independent)
- Hierarchical merge allows common configs with machine-specific overrides
- SOPS template substitution cleanly separated from main logic
- Python enables arbitrary logic (vs YAML/templating constraints)

## Architectural Patterns

### 1. Hierarchical Merge Architecture
**Current:** common → linuxcommon → machine-specific
**Strength:** Maximizes reuse while allowing overrides
**Gap:** No visibility into what's being overridden (silent shadowing)

### 2. Plugin Architecture for Setup Steps
**Current:** Each setup module (`ssh_setup.py`, `systemd_setup.py`, etc.) is independent
**Strength:** Easy to extend, clear boundaries
**Gap:** No dependency declaration between modules

### 3. Declarative Configuration
**Current:** YAML for merge rules, SOPS for secrets, Python for orchestration
**Strength:** Configuration is data, logic is code (appropriate separation)
**Gap:** Some logic buried in orchestration that could be declarative

### 4. Symlink-Based Deployment
**Current:** Merge creates machine-specific staging, then symlink to system locations
**Strength:** Changes to dotfiles immediately reflected in system
**Gap:** No rollback mechanism, broken symlink cleanup

### 5. Secrets Template Substitution
**Current:** SOPS + age + template `{{key}}` substitution in `tools.yaml`
**Strength:** Secrets encrypted in git, per-machine keys
**Gap:** Only works in `tools.yaml`, not general-purpose templating

## Anti-Patterns & Remediation

### 1. Silent Merge Shadowing
**Problem:** Machine files override common with no visibility
**Impact:** Hard to debug why config differs between machines
**Fix:** Add `--check-shadows` diagnostic showing what's overridden

### 2. No Dependency Declaration
**Problem:** Setup steps run in hardcoded order in `setup.py`
**Impact:** Adding new steps requires understanding implicit dependencies
**Fix:** Add explicit dependency metadata to setup modules

### 3. Fire-and-Forget Execution
**Problem:** No dry-run, no preview, no validation before changes
**Impact:** Mistakes deployed immediately to live system
**Fix:** Add dry-run mode, validation phase, diff preview

## Improvement Opportunities

Priority-ordered by dependency graph:

| # | Improvement | Complexity | Impact | Blocks |
|---|-------------|-----------|--------|---------|
| 1 | **Dry-run mode** | MEDIUM | HIGH | Diff, validation, rollback |
| 2 | **Module dependency metadata** | LOW | MEDIUM | Selective apply, parallel execution |
| 3 | **State tracking (.state/)** | MEDIUM | HIGH | Run-once, drift, rollback |
| 4 | **Shadow detection** | LOW | MEDIUM | None |
| 5 | **Broken symlink cleanup** | LOW | MEDIUM | None |
| 6 | **General-purpose templating** | HIGH | HIGH | None |
| 7 | **Rollback mechanism** | HIGH | MEDIUM | Dry-run, state tracking |

## Scaling Considerations

### 1-3 Machines (Current)
- Hierarchical merge works well
- Manual testing acceptable
- Current architecture sufficient

### 4-10 Machines
- Need: Shadow detection to prevent override confusion
- Need: Health check/audit to validate consistency
- Need: Drift detection to catch manual changes

### 10+ Machines
- Need: Parallel execution of independent modules
- Need: Remote deployment orchestration
- Consider: Centralized state tracking
- Consider: Automated testing framework

## Integration Points

### External Services
- **SOPS/age:** Secret encryption/decryption
- **Git:** Version control, change tracking
- **Systemd:** Service/timer management (Linux)
- **Crontab:** Job scheduling
- **Claude Code MCP:** Tool configuration

### Internal Boundaries
- **Orchestrator → Setup Modules:** Clean plugin interface
- **Merge → Symlink:** Staging directory handoff
- **Secrets → Templates:** SOPS key substitution
- **Config → Modules:** Declarative rules consumption

## Recommended Patterns

**Keep:**
- Plugin architecture for setup modules
- Hierarchical merge for config reuse
- Python for orchestration logic
- Symlink-based deployment

**Add:**
- Dry-run mode for safety
- State tracking for persistence
- Module dependency metadata
- Shadow detection for visibility

**Avoid:**
- Bash scripts for complex logic (use Python)
- Frameworks that replace current architecture (chezmoi, Ansible)
- Real-time sync mechanisms (race conditions)
- Monolithic orchestration (keep modular)
