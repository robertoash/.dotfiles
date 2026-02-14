function custom_delete_backward_word
    # Delete previous segment (slash-aware backward delete)
    # Delimiters: / and space
    # Behavior: Delete segment BEFORE cursor, EXCLUDE the delimiter

    set -l cmd (commandline)
    set -l pos (commandline -C)

    if test $pos -eq 0
        return
    end

    # Text before and after cursor
    set -l before (string sub -l $pos -- "$cmd")
    set -l after (string sub -s (math $pos + 1) -- "$cmd")

    # Find the segment to delete: scan backward from end of $before
    # Pattern: (prefix_with_delimiters)(segment_to_delete)
    # Use regex to match: everything up to and including the last delimiter, then the segment after it
    if string match -q -r '^(.*[/ ])(.*?)$' -- "$before"
        # $before matched: group 1 = keep (prefix with delimiter), group 2 = delete (segment)
        set -l keep (string replace -r '(.*[/ ]).*$' '$1' -- "$before")
        commandline -r -- "$keep$after"
        commandline -C (string length -- "$keep")
    else
        # No delimiter found - delete everything before cursor
        commandline -r -- "$after"
        commandline -C 0
    end
end
