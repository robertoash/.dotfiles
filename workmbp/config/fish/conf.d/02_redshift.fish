# Redshift/PostgreSQL environment variables (loaded from sops secrets)

if test -d "$XDG_RUNTIME_DIR/secrets"
    set -gx PGHOST (cat $XDG_RUNTIME_DIR/secrets/redshift-url 2>/dev/null | sed 's|^http://||; s|^https://||')
    set -gx PGPORT (cat $XDG_RUNTIME_DIR/secrets/redshift-port 2>/dev/null)
    set -gx PGUSER (cat $XDG_RUNTIME_DIR/secrets/redshift-user 2>/dev/null)
    set -gx PGPASSWORD (cat $XDG_RUNTIME_DIR/secrets/redshift-password 2>/dev/null)
end