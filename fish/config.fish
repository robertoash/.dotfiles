# ~/.config/fish/config.fish

# #################################
# # Fish Configuration
# #################################

# Disable greeting
set -g fish_greeting


# #################################
# # Mise Configuration
# #################################

~/.local/bin/mise activate fish | source

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
