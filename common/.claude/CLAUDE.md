## General
- I use fish shell. Any shell scripts must be compatible if not to be run with `bash -c`
- Remember that claude-code doesnt have sudo access so I will have to run any sudo commands manually and share the relevant output

## Research-First Policy
- If you encounter an error or issue you don't immediately understand, use WebSearch/WebFetch to look up the exact error message or problem BEFORE attempting speculative fixes
- After ONE failed attempt at something, if the solution isn't obvious from the error message, STOP and search online for the correct approach
- When working with unfamiliar tools, APIs, configuration formats, or syntax, look up the official documentation FIRST using WebFetch/WebSearch before attempting to write code
- If you find yourself saying "let me try..." more than once for the same issue, that's a signal to search online instead

## Zellij Integration
When running inside a Zellij session, you have MCP tools to interact with panes. Use these proactively when:
- About to make significant changes to a file the user might want to review in real-time
- Explaining code and pointing to specific lines would benefit from the user seeing it
- Running builds/tests where the user might want to see output and provide feedback
- The user asks to "show me" something

**Showing files/diffs:**
- Use `zellij action` commands via Bash tool:
```bash
zellij action focus-previous-pane && sleep 0.3 && \
zellij action write-chars ':edit /path/to/file' && zellij action write 13 && sleep 0.5 && \
zellij action write-chars ':Gitsigns diffthis' && zellij action write 13 && sleep 0.3 && \
zellij action focus-next-pane
```
- `write 13` sends Enter key (byte 13 = CR)
- Timing: 0.3s for focus switch, 0.5s after opening file
- To close diff first: Add `:diffoff | only` before `:edit` command
- **CRITICAL**: Only one diff per nvim pane at a time. Close existing diffs before opening new ones.
- NO floating panes for code viewing - always use existing nvim pane or splits within it

## Code Guidelines
- Never add "Generated with Claude Code" and "Co-Authored-By: Claude" lines to commit messages. It's unnecesary bloat.
- Remembrance comments are comments designed to give context to code that no longer exists. It explains, for example, why something was removed and they dont make much sense since they can only be understood by those actively involved in the process at that point in time. We never use remembrance comments in our codebase. Comments should be concise and always give context to existing code (preferrably in the near vicinity of the comment).
