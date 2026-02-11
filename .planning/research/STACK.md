# Stack: Dotfiles Management

**Research Date:** 2026-02-10
**Confidence:** HIGH

## Current Stack Assessment

**Verdict:** The existing custom Python + SOPS + symlink stack is the right approach. Keep it.

### Core Technologies (Keep)

| Technology | Current | Latest | Recommendation |
|------------|---------|--------|----------------|
| **Python** | 3.x | 3.13+ | Keep - arbitrary logic capability essential |
| **uv** | Used | 0.10.0 | Keep - PEP 723 inline metadata, zero config overhead |
| **SOPS** | Used | 3.11.0 | Keep - CNCF sandbox project, gold standard for secrets-in-git |
| **age** | Used | 1.3.1 | Keep - per-machine keys, YubiKey support in 1.3.1 |
| **Symlinks** | Core | N/A | Keep - standard Unix pattern, works everywhere |

**Rationale:** The main alternatives (chezmoi, yadm, Nix Home Manager) would each be a downgrade in flexibility. This system already implements their key features via Python, which provides arbitrary logic capability (e.g., `claude_setup.py`, `env_distribution.py`).

### Quality Tooling (Add)

| Tool | Version | Purpose | Priority |
|------|---------|---------|----------|
| **ruff** | 0.15.0 | Linting + formatting, replaces multiple tools | HIGH |
| **pre-commit** | 4.5.1 | Git hooks for quality gates | HIGH |
| **pytest** | 9.1 | Testing framework for setup modules | MEDIUM |
| **rich** | 14.3.x | Better terminal output | LOW |

**Rationale:** Main gaps are in quality tooling, not core stack. Ruff + pre-commit provide code quality with minimal overhead.

### Optional Enhancements

| Tool | Version | Purpose | When to Add |
|------|---------|---------|-------------|
| **typer** | Latest | CLI subcommands (deploy/verify/backup/diff) | If CLI expansion needed |
| **deepdiff** | Latest | Drift detection comparisons | If drift detection phase planned |
| **age plugin** | 1.3.1+ | Hardware key storage (YubiKey) | If higher security desired |

## Alternatives Considered (Reject)

### chezmoi
- **Pros:** Popular, feature-rich, templating
- **Cons:** Go templates less flexible than Python, migration cost high
- **Verdict:** REJECT - Current system more flexible

### Nix Home Manager
- **Pros:** Declarative, reproducible, package management
- **Cons:** Steep learning curve, conflicts with existing architecture
- **Verdict:** REJECT - Massive migration cost, overkill for dotfiles

### Ansible
- **Pros:** Industry standard, YAML-based
- **Cons:** Heavy dependency, slower than Python, less flexible
- **Verdict:** REJECT - Python orchestration already optimal

### yadm
- **Pros:** Simple, git-based
- **Cons:** Less capable than current system, no hierarchical merge
- **Verdict:** REJECT - Current system superior

## Implementation Notes

**Early phase recommendations:**
- Add ruff for linting/formatting (replaces black, isort, flake8)
- Add pre-commit for git hooks (enforce quality gates)

**Mid phase (if refactoring):**
- Add pytest for setup module regression testing

**Do NOT plan:**
- Framework migration - current stack is correct
- Rewrite in Go/Rust/etc - Python is optimal for this use case

## Version Verification

All versions verified against:
- PyPI official releases
- GitHub release tags
- Official project documentation
- Current as of 2026-02-10
