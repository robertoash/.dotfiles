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

# Enhanced completions for existing commands removed to preserve normal Tab behavior
# Normal Tab behavior (including history suggestion acceptance) is now preserved
# Use triggers (ff<Tab>, dd<Tab>, aa<Tab>) for frecent functionality with any command

# Trigger sequence completions are handled by key bindings
# Triggers: ff<Tab>, dd<Tab>, aa<Tab>


