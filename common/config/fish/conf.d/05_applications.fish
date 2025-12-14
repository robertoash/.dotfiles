# ~/.config/fish/conf.d/05_applications.fish
# Application Integrations

# Check if we're not in a secure shell
if not set -q SECURE_SHELL
    # Zoxide (replaces fasd for fish)
    if command -v zoxide >/dev/null 2>&1
        zoxide init fish | source
    end

    # Atuin shell history
    if command -v atuin >/dev/null 2>&1
        atuin init fish --disable-up-arrow | source
    end
end

# Broot
if test -f ~/.config/broot/launcher/fish/br
    source ~/.config/broot/launcher/fish/br
end

# Buku browser integration
if test -f ~/.dotfiles/linuxmini/scripts/shell/buku_browser_wrapper.py
    set -gx BROWSER ~/.dotfiles/linuxmini/scripts/shell/buku_browser_wrapper.py
end