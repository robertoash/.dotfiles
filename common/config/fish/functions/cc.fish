function cc --description "Launch Claude Code with optional account profile"
    # Usage:
    #   cc                         # work profile (default)
    #   cc personal                # personal profile
    #   cc work                    # work profile (explicit)
    #   cc --continue              # work profile, pass --continue to claude
    #   cc personal --resume ...   # personal profile, pass args to claude
    #
    # The 'claude' fish function wraps the binary and always sets up the work
    # profile. cc delegates to it for work, and handles personal directly via
    # 'command claude' to bypass the wrapper.

    set -l known_profiles work personal
    set -l profile work
    set -l claude_args $argv

    if set -q argv[1]; and contains -- $argv[1] $known_profiles
        set profile $argv[1]
        set claude_args $argv[2..]
    end

    if test "$profile" = personal
        set -l account_file $HOME/.dotfiles/common/.claude/personal-account.json
        if not test -f $account_file
            echo '{}' > $account_file
        end
        ln -sf $account_file $HOME/.claude.json

        set -l profile_cache $HOME/.config/claude-profiles/personal.json
        if test -f $profile_cache
            python3 -c "
import json
with open('$profile_cache') as f:
    profile = json.load(f)
path = '$HOME/.claude.json'
try:
    with open(path) as f:
        cfg = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cfg = {}
cfg['mcpServers'] = profile.get('mcpServers', {})
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
" 2>/dev/null
        end

        set -x CLAUDE_CONFIG_DIR $HOME/.claude-personal
        command claude --allow-dangerously-skip-permissions $claude_args
        set -e CLAUDE_CONFIG_DIR
        # Restore work as default; next bare 'claude' call will also do this,
        # but restore eagerly so other terminal sessions aren't affected
        if not test -f $HOME/.dotfiles/common/.claude/work-account.json
            echo '{}' > $HOME/.dotfiles/common/.claude/work-account.json
        end
        ln -sf $HOME/.dotfiles/common/.claude/work-account.json $HOME/.claude.json
    else
        claude --allow-dangerously-skip-permissions $claude_args
    end
end
