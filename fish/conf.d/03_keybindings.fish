# ~/.config/fish/conf.d/03_keybindings.fish
# Key Bindings Configuration

# Set vi mode as base (fish default is emacs)
# You can change this to fish_default_key_bindings for emacs mode
fish_vi_key_bindings

# Navigation - emacs style bindings
bind \ca beginning-of-line
bind \ce end-of-line
bind \e\[3~ delete-char

# Home and End keys
bind \eOH beginning-of-line
bind \eOF end-of-line

# Alt + LeftArrow -> backward-word
bind \e\[1\;3D backward-word
# Alt + RightArrow -> forward-word
bind \e\[1\;3C forward-word

# Delete until the previous slash or word boundary
bind \cH backward-kill-path-component

# History substring search (if fish_history_substring_search is installed)
# bind \e\[A history-substring-search-up
# bind \e\[B history-substring-search-down

# Note: Fish doesn't have direct equivalents for some zsh-specific bindings like:
# - fasd-complete functions (fasd isn't commonly used with fish)
# - sgpt bindings (would need custom fish functions)
# - fzf path completion (fish has built-in completion system)

# FZF bindings (if fzf is installed)
# These are typically handled by fzf's fish integration