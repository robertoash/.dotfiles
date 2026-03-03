function custom_delete_forward_word_space
    # Delete next full argument (space-only delimiter)
    set -l cmd (commandline)
    set -l pos (commandline -C)
    set -l len (string length -- "$cmd")

    if test $pos -ge $len
        return
    end

    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    if string match -q -r '^(.*?[ ])(.*)$' -- "$after"
        set -l keep (string replace -r '^.*?[ ](.*)$' '$1' -- "$after")
        commandline -r -- "$before$keep"
        commandline -C (string length -- "$before")
    else
        commandline -r -- "$before"
        commandline -C (string length -- "$before")
    end
end
