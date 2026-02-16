# Auto-load all sops secrets from $XDG_RUNTIME_DIR/secrets/ as env vars
# Secret filenames (kebab-case) are transformed to UPPER_SNAKE_CASE automatically.
# Adding a new key to sops makes it available here with no further config needed.

if status is-interactive
    function __load_sops_secrets --on-event fish_prompt
        # Only run once per session
        if not set -q __sops_secrets_loaded
            set -l secrets_dir "$XDG_RUNTIME_DIR/secrets"

            if test -d "$secrets_dir"
                for secret_file in $secrets_dir/*
                    test -f "$secret_file"; or continue
                    set -l name (path basename $secret_file)

                    # Skip hidden/marker files
                    string match -q '.*' $name; and continue

                    # Transform kebab-case to UPPER_SNAKE_CASE
                    set -l var_name (string upper (string replace -a '-' '_' $name))
                    set -gx $var_name (cat $secret_file)
                end
                set -g __sops_secrets_loaded 1
            end
        end
    end
end
