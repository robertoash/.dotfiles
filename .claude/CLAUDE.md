# Dotfiles Project Instructions

## Dotfiles Management (CRITICAL)

**NEVER directly modify:**
- ~/.config/*
- ~/.local/bin/*
- ~/.ssh/config
- /etc/hosts
- /etc/sudoers.d/*
- systemd units
- crontab

**ALWAYS:**
1. Modify source files in `~/.dotfiles/{hostname}/` or `~/.dotfiles/common/`
2. Run `cd ~/.dotfiles && python setup.py` to apply changes
3. The repo uses symlinks - changes must be to source files, not symlinked targets

**Exceptions require:**
- Clear justification why dotfiles approach won't work
- Explicit user approval before proceeding

**Example workflow:**
```bash
# ❌ WRONG: vim ~/.config/nvim/init.lua
# ✅ RIGHT:
vim ~/.dotfiles/common/config/nvim/init.lua
cd ~/.dotfiles && python setup.py
```

<!-- CODEGRAPH_START -->
## CodeGraph

CodeGraph builds a semantic knowledge graph of codebases for faster, smarter code exploration.

### If `.codegraph/` exists in the project

**Use codegraph tools for faster exploration.** These tools provide instant lookups via the code graph instead of scanning files:

| Tool | Use For |
|------|---------|
| `codegraph_search` | Find symbols by name (functions, classes, types) |
| `codegraph_context` | Get relevant code context for a task |
| `codegraph_callers` | Find what calls a function |
| `codegraph_callees` | Find what a function calls |
| `codegraph_impact` | See what's affected by changing a symbol |
| `codegraph_node` | Get details + source code for a symbol |

**When spawning Explore agents in a codegraph-enabled project:**

Tell the Explore agent to use codegraph tools for faster exploration.

**For quick lookups in the main session:**
- Use `codegraph_search` instead of grep for finding symbols
- Use `codegraph_callers`/`codegraph_callees` to trace code flow
- Use `codegraph_impact` before making changes to see what's affected

### If `.codegraph/` does NOT exist

At the start of a session, ask the user if they'd like to initialize CodeGraph:

"I notice this project doesn't have CodeGraph initialized. Would you like me to run `codegraph init -i` to build a code knowledge graph?"
<!-- CODEGRAPH_END -->
