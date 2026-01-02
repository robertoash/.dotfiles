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

# npm global packages
if test -d ~/.npm-global/bin
    fish_add_path ~/.npm-global/bin
end