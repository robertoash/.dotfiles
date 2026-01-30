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

                # Jellyfin (parse nested YAML structure)
                if test -f "$secrets_dir/jellyfin"
                    set -gx JELLYFIN_URL (yq -r '.server' "$secrets_dir/jellyfin" 2>/dev/null)
                    set -gx JELLYFIN_API_KEY (yq -r '.api_key' "$secrets_dir/jellyfin" 2>/dev/null)
                end

                set -g __linuxmini_sops_secrets_loaded 1
            end
        end
    end
end
