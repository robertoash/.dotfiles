# ~/.config/fish/conf.d/05_applications.fish
# Application Integrations

# Check if we're in a secure shell
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

# Thefuck
if command -v thefuck >/dev/null 2>&1
    thefuck --alias fuck | source
end

# Hass cli
if command -v hass-cli >/dev/null 2>&1
    _HASS_CLI_COMPLETE=source_fish hass-cli | source
end

# Load Google Cloud SDK
if test -f '/home/rash/builds/google-cloud-sdk/path.fish.inc'
    source '/home/rash/builds/google-cloud-sdk/path.fish.inc'
end

# Load Google Cloud SDK completion
if test -f '/home/rash/builds/google-cloud-sdk/completion.fish.inc'
    source '/home/rash/builds/google-cloud-sdk/completion.fish.inc'
end



# Broot
if test -f ~/.config/broot/launcher/fish/br
    source ~/.config/broot/launcher/fish/br
end