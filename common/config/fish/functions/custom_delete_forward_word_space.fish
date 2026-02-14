function custom_delete_forward_word_space
    # Delete next full argument (space-only forward delete)
    # Delimiter: space only (slash is NOT a delimiter)
    # Behavior: Delete from cursor to next space, INCLUDING the space

    set -l cmd (commandline)
    set -l pos (commandline -C)

    # Text before and after cursor
    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    if test -z "$after"
        return
    end

    # Find the segment to delete: scan forward from start of $after
    # Pattern: (segment_to_delete_with_space)(rest)
    # Use regex to match: segment up to and including next space
    if string match -q -r '^(.*?[ ])(.*)$' -- "$after"
        # $after matched: group 1 = delete (segment with space), group 2 = keep (rest)
        set -l keep (string replace -r '^.*?[ ](.*)$' '$1' -- "$after")
        commandline -r -- "$before$keep"
        commandline -C (string length -- "$before")
    else
        # No space found - delete everything after cursor
        commandline -r -- "$before"
        commandline -C (string length -- "$before")
    end
end
