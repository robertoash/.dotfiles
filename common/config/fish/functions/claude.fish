function claude --description "Claude Code (work profile; use 'cc personal' for personal account)"
    # Ensures ~/.claude.json always points to the work account file before launching.
    # Wrapping the binary here means direct 'claude' invocations work correctly,
    # not just ones via 'cc'. The cc function calls 'command claude' directly for
    # the personal profile to bypass this wrapper.

    set -l account_file $HOME/.dotfiles/common/.claude/work-account.json

    # Migrate existing real ~/.claude.json on first run rather than losing state
    if not test -f $account_file
        if test -f $HOME/.claude.json; and not test -L $HOME/.claude.json
            cp $HOME/.claude.json $account_file
        else
            echo '{}' > $account_file
        end
    end
    ln -sf $account_file $HOME/.claude.json

    set -l profile_cache $HOME/.config/claude-profiles/work.json
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

    command claude $argv
end
