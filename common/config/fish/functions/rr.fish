function rr
    # If in secure_shell, recopy config from real location before reloading
    if set -q SECURE_SHELL
        rsync -aL ~/.config/fish/ "$XDG_CONFIG_HOME/fish/"
        sync
    end
    clear
    exec fish
end
