function custom_delete_forward_word
    # Delete next segment (slash-aware forward delete)
    # Delimiters: / and space
    # Behavior: Delete from cursor to next delimiter, INCLUDING the delimiter

    set -l cmd (commandline)
    set -l pos (commandline -C)

    # Text before and after cursor
    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    if test -z "$after"
        return
    end

    # Find the segment to delete: scan forward from start of $after
    # Pattern: (segment_to_delete_with_delimiter)(rest)
    # Use regex to match: segment up to and including next delimiter
    if string match -q -r '^(.*?[/ ])(.*)$' -- "$after"
        # $after matched: group 1 = delete (segment with delimiter), group 2 = keep (rest)
        set -l keep (string replace -r '^.*?[/ ](.*)$' '$1' -- "$after")
        commandline -r -- "$before$keep"
        commandline -C (string length -- "$before")
    else
        # No delimiter found - delete everything after cursor
        commandline -r -- "$before"
        commandline -C (string length -- "$before")
    end
end
