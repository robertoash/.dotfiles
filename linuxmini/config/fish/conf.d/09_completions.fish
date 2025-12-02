## Frecent
# Completions for frecent itself
complete -c frecent -s d -l dirs -d "Show directories only"
complete -c frecent -s f -l files -d "Show files only"
complete -c frecent -s a -l all -d "Show both directories and files"
complete -c frecent -s i -l interactive -d "Use fzf for interactive selection"
complete -c frecent -s h -l help -d "Show help"

## Hass-cli (dynamically generated)
eval (_HASS_CLI_COMPLETE=fish_source hass-cli)

# Enhanced completions for existing commands removed to preserve normal Tab behavior
# Normal Tab behavior (including history suggestion acceptance) is now preserved
# Use triggers (ff<Tab>, dd<Tab>, aa<Tab>) for frecent functionality with any command

# Trigger sequence completions are handled by key bindings
# Triggers: ff<Tab>, dd<Tab>, aa<Tab>


