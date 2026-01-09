# ~/.config/fish/conf.d/00_environment.fish
# Environment Variables Configuration for macOS
#
# NOTE: Environment variables are centralized in ~/.dotfiles/system/env_vars.yaml
# That file is distributed by setup.py to ~/.config/environment.d/env_vars.conf
# Since macOS doesn't have systemd, we parse the file directly

# Parse environment.d files (systemd-style format: KEY=value)
for env_file in ~/.config/environment.d/*.conf
    if test -f $env_file
        for line in (cat $env_file)
            # Skip comments and empty lines
            if string match -qr '^#' -- $line; or test -z "$line"
                continue
            end
            set -l parts (string split -m 1 = $line)
            if test (count $parts) -eq 2
                # Skip fish read-only variables and TERM (let terminal set it)
                if contains $parts[1] PWD SHLVL _ TERM
                    continue
                end
                # PATH: append each component via fish_add_path (respects fish_user_paths)
                if test $parts[1] = PATH
                    for p in (string split : $parts[2])
                        if test -d $p
                            fish_add_path --append $p
                        end
                    end
                else
                    set -gx $parts[1] $parts[2]
                end
            end
        end
    end
end

# Load shell-only environment variables from env_vars.yaml
if command -v yq >/dev/null 2>&1; and test -f ~/.dotfiles/system/env_vars.yaml
    for line in (yq -r '.shell_only | to_entries | .[] | "\(.key)=\(.value)"' ~/.dotfiles/system/env_vars.yaml 2>/dev/null)
        set -l parts (string split -m 1 = $line)
        if test (count $parts) -eq 2
            # Expand $HOME in values
            set -l value (string replace -a '$HOME' $HOME -- $parts[2])
            set -gx $parts[1] $value
        end
    end
end

# Set SHELL to fish
set -gx SHELL (which fish)

# Set TERM_PROGRAM for WezTerm (helps applications detect terminal capabilities)
set -gx TERM_PROGRAM WezTerm
