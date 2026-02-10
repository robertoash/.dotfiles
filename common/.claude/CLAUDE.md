## General
- I use fish shell. Any shell scripts must be compatible if not to be run with `bash -c`
- Remember that claude-code doesnt have sudo access so I will have to run any sudo commands manually and share the relevant output

## Research-First Policy
- If you encounter an error or issue you don't immediately understand, use WebSearch/WebFetch to look up the exact error message or problem BEFORE attempting speculative fixes
- After ONE failed attempt at something, if the solution isn't obvious from the error message, STOP and search online for the correct approach
- When working with unfamiliar tools, APIs, configuration formats, or syntax, look up the official documentation FIRST using WebFetch/WebSearch before attempting to write code
- If you find yourself saying "let me try..." more than once for the same issue, that's a signal to search online instead

## Code Guidelines
- Never add "Generated with Claude Code" and "Co-Authored-By: Claude" lines to commit messages. It's unnecesary bloat.
- Remembrance comments are comments designed to give context to code that no longer exists. It explains, for example, why something was removed. They dont make any sense to those not directly involved in the project at that point in time. We never use remembrance comments in our codebase. Comments should be concise and always give context to existing code (preferrably in the near vicinity of the comment).

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
