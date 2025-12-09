# ~/.config/fish/conf.d/00_homebrew.fish
# Homebrew Configuration (macOS only)

# Add Homebrew to PATH on macOS
if test (uname) = Darwin
    # Check for Apple Silicon Homebrew
    if test -d /opt/homebrew
        fish_add_path --prepend /opt/homebrew/bin
        fish_add_path --prepend /opt/homebrew/sbin

        # Set Homebrew environment variables
        set -gx HOMEBREW_PREFIX /opt/homebrew
        set -gx HOMEBREW_CELLAR /opt/homebrew/Cellar
        set -gx HOMEBREW_REPOSITORY /opt/homebrew

        # Add to MANPATH
        if test -d /opt/homebrew/share/man
            set -gx MANPATH /opt/homebrew/share/man $MANPATH
        end

        # Add to INFOPATH
        if test -d /opt/homebrew/share/info
            set -gx INFOPATH /opt/homebrew/share/info $INFOPATH
        end
    # Check for Intel Homebrew
    else if test -d /usr/local/Homebrew
        fish_add_path --prepend /usr/local/bin
        fish_add_path --prepend /usr/local/sbin

        # Set Homebrew environment variables
        set -gx HOMEBREW_PREFIX /usr/local
        set -gx HOMEBREW_CELLAR /usr/local/Cellar
        set -gx HOMEBREW_REPOSITORY /usr/local/Homebrew

        # Add to MANPATH
        if test -d /usr/local/share/man
            set -gx MANPATH /usr/local/share/man $MANPATH
        end

        # Add to INFOPATH
        if test -d /usr/local/share/info
            set -gx INFOPATH /usr/local/share/info $INFOPATH
        end
    end
end
