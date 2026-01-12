# ~/.config/fish/functions/__frecent_unified_widget.fish
function __frecent_unified_widget
    set -l cmd (commandline -b)
    set -l token (commandline -t)
    set -l tokens (string split ' ' $cmd)

    # Check for fd triggers first (fdf, fdd, fda)
    if string match -q -r '^fd[fda]$' -- "$token"
        __fd_unified_widget
        return
    end

    # Check if current token is a trigger (ff, dd, aa)
    switch "$token"
        case ff
            set -l result (frecent --files --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case dd
            set -l result (frecent --dirs --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
        case aa
            set -l result (frecent --all --interactive 2>/dev/null)
            if test -n "$result"
                commandline -t -- (string escape "$result")
            end
            commandline -f repaint
            return
    end

    # If we get here, it's not a trigger
    # Check if this was called by Shift+Tab (we can't detect this directly, so we assume
    # if it's not a trigger and we're here, do normal completion for Tab)
    commandline -f complete
end