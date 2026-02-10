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
