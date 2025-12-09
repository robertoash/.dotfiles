#!/usr/bin/env bash
set -e

SECRETS_DIR="/run/user/$UID/secrets"
COMMON_SOPS_FILE="$HOME/.dotfiles/common/secrets/common.yaml"
MACHINE_SOPS_FILE="$HOME/.dotfiles/linuxmini/secrets/linuxmini.yaml"
AGE_KEY="$HOME/.config/sops/age/keys.txt"

# Check if age key exists
if [ ! -f "$AGE_KEY" ]; then
    echo "Error: Age key not found at $AGE_KEY" >&2
    exit 1
fi

# Check if at least one sops file exists
if [ ! -f "$COMMON_SOPS_FILE" ] && [ ! -f "$MACHINE_SOPS_FILE" ]; then
    echo "Error: No secrets files found" >&2
    echo "  Common: $COMMON_SOPS_FILE" >&2
    echo "  Machine: $MACHINE_SOPS_FILE" >&2
    exit 1
fi

# Create secrets directory
mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR"

# Decrypt and extract secrets to individual files
# The secrets are in YAML format with key: value pairs
export SOPS_AGE_KEY_FILE="$AGE_KEY"

# Function to decrypt and extract secrets from a file
decrypt_file() {
    local sops_file="$1"
    local label="$2"

    if [ ! -f "$sops_file" ]; then
        echo "Skipping $label: file not found at $sops_file"
        return
    fi

    echo "Decrypting $label secrets from $sops_file"
    sops -d "$sops_file" | python3 -c "
import sys
import yaml
import os

data = yaml.safe_load(sys.stdin)
secrets_dir = '$SECRETS_DIR'

for key, value in data.items():
    if value is not None:
        filepath = os.path.join(secrets_dir, key)
        with open(filepath, 'w') as f:
            f.write(str(value))
        os.chmod(filepath, 0o600)
        print(f'Decrypted: {key}')
"
}

# Decrypt common secrets first
decrypt_file "$COMMON_SOPS_FILE" "common"

# Decrypt machine-specific secrets (can override common secrets)
decrypt_file "$MACHINE_SOPS_FILE" "machine-specific"

echo "All secrets decrypted to $SECRETS_DIR"
