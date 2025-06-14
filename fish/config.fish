# ~/.config/fish/config.fish

# #################################
# # Fish Configuration
# #################################

# Disable greeting
set -g fish_greeting

# #################################
# # ASDF Configuration
# #################################

# ASDF configuration code
if test -z $ASDF_DATA_DIR
    set _asdf_shims "$HOME/.asdf/shims"
else
    set _asdf_shims "$ASDF_DATA_DIR/shims"
end

# Do not use fish_add_path (added in Fish 3.2) because it
# potentially changes the order of items in PATH
if not contains $_asdf_shims $PATH
    set -gx --prepend PATH $_asdf_shims
end
set --erase _asdf_shims

# #################################
# # History Configuration
# #################################

# History settings
set -g fish_history_max 10000
set -g fish_history_save_on_exit 1

# #################################
# # Cursor Configuration
# #################################

# Cursor settings
set -g fish_cursor_default block
set -g fish_cursor_insert line
set -g fish_cursor_replace_one underscore
set -g fish_cursor_visual block

# #################################
# # Frequently Used Functions
# #################################

for file in ~/.config/fish/conf.d/startup_functions/*.fish
    source $file
end

# #################################
# # Secrets
# #################################

for file in ~/.config/fish/conf.d/secrets/*.fish
    source $file
end

# Note: Fish automatically loads:
# - All files in conf.d/ directory (in alphabetical order)
# - All .fish files in functions/ directory as functions
# - Custom completions from completions/ directory