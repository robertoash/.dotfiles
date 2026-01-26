# Load secrets from sops-nix
# Secrets are decrypted and stored in $XDG_RUNTIME_DIR/secrets/
# This file loads them as environment variables for interactive shells

if status is-interactive
    function __load_sops_secrets --on-event fish_prompt
        # Only run once
        if not set -q __sops_secrets_loaded
            set -l secrets_dir "$XDG_RUNTIME_DIR/secrets"

            if test -d "$secrets_dir"
                # HASS (Home Assistant)
                test -f "$secrets_dir/hass-server" && set -gx HASS_SERVER (cat "$secrets_dir/hass-server")
                test -f "$secrets_dir/hass-token" && set -gx HASS_TOKEN (cat "$secrets_dir/hass-token")

                # Tibber
                test -f "$secrets_dir/tibber-token" && set -gx TIBBER_TOKEN (cat "$secrets_dir/tibber-token")

                # Spotify
                test -f "$secrets_dir/sp-user" && set -gx SP_USER (cat "$secrets_dir/sp-user")
                test -f "$secrets_dir/sp-pass" && set -gx SP_PASS (cat "$secrets_dir/sp-pass")

                # CJAR (encrypted filesystem)
                test -f "$secrets_dir/cjar-oven" && set -gx CJAR_OVEN (cat "$secrets_dir/cjar-oven")
                test -f "$secrets_dir/cjar-laxative" && set -gx CJAR_LAXATIVE (cat "$secrets_dir/cjar-laxative")
                test -f "$secrets_dir/dough-storage" && set -gx DOUGH_STORAGE (cat "$secrets_dir/dough-storage")
                test -f "$secrets_dir/dinner-table" && set -gx DINNER_TABLE (cat "$secrets_dir/dinner-table")

                # API Keys
                test -f "$secrets_dir/openai-api-key" && set -gx OPENAI_API_KEY (cat "$secrets_dir/openai-api-key")
                test -f "$secrets_dir/anthropic-api-key" && set -gx ANTHROPIC_API_KEY (cat "$secrets_dir/anthropic-api-key")
                test -f "$secrets_dir/linkding-token" && set -gx LINKDING_TOKEN (cat "$secrets_dir/linkding-token")
                test -f "$secrets_dir/github-token" && set -gx GITHUB_PERSONAL_ACCESS_TOKEN (cat "$secrets_dir/github-token")
                test -f "$secrets_dir/gitlab-token" && set -gx GITLAB_TOKEN (cat "$secrets_dir/gitlab-token")
                test -f "$secrets_dir/obsidian-api-key" && set -gx OBSIDIAN_API_KEY (cat "$secrets_dir/obsidian-api-key")

                # Email
                test -f "$secrets_dir/rash-gmail-pass" && set -gx RASH_GMAIL_PASS (cat "$secrets_dir/rash-gmail-pass")

                # Claude Code OAuth Token (only for SSH connections to workmbp)
                if test -n "$SSH_CONNECTION"; and test (hostname) = "workmbp"
                    test -f "$secrets_dir/workmbp-claude-token" && set -gx CLAUDE_CODE_OAUTH_TOKEN (cat "$secrets_dir/workmbp-claude-token")
                end

                set -g __sops_secrets_loaded 1
            end
        end
    end
end
