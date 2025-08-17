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

# Ctrl+Shift+Left/Right arrow keys for space-only word movement
bind \e\[1\;6D custom_backward_word_space   # Ctrl+Shift+Left
bind \e\[1\;6C custom_forward_word_space    # Ctrl+Shift+Right

set -l modes insert default visual replace

for mode in $modes
    if test $mode = default
        bind -M $mode \e\[1\;5H custom_backward_word
        bind -M $mode \e\[1\;5L custom_forward_word
        bind -M $mode \e\[1\;6H custom_backward_word_space
        bind -M $mode \e\[1\;6L custom_forward_word_space
        bind -M $mode \e\[1\;6D custom_backward_word_space
        bind -M $mode \e\[1\;6C custom_forward_word_space

    else if test $mode = insert
        bind -M $mode \e\[1\;5H custom_backward_word
        bind -M $mode \e\[1\;5L custom_forward_word
        bind -M $mode \e\[3\;5~ custom_delete_forward_word
        bind -M $mode \e\[127\;5u custom_delete_backward_word
        bind -M $mode \e\[1\;6H custom_backward_word_space
        bind -M $mode \e\[1\;6L custom_forward_word_space
        bind -M $mode \e\[1\;6D custom_backward_word_space
        bind -M $mode \e\[1\;6C custom_forward_word_space
        bind -M $mode \e\[3\;6~ custom_delete_forward_word_space
        bind -M $mode \e\[127\;6u custom_delete_backward_word_space

    else
        # visual and replace
        bind -M $mode \e\[1\;5H custom_backward_word
        bind -M $mode \e\[1\;5L custom_forward_word
        bind -M $mode \e\[1\;6H custom_backward_word_space
        bind -M $mode \e\[1\;6L custom_forward_word_space
        bind -M $mode \e\[1\;6D custom_backward_word_space
        bind -M $mode \e\[1\;6C custom_forward_word_space
    end
end

# Fuzzy find files and dirs
for mode in insert default visual
    bind -M $mode \cf insert_fre_file
    bind -M $mode \cd insert_zoxide_dir
end

# Shell-GPT integration - Alt+G
for mode in insert default visual
    bind -M $mode \eg sgpt_fish
end

# Allow Alt+hjkl to pass through to Neovim (add after your existing bindings)
for mode in insert default visual replace
    bind -M $mode \eh ''  # Alt+h - clear command, pass through
    bind -M $mode \ej ''  # Alt+j - clear command, pass through  
    bind -M $mode \ek ''  # Alt+k - clear command, pass through
    bind -M $mode \el ''  # Alt+l - clear command, pass through
    bind -M $mode \en ''  # Alt+n - clear command, pass through
end

# Ctrl+Tab for accepting autosuggestion with slashes
bind \e\[27\;5\;9~ accept_next_path_segment

for mode in insert default visual
    bind -M $mode \e\[27\;5\;9~ accept_next_path_segment
end

# Frecent triggers - ff<Tab>, dd<Tab>, aa<Tab>
for mode in insert default visual
    bind -M $mode \t __frecent_unified_widget
end
