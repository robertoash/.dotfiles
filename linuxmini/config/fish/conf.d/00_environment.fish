# ~/.config/fish/conf.d/00_environment.fish
# Environment Variables Configuration
#
# NOTE: Environment variables are centralized in ~/.dotfiles/system/env_vars.yaml
# That file is distributed by setup.py to ~/.config/environment.d/env_vars.conf
# This uses systemd user environment (works across all shells and applications)
#
# Import systemd user environment into fish
# This is needed because fish doesn't automatically inherit from environment.d
# Import all environment variables from systemd user environment
for line in (systemctl --user show-environment 2>/dev/null)
    set -l parts (string split -m 1 = $line)
    if test (count $parts) -eq 2
        # Skip fish read-only variables and TERM (let terminal set it)
        if not contains $parts[1] PWD SHLVL _ TERM
            set -gx $parts[1] $parts[2]
        end
    end
end

# Load shell-only environment variables from env_vars.yaml
if command -v yq >/dev/null 2>&1; and test -f ~/.dotfiles/system/env_vars.yaml
    for line in (yq -r '.shell_only | to_entries | .[] | "\(.key)=\(.value)"' ~/.dotfiles/system/env_vars.yaml 2>/dev/null)
        set -l parts (string split -m 1 = $line)
        if test (count $parts) -eq 2
            # Expand $HOME in values
            set -l value (string replace -a '$HOME' $HOME -- $parts[2])
            set -gx $parts[1] $value
        end
    end
end

# Set SHELL to fish (systemd has /bin/bash)
set -gx SHELL /usr/bin/fish

# Unset NPM_CONFIG_PREFIX inherited from /usr/bin/claude wrapper
# Claude Code sets this to /nonexistent to prevent self-detection,
# but we want npm to use the prefix from ~/.npmrc instead
set -e NPM_CONFIG_PREFIX

# Load linuxmini-specific sops secrets
if status is-interactive
    function __load_linuxmini_sops_secrets --on-event fish_prompt
        # Only run once
        if not set -q __linuxmini_sops_secrets_loaded
            set -l secrets_dir "$XDG_RUNTIME_DIR/secrets"

            if test -d "$secrets_dir"
                # Xtream IPTV (parse nested YAML structure)
                if test -f "$secrets_dir/xtream"
                    set -gx XTREAM_PROXY_SERVER (yq -r '.upstream.server' "$secrets_dir/xtream" 2>/dev/null)
                    set -gx XTREAM_PROXY_USERNAME (yq -r '.upstream.username' "$secrets_dir/xtream" 2>/dev/null)
                    set -gx XTREAM_PROXY_PASSWORD (yq -r '.upstream.password' "$secrets_dir/xtream" 2>/dev/null)
                end

                set -g __linuxmini_sops_secrets_loaded 1
            end
        end
    end
end
