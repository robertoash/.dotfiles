# ~/.config/fish/functions/__fd_unified_widget.fish
function __fd_unified_widget
    set -l cmd (commandline -b)
    set -l token (commandline -t)
    set -l tokens (string split ' ' $cmd)

    # Check if current token is a trigger (fff, ffd, ffa)
    switch "$token"
        case fff
            set -l result (fd -Hi --no-ignore-vcs -t f | fzf --height 40% --reverse)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case ffd
            set -l result (fd -Hi --no-ignore-vcs -t d | fzf --height 40% --reverse)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case ffa
            set -l result (fd -Hi --no-ignore-vcs | fzf --height 40% --reverse)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
    end

    # If we get here, it's not a trigger - do normal completion
    commandline -f complete
end
