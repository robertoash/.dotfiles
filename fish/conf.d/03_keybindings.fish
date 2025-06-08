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

# Custom word movement with Ctrl+h (backward) and Ctrl+l (forward)
# These use custom escape sequences from wezterm and treat slashes as word boundaries
bind \e\[1\;5H custom_backward_word
bind \e\[1\;5L custom_forward_word

# Word deletion keybinds (slash-aware)
bind \e\[3\;5~ custom_delete_forward_word   # Ctrl+Delete
bind \e\[127\;5u custom_delete_backward_word # Ctrl+Backspace

# Space-only word movement with Ctrl+Shift+h and Ctrl+Shift+l
# These ignore slashes and only treat spaces as delimiters
bind \e\[1\;6H custom_backward_word_space
bind \e\[1\;6L custom_forward_word_space

# Space-only word deletion keybinds
bind \e\[3\;6~ custom_delete_forward_word_space   # Ctrl+Shift+Delete
bind \e\[127\;6u custom_delete_backward_word_space # Ctrl+Shift+Backspace

# Additional compatibility bindings for different terminal emulators
# These handle common escape sequences that different terminals might send
bind \e\[1\;5D custom_backward_word         # Some terminals: Ctrl+Left
bind \e\[1\;5C custom_forward_word          # Some terminals: Ctrl+Right
bind \e\[5D custom_backward_word            # Alternative Ctrl+Left
bind \e\[5C custom_forward_word             # Alternative Ctrl+Right

# Alternative binding for Ctrl+Delete in some terminals
bind \e\[M custom_delete_forward_word       # Alternative Ctrl+Delete

# Ensure our custom functions work in different vim modes
bind -M insert \e\[1\;5H custom_backward_word
bind -M insert \e\[1\;5L custom_forward_word
bind -M insert \e\[3\;5~ custom_delete_forward_word
bind -M insert \e\[127\;5u custom_delete_backward_word

# Default mode bindings
bind -M default \e\[1\;5H custom_backward_word
bind -M default \e\[1\;5L custom_forward_word

# Add bindings for all vi modes
bind -M visual \e\[1\;5H custom_backward_word
bind -M visual \e\[1\;5L custom_forward_word
bind -M replace \e\[1\;5H custom_backward_word
bind -M replace \e\[1\;5L custom_forward_word

# Space-only bindings for all modes
bind -M insert \e\[1\;6H custom_backward_word_space
bind -M insert \e\[1\;6L custom_forward_word_space
bind -M insert \e\[3\;6~ custom_delete_forward_word_space
bind -M insert \e\[127\;6u custom_delete_backward_word_space

bind -M default \e\[1\;6H custom_backward_word_space
bind -M default \e\[1\;6L custom_forward_word_space
bind -M visual \e\[1\;6H custom_backward_word_space
bind -M visual \e\[1\;6L custom_forward_word_space
bind -M replace \e\[1\;6H custom_backward_word_space
bind -M replace \e\[1\;6L custom_forward_word_space

# History substring search (if fish_history_substring_search is installed)
# bind \e\[A history-substring-search-up
# bind \e\[B history-substring-search-down

# Note: Fish doesn't have direct equivalents for some zsh-specific bindings like:
# - fasd-complete functions (fasd isn't commonly used with fish)
# - sgpt bindings (would need custom fish functions)
# - fzf path completion (fish has built-in completion system)

# FZF bindings (if fzf is installed)
# These are typically handled by fzf's fish integration