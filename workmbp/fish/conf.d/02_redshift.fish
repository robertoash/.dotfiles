# Redshift/PostgreSQL environment variables (loaded from sops secrets)
# Use system secrets to avoid LaunchAgent SSH issues

# Try system secrets first, fallback to home-manager
if test -f "/run/secrets/redshift-url"
    set -gx PGHOST (cat /run/secrets/redshift-url 2>/dev/null | sed 's|^http://||; s|^https://||')
    set -gx PGPORT (cat /run/secrets/redshift-port 2>/dev/null)
    set -gx PGUSER (cat /run/secrets/redshift-user 2>/dev/null)
    set -gx PGPASSWORD (cat /run/secrets/redshift-password 2>/dev/null)
else if test -d "$XDG_RUNTIME_DIR/secrets"
    # Fallback to home-manager secrets
    set -gx PGHOST (cat $XDG_RUNTIME_DIR/secrets/redshift-url 2>/dev/null | sed 's|^http://||; s|^https://||')
    set -gx PGPORT (cat $XDG_RUNTIME_DIR/secrets/redshift-port 2>/dev/null)
    set -gx PGUSER (cat $XDG_RUNTIME_DIR/secrets/redshift-user 2>/dev/null)
    set -gx PGPASSWORD (cat $XDG_RUNTIME_DIR/secrets/redshift-password 2>/dev/null)
end