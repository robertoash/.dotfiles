# CLAUDE_CODE_OAUTH_TOKEN is injected globally but should only be active in
# SSH sessions (to avoid conflicting with local claude account on each machine)
if not set -q SSH_CONNECTION
    set -e CLAUDE_CODE_OAUTH_TOKEN
end
