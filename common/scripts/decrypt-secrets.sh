#!/usr/bin/env bash
# Decrypt sops secrets and place them in XDG_RUNTIME_DIR/secrets/
# Also injects them into systemd user environment (Linux) or launchctl (macOS)
# Works on both Linux and macOS, for both common and host-specific secrets
#
# Secret filenames use kebab-case and are auto-transformed to UPPER_SNAKE_CASE
# env vars. Add a new key to sops and it becomes available everywhere automatically.

set -euo pipefail

# Detect OS and set runtime directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    RUNTIME_DIR="${XDG_RUNTIME_DIR:-$HOME/.local/state/runtime}"
    IS_MACOS=1
else
    RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$UID}"
    IS_MACOS=0
fi

SECRETS_DIR="$RUNTIME_DIR/secrets"
DOTFILES="$HOME/.dotfiles"

# Get hostname - use /etc/hostname on Linux, hostname command on macOS
if [[ "$IS_MACOS" -eq 1 ]]; then
    HOSTNAME=$(hostname -s)
else
    HOSTNAME=$(cat /etc/hostname)
fi

# Create secrets directory with secure permissions, clearing stale files first
mkdir -p "$SECRETS_DIR"
chmod 700 "$RUNTIME_DIR"
chmod 700 "$SECRETS_DIR"
find "$SECRETS_DIR" -maxdepth 1 -type f ! -name '.*' -delete

# Set SOPS_AGE_KEY_FILE if not set
if [ -z "${SOPS_AGE_KEY_FILE:-}" ]; then
    # Try machine-specific keys first, then common location
    if [ -f "$DOTFILES/$HOSTNAME/sops/age/keys.txt" ]; then
        export SOPS_AGE_KEY_FILE="$DOTFILES/$HOSTNAME/sops/age/keys.txt"
    elif [ -f "$HOME/.config/sops/age/keys.txt" ]; then
        export SOPS_AGE_KEY_FILE="$HOME/.config/sops/age/keys.txt"
    else
        echo "Error: No age keys found" >&2
        exit 1
    fi
fi

# Transform kebab-case filename to UPPER_SNAKE_CASE env var name
to_env_name() {
    echo "$1" | tr '[:lower:]' '[:upper:]' | tr '-' '_'
}

# Function to decrypt and extract all secrets from a YAML file
decrypt_file() {
    local sops_file="$1"
    local label="$2"

    if [ ! -f "$sops_file" ]; then
        return
    fi

    echo "Decrypting $label secrets from $sops_file"

    # Decrypt the file
    local decrypted
    decrypted=$(sops -d "$sops_file" 2>/dev/null) || {
        echo "Error: Failed to decrypt $sops_file" >&2
        return 1
    }

    # Extract all top-level keys and their values using yq
    echo "$decrypted" | yq -r 'to_entries | .[] | "\(.key)\t\(.value)"' | while IFS=$'\t' read -r key value; do
        # Skip sops metadata and empty values
        if [[ "$key" == "sops" ]] || [[ -z "$value" ]]; then
            continue
        fi

        # Write secret to file (using original kebab-case name)
        local output_file="$SECRETS_DIR/$key"
        echo "$value" > "$output_file"
        chmod 600 "$output_file"
    done
}

# Decrypt common secrets first (available to all machines)
decrypt_file "$DOTFILES/common/secrets/common.yaml" "common"

# Decrypt OS-specific secrets (Linux or macOS)
if [[ "$IS_MACOS" -eq 0 ]]; then
    # Linux-specific secrets
    decrypt_file "$DOTFILES/linuxcommon/secrets/linuxcommon.yaml" "linuxcommon"
fi

# Decrypt machine-specific secrets (can override common secrets)
# Try both .yaml and .yml extensions
decrypt_file "$DOTFILES/$HOSTNAME/secrets/$HOSTNAME.yaml" "machine-specific"
decrypt_file "$DOTFILES/$HOSTNAME/secrets/$HOSTNAME.yml" "machine-specific"

# Create a marker file to indicate secrets are loaded
echo "1" > "$SECRETS_DIR/.secrets-loaded"
chmod 600 "$SECRETS_DIR/.secrets-loaded"

# Inject all secrets into system environment
# This makes them available to systemd services and GUI apps
echo "Injecting secrets into system environment..."
for secret_file in "$SECRETS_DIR"/*; do
    [ -f "$secret_file" ] || continue
    basename=$(basename "$secret_file")

    # Skip marker/hidden files
    case "$basename" in
        .*) continue ;;
    esac

    env_name=$(to_env_name "$basename")
    value=$(cat "$secret_file")

    if [[ "$IS_MACOS" -eq 1 ]]; then
        launchctl setenv "$env_name" "$value"
    else
        systemctl --user set-environment "$env_name=$value" 2>/dev/null || true
    fi
done

echo "Secrets decrypted to $SECRETS_DIR and injected into environment"
