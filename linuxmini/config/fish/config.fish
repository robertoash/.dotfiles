# ~/.config/fish/config.fish

# Disable greeting
set -g fish_greeting

# Load all custom configurations
for file in ~/.config/fish/conf.d/*.fish
    source $file
end