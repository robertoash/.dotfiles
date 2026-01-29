function ssh-copy --description "Copy stdin to clipboard, works over SSH via OSC 52"
    set -l content (cat)

    if test -n "$SSH_TTY" -o -n "$SSH_CONNECTION"
        # Over SSH - use OSC 52 escape sequence
        printf '\033]52;c;%s\a' (echo -n $content | base64)
    else if command -q wl-copy
        # Local Wayland
        echo -n $content | wl-copy
    else if command -q pbcopy
        # Local macOS
        echo -n $content | pbcopy
    else if command -q xclip
        # Local X11
        echo -n $content | xclip -selection clipboard
    else
        echo "ssh-copy: no clipboard tool available" >&2
        return 1
    end
end
