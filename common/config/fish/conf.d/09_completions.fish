# Auto-load completion directories from ~/.config/fish/completions/*.d/
# This allows symlinking external completion directories (e.g., brew, cargo)
for comp_dir in $__fish_config_dir/completions/*.d
    if test -d "$comp_dir"
        set -gx fish_complete_path "$comp_dir" $fish_complete_path
    end
end

## Frecent
# Completions for frecent itself
complete -c frecent -s d -l dirs -d "Show directories only"
complete -c frecent -s f -l files -d "Show files only"
complete -c frecent -s a -l all -d "Show both directories and files"
complete -c frecent -s i -l interactive -d "Use fzf for interactive selection"
complete -c frecent -s h -l help -d "Show help"

## Hass-cli (dynamically generated)
if test -f /etc/hostname; and test (cat /etc/hostname 2>/dev/null) = "linuxmini"; and command -v hass-cli >/dev/null 2>&1
    # Try to generate completions, suppress errors if hass-cli has broken shebang
    _HASS_CLI_COMPLETE=fish_source hass-cli 2>/dev/null | source 2>/dev/null
end

# Tab completion: __smart_tab_complete handles context-aware completion with smart ordering and reasoning labels
# Trigger words: ff/dd/aa (frecent), fff/fdd/faa (fd) handled within __smart_tab_complete
# Preview: Ctrl+P toggles preview in fzf (hidden by default)


