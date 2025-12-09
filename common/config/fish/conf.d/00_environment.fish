# ~/.config/fish/conf.d/00_environment.fish
# Environment Variables Configuration
#
# NOTE: Environment variables are centralized in ~/.config/environment.d/env_vars.conf
# This uses systemd user environment (works across all shells and applications)
#
# Import systemd user environment into fish
# This is needed because fish doesn't automatically inherit from environment.d
# Import all environment variables from systemd user environment
for line in (systemctl --user show-environment 2>/dev/null)
    set -l parts (string split -m 1 = $line)
    if test (count $parts) -eq 2
        # Skip fish read-only variables, TERM (let terminal set it), and SHELL (already correct)
        if not contains $parts[1] PWD SHLVL _ TERM SHELL
            set -gx $parts[1] $parts[2]
        end
    end
end

# Secrets are loaded via sops-nix (see 01_load_sops_scrts.fish)
