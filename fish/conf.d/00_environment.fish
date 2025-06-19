# ~/.config/fish/conf.d/00_environment.fish
# Environment Variables Configuration

# Defaults
set -gx EDITOR "nvim"
set -gx VISUAL "nvim"
set -gx SUDO_EDITOR "nvim"
set -gx GIT_EDITOR "nvim"
set -gx IDE "cursor"
set -gx TERMINAL "wezterm"
set -gx COLORTERM "truecolor"
set -gx TERM "xterm-256color"
set -gx BROWSER "/home/rash/.local/bin/qute_profile rash %s"
set -gx BROWSER_CLEAN "/home/rash/.local/bin/qute_profile rash"
set -gx NOTE_EDITOR "obsidian"
set -gx QT_QPA_PLATFORMTHEME gtk2
set -gx XDG_CURRENT_DESKTOP Hyprland

# Theme
set -gx GTK_THEME "tokyonight_deep"

set -gx CURRENT_PROJECT_DIR "/home/rash/dev/apps"
set -gx DOTFILES_DIR "/home/rash/.config"

# File locations
set -gx XDG_CONFIG_HOME "$HOME/.config"
set -gx ZELLIJ_CONFIG_FILE ~/.config/zellij/config.kdl
set -gx GTK2_RC_FILES "$HOME/.config/gtk-2.0/gtkrc-2.0"
set -gx YARN_RC_FILENAME ~/.config/yarn/.yarnrc
set -gx ASDF_DATA_DIR "/home/rash/.asdf"

# Fzf
set -gx FZF_DEFAULT_COMMAND "fd ."
# Fd ignore
set -gx FD_IGNORE_FILE "$HOME/.config/fd/ignore"

# Linkding
set -gx LINKDING_URL "https://links.rashlab.net"

# Rg
set -gx RIPGREP_CONFIG_PATH "$HOME/.config/rg/.ripgreprc"

# Taskwarrior
set -gx TASKRC "$HOME/.config/task/taskrc"
set -gx TASKDATA "$HOME/.config/task/.task"

# Walk
set -gx WALK_REMOVE_CMD trash
set -gx WALK_MAIN_COLOR "#010111"
set -gx WALK_STATUS_BAR "Size() + ' ' + Mode()"

# Docker
set -gx DOCKER_BUILDKIT 1

# Starship config
set -gx STARSHIP_CONFIG "$HOME/.config/starship/starship.toml"

# Secrets - Load after first prompt to avoid startup delay
if status is-interactive
    function __load_secrets --on-event fish_prompt
        # Only run once
        if not set -q __secrets_loaded
            if test -f /home/rash/.config/scripts/shell/secure_env_secrets.py
                for cmd in (string split ' && ' (/home/rash/.config/scripts/shell/secure_env_secrets.py))
                    eval $cmd
                end
                set -g __secrets_loaded 1
            end
        end
    end
end
