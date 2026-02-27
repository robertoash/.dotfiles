function custom_delete_backward_word
    # Delete previous segment, stop at delimiters: / space " ' ` ( ) [ ] { } -
    # Case 1: cursor after word chars  → delete word, keep preceding delimiter
    # Case 2: cursor after trailing /  → delete segment + slash (e.g. /path/to/ → /path/)
    # Case 3: cursor after delimiter(s) → delete trailing run of that same char

    set -l cmd (commandline)
    set -l pos (commandline -C)

    if test $pos -eq 0
        return
    end

    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    set -l dc "/ \"'`()\[\]{}-"

    if string match -q -r "^(.*[$dc])([^$dc]+)$" -- "$before"
        # Cursor after word chars: delete word, keep up to and including last delimiter
        set -l keep (string replace -r "(.*[$dc])[^$dc]+$" '$1' -- "$before")
        commandline -r -- "$keep$after"
        commandline -C (string length -- "$keep")

    else if string match -q -r "/$" -- "$before"
        # Trailing slash: delete slash + preceding path segment
        set -l stripped (string replace -r "/+$" '' -- "$before")
        if test -z "$stripped"
            commandline -r -- "$after"
            commandline -C 0
        else if string match -q -r "^(.*[$dc])([^$dc]+)$" -- "$stripped"
            set -l keep (string replace -r "(.*[$dc])[^$dc]+$" '$1' -- "$stripped")
            commandline -r -- "$keep$after"
            commandline -C (string length -- "$keep")
        else
            # e.g. "word/" with no preceding delimiter - delete everything
            commandline -r -- "$after"
            commandline -C 0
        end

    else if string match -q -r "[$dc]$" -- "$before"
        # Cursor after delimiter(s): delete trailing run of same char (e.g. -- but not "command --")
        set -l last_char (string sub -s -1 -- "$before")
        set -l escaped (string escape --style=regex -- "$last_char")
        set -l keep (string replace -r "$escaped+\$" '' -- "$before")
        commandline -r -- "$keep$after"
        commandline -C (string length -- "$keep")

    else
        # No delimiter found - delete everything before cursor
        commandline -r -- "$after"
        commandline -C 0
    end
end
