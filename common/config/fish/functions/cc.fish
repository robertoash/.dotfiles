function cc --description "Launch Claude Code with optional account profile"
    # Usage:
    #   cc                         # work profile (default)
    #   cc personal                # personal profile
    #   cc work                    # work profile (explicit)
    #   cc --continue              # work profile, pass --continue to claude
    #   cc personal --resume ...   # personal profile, pass args to claude
    #
    # Profiles are defined in dotfiles tools.yaml / settings.{profile}.json.
    # setup.py pre-generates ~/.config/claude-profiles/{profile}.json with
    # the MCP servers for each profile.
    #
    # Account switching: ~/.claude.json is always read from $HOME regardless of
    # CLAUDE_CONFIG_DIR. We manage it as a symlink into per-profile account files
    # in dotfiles so each profile gets its own oauthAccount/userID and full state.
    # The account files are gitignored (contain account UUIDs + session state).

    set -l known_profiles work personal
    set -l profile work
    set -l claude_args $argv

    if set -q argv[1]; and contains -- $argv[1] $known_profiles
        set profile $argv[1]
        set claude_args $argv[2..]
    end

    # Point ~/.claude.json at the profile's account file (symlink).
    # On first run for work, migrate the existing real file rather than losing state.
    set -l account_file $HOME/.dotfiles/common/.claude/$profile-account.json
    if not test -f $account_file
        if test "$profile" = work; and test -f $HOME/.claude.json; and not test -L $HOME/.claude.json
            cp $HOME/.claude.json $account_file
        else
            echo '{}' > $account_file
        end
    end
    ln -sf $account_file $HOME/.claude.json

    # Swap MCPs in ~/.claude.json (writes through the symlink into the account file)
    set -l profile_cache $HOME/.config/claude-profiles/$profile.json
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

    if test "$profile" = personal
        set -x CLAUDE_CONFIG_DIR $HOME/.claude-personal
        command claude --allow-dangerously-skip-permissions $claude_args
        set -e CLAUDE_CONFIG_DIR
        # Restore work as default so bare 'claude' invocations use the work account
        ln -sf $HOME/.dotfiles/common/.claude/work-account.json $HOME/.claude.json
    else
        command claude --allow-dangerously-skip-permissions $claude_args
    end
end
