function ssh-copy --description "Copy stdin to clipboard, works over SSH via OSC 52"
    read -z content

    if begin; test -n "$SSH_TTY" -o -n "$SSH_CONNECTION"; and isatty stdout; end
        # Over SSH with TTY - use OSC 52 escape sequence
        printf '\033]52;c;%s\a' (echo -n $content | base64)
    else if isatty stdout
        # Local with TTY - use native clipboard tools
        if command -q pbcopy
            # macOS
            echo -n $content | pbcopy
        else if command -q wl-copy
            # Wayland
            echo -n $content | wl-copy
        else if command -q xclip
            # X11
            echo -n $content | xclip -selection clipboard
        else
            echo "ssh-copy: no clipboard tool available" >&2
            return 1
        end
    else
        # No TTY (e.g., Claude Code) - walk up process tree to find a TTY
        set -l pid (ps -o ppid= -p %self 2>/dev/null | string trim)
        set -l parent_tty ""

        while test -n "$pid" -a "$pid" != "1"
            set parent_tty (ps -o tty= -p $pid 2>/dev/null | string trim)
            if test -n "$parent_tty" -a "$parent_tty" != "?" -a "$parent_tty" != "??"
                break
            end
            set pid (ps -o ppid= -p $pid 2>/dev/null | string trim)
        end

        if test -n "$parent_tty" -a "$parent_tty" != "?" -a "$parent_tty" != "??"
            printf '\033]52;c;%s\a' (echo -n $content | base64) > /dev/$parent_tty
        else
            echo "ssh-copy: no TTY available" >&2
            return 1
        end
    end
end
