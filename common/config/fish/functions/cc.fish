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
    #
    # Account switching: ~/.claude.json also stores oauthAccount/userID which
    # Claude Code uses to identify the active account. CLAUDE_CONFIG_DIR only
    # controls the credentials directory, not ~/.claude.json. So we save/restore
    # account fields around personal launches to keep profiles fully isolated.

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
import json
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
        # Before switching: save current (work) account fields and load personal ones.
        # This is self-bootstrapping: first run saves work data and prompts Claude
        # login for personal; subsequent runs swap the saved personal data in.
        python3 -c "
import json, os
home = '$HOME'
claude_json = home + '/.claude.json'
work_acct_file = home + '/.config/claude-profiles/work-account.json'
personal_acct_file = home + '/.config/claude-profiles/personal-account.json'
acct_keys = ['oauthAccount', 'userID']

try:
    with open(claude_json) as f:
        cfg = json.load(f)
except FileNotFoundError:
    cfg = {}

# Save current work account data
work_acct = {k: cfg[k] for k in acct_keys if k in cfg}
with open(work_acct_file, 'w') as f:
    json.dump(work_acct, f, indent=2)

# Load personal account data if it exists from a previous session
if os.path.exists(personal_acct_file):
    with open(personal_acct_file) as f:
        personal_acct = json.load(f)
    cfg.update(personal_acct)
    with open(claude_json, 'w') as f:
        json.dump(cfg, f, indent=2)
" 2>/dev/null

        set -x CLAUDE_CONFIG_DIR $HOME/.claude-personal
        command claude --allow-dangerously-skip-permissions $claude_args
        set -e CLAUDE_CONFIG_DIR

        # After exit: save personal account data and restore work account.
        python3 -c "
import json, os
home = '$HOME'
claude_json = home + '/.claude.json'
work_acct_file = home + '/.config/claude-profiles/work-account.json'
personal_acct_file = home + '/.config/claude-profiles/personal-account.json'
acct_keys = ['oauthAccount', 'userID']

try:
    with open(claude_json) as f:
        cfg = json.load(f)
except FileNotFoundError:
    cfg = {}

# Save personal account data (may have been refreshed during the session)
personal_acct = {k: cfg[k] for k in acct_keys if k in cfg}
with open(personal_acct_file, 'w') as f:
    json.dump(personal_acct, f, indent=2)

# Restore work account data
if os.path.exists(work_acct_file):
    with open(work_acct_file) as f:
        work_acct = json.load(f)
    cfg.update(work_acct)
    with open(claude_json, 'w') as f:
        json.dump(cfg, f, indent=2)
" 2>/dev/null
    else
        command claude --allow-dangerously-skip-permissions $claude_args
    end
end
