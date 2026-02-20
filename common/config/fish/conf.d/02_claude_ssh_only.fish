# CLAUDE_CODE_OAUTH_TOKEN is injected globally but should only be active in
# SSH sessions (to avoid conflicting with local claude account on each machine)
if status is-interactive
    function __unset_claude_token_if_not_ssh --on-event fish_prompt
        if not set -q SSH_CONNECTION; or test $hostname != workmbp
            set -e CLAUDE_CODE_OAUTH_TOKEN
        end
        functions -e __unset_claude_token_if_not_ssh
    end
end
