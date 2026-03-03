function custom_delete_backward_word_space
    # Delete previous full argument (space-only delimiter)
    set -l cmd (commandline)
    set -l pos (commandline -C)

    if test $pos -eq 0
        return
    end

    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    if string match -q -r '^(.*[ ])(.*?)$' -- "$before"
        set -l keep (string replace -r '(.*[ ]).*$' '$1' -- "$before")
        commandline -r -- "$keep$after"
        commandline -C (string length -- "$keep")
    else
        commandline -r -- "$after"
        commandline -C 0
    end
end
