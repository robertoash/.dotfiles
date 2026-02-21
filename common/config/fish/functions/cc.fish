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
    # the MCP servers for each profile. On launch, those MCPs are swapped
    # into ~/.claude.json (which Claude Code always reads from $HOME).

    set -l known_profiles work personal
    set -l profile work
    set -l claude_args $argv

    if set -q argv[1]; and contains -- $argv[1] $known_profiles
        set profile $argv[1]
        set claude_args $argv[2..]
    end

    # Swap MCPs in ~/.claude.json to match the selected profile
    set -l profile_cache $HOME/.config/claude-profiles/$profile.json
    if test -f $profile_cache
        python3 -c "
import json, sys
with open('$profile_cache') as f:
    profile = json.load(f)
path = '$HOME/.claude.json'
try:
    with open(path) as f:
        cfg = json.load(f)
except FileNotFoundError:
    cfg = {}
cfg['mcpServers'] = profile.get('mcpServers', {})
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
" 2>/dev/null
    end

    if test "$profile" = personal
        env CLAUDE_CONFIG_DIR=$HOME/.claude-personal \
            command claude --allow-dangerously-skip-permissions $claude_args
    else
        command claude --allow-dangerously-skip-permissions $claude_args
    end
end
