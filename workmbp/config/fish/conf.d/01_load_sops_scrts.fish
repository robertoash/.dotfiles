# Load secrets from sops (workmbp-specific version)
# Uses $XDG_RUNTIME_DIR/secrets/ for secrets

if status is-interactive
    function __load_workmbp_sops_secrets --on-event fish_prompt
        # Only run once
        if not set -q __workmbp_sops_secrets_loaded
            set -l secrets_dir "$XDG_RUNTIME_DIR/secrets"

            if test -d "$secrets_dir"
                # API Keys (available on workmbp via system secrets)
                if test -f "$secrets_dir/openai-api-key"
                    set -gx OPENAI_API_KEY (cat "$secrets_dir/openai-api-key")
                end
                
                if test -f "$secrets_dir/anthropic-api-key"
                    set -gx ANTHROPIC_API_KEY (cat "$secrets_dir/anthropic-api-key")
                end
                
                if test -f "$secrets_dir/linkding-token"
                    set -gx LINKDING_TOKEN (cat "$secrets_dir/linkding-token")
                end
                
                if test -f "$secrets_dir/github-token"
                    set -gx GITHUB_PERSONAL_ACCESS_TOKEN (cat "$secrets_dir/github-token")
                    set -gx GITHUB_TOKEN (cat "$secrets_dir/github-token")  # Also set the expected name
                end
                
                if test -f "$secrets_dir/obsidian-api-key"
                    set -gx OBSIDIAN_API_KEY (cat "$secrets_dir/obsidian-api-key")
                end

                # Email
                if test -f "$secrets_dir/rash-gmail-pass"
                    set -gx RASH_GMAIL_PASS (cat "$secrets_dir/rash-gmail-pass")
                end

                # Claude Code OAuth Token (only for SSH connections to workmbp)
                if test -n "$SSH_CONNECTION"; and test (hostname) = "workmbp"
                    if test -f "$secrets_dir/workmbp-claude-token"
                        set -gx CLAUDE_CODE_OAUTH_TOKEN (cat "$secrets_dir/workmbp-claude-token")
                    end
                end

                # WorkMBP-specific secrets
                if test -f "$secrets_dir/private-key-passphrase"
                    set -gx PRIVATE_KEY_PASSPHRASE (cat "$secrets_dir/private-key-passphrase")
                end
                
                if test -f "$secrets_dir/workmbp-sops-secrets-set"
                    set -gx WORKMBP_SOPS_SECRETS_SET (cat "$secrets_dir/workmbp-sops-secrets-set")
                end

                set -g __workmbp_sops_secrets_loaded 1
            end
        end
    end
end