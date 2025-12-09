# Set up XDG_RUNTIME_DIR and decrypt sops secrets on shell initialization
# This works on both Linux and macOS

# Set XDG_RUNTIME_DIR if not already set (needed on macOS, systemd sets this on Linux)
if not set -q XDG_RUNTIME_DIR
    # Check if we're on macOS
    if test (uname) = "Darwin"
        set -gx XDG_RUNTIME_DIR "$HOME/.local/state/runtime"
    else
        # On Linux, use systemd's runtime dir
        set -gx XDG_RUNTIME_DIR "/run/user/"(id -u)
    end
end

# Function to decrypt secrets (runs once per session)
function __decrypt_sops_secrets --on-event fish_prompt
    # Only run once per session
    if not set -q __sops_secrets_decrypted
        # Check if we have the common decrypt script
        set -l decrypt_script "$HOME/.dotfiles/common/scripts/decrypt-secrets.sh"

        if test -x "$decrypt_script"
            # Run decrypt script silently
            $decrypt_script >/dev/null 2>&1
            if test $status -eq 0
                set -g __sops_secrets_decrypted 1
            end
        end
    end
end
