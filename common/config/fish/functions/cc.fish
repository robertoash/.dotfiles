function cc --description "Launch Claude Code with optional account profile"
    # Usage:
    #   cc                         # work profile (default)
    #   cc personal                # personal profile
    #   cc work                    # work profile (explicit)
    #   cc --continue              # work profile, pass --continue to claude
    #   cc personal --resume ...   # personal profile, pass args to claude
    #
    # Profiles are defined in dotfiles tools.yaml / settings.{profile}.json.
    # setup.py pre-generates ~/.config/claude-profiles/{profile}.json with MCP
    # servers for each profile. CLAUDE_CONFIG_DIR moves the entire config root,
    # so .claude.json lives at $CLAUDE_CONFIG_DIR/.claude.json (or ~/.claude.json
    # for the default work profile where config root is $HOME).

    set -l known_profiles work personal
    set -l profile work
    set -l claude_args $argv

    if set -q argv[1]; and contains -- $argv[1] $known_profiles
        set profile $argv[1]
        set claude_args $argv[2..]
    end

    # Swap MCPs into the .claude.json that Claude will actually read.
    # Default config root is $HOME; CLAUDE_CONFIG_DIR overrides it.
    if test "$profile" = personal
        set -l claude_json $HOME/.claude-personal/.claude.json
    else
        set -l claude_json $HOME/.claude.json
    end
    set -l profile_cache $HOME/.config/claude-profiles/$profile.json
    if test -f $profile_cache
        python3 -c "
import json
with open('$profile_cache') as f:
    profile = json.load(f)
path = '$claude_json'
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
    else
        command claude --allow-dangerously-skip-permissions $claude_args
    end
end
