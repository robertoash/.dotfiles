# Snowflake environment variables (loaded from sops secrets)
# These are decrypted by sops-nix and placed in $XDG_RUNTIME_DIR/secrets/

if test -d "$XDG_RUNTIME_DIR/secrets"
    # Read secrets from sops-decrypted files
    # Snowflake CLI uses PRIVATE_KEY_PASSPHRASE (not SNOWSQL_PRIVATE_KEY_PASSPHRASE)
    set -gx PRIVATE_KEY_PASSPHRASE (cat $XDG_RUNTIME_DIR/secrets/private-key-passphrase 2>/dev/null)
end
