function rr
    # If in secure_shell, regenerate entire tmp environment before reloading
    if set -q SECURE_SHELL
        # Clean up old temp dirs (except XDG parent dirs which we'll reuse)
        rm -rf "$XDG_CONFIG_HOME/fish" "$XDG_CONFIG_HOME/yazi"
        rm -rf "$XDG_DATA_HOME/nvim" "$XDG_DATA_HOME/yazi" "$XDG_DATA_HOME/buku"

        # Recopy fish config
        rsync -aL ~/.config/fish/ "$XDG_CONFIG_HOME/fish/"

        # Recopy yazi config
        rsync -aL ~/.config/yazi/ "$XDG_CONFIG_HOME/yazi/"

        # Recopy nvim data in background
        if test -d ~/.local/share/nvim
            cp -r ~/.local/share/nvim "$XDG_DATA_HOME/nvim" &
        end

        # Recreate yazi state symlink
        ln -s ~/.local/state/yazi "$XDG_DATA_HOME/yazi"

        # Recreate buku database symlink
        if test -d ~/.local/share/buku
            ln -s ~/.local/share/buku "$XDG_DATA_HOME/buku"
        end

        # Regenerate secure config with new session ID
        set SESSION_ID "secure_shell_"(date +%s)"_$RANDOM"
        echo "# Secure shell: Ephemeral Fish history and Starship SMART_CWD

set -gx fish_history $SESSION_ID

set -gx SECURE_SHELL 1" > "$XDG_CONFIG_HOME/fish/conf.d/99-secure-shell.fish"

        sync
    end
    clear
    exec fish
end
