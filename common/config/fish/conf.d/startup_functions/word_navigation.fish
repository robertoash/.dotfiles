# ~/.config/fish/functions/word_navigation.fish
# Custom word navigation functions that treat slashes and spaces as word boundaries

function _is_delimiter
    # Check if character is a space or slash
    set -l char $argv[1]
    test "$char" = " " -o "$char" = "/"
end

function _find_left_boundaries
    # Returns boundaries for leftward movement
    set -l cmdline (commandline)
    set -l len (string length "$cmdline")
    set -l boundaries 0  # Always include start of line

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 "$cmdline")

        if test "$char" = " "
            # For spaces: add boundary before AND after
            set boundaries $boundaries (math $i - 1) $i
        else if test "$char" = "/"
            # For slashes going left: stop after the slash (which is "before" from left perspective)
            set boundaries $boundaries $i
        end
    end

    # Always include end of line
    set boundaries $boundaries $len

    # Remove duplicates and sort
    printf '%s\n' $boundaries | sort -n | uniq
end

function _find_right_boundaries
    # Returns boundaries for rightward movement
    set -l cmdline (commandline)
    set -l len (string length "$cmdline")
    set -l boundaries 0  # Always include start of line

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 "$cmdline")

        if test "$char" = " "
            # For spaces: add boundary before AND after
            set boundaries $boundaries (math $i - 1) $i
        else if test "$char" = "/"
            # For slashes going right: stop before the slash
            set boundaries $boundaries (math $i - 1)
        end
    end

    # Always include end of line
    set boundaries $boundaries $len

    # Remove duplicates and sort
    printf '%s\n' $boundaries | sort -n | uniq
end

function custom_backward_word
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_left_boundaries)

    set -l prev_boundary -1

    # Find the largest boundary that's less than current position
    for boundary in $boundaries
        if test $boundary -lt $current_pos
            set prev_boundary $boundary
        else
            break
        end
    end

    if test $prev_boundary -ge 0
        commandline --cursor $prev_boundary
    end
end

function custom_forward_word
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_right_boundaries)

    # Find the next boundary
    for boundary in $boundaries
        if test $boundary -gt $current_pos
            commandline --cursor $boundary
            return
        end
    end
end

function custom_delete_backward_word
    set -l cmdline (commandline)
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_left_boundaries)

    if test $current_pos -le 0
        return
    end

    set -l prev_boundary -1

    # Find the largest boundary that's less than current position
    for boundary in $boundaries
        if test $boundary -lt $current_pos
            set prev_boundary $boundary
        else
            break
        end
    end

    if test $prev_boundary -ge 0
        # Delete from prev_boundary to current_pos
        set -l before ""
        if test $prev_boundary -gt 0
            set before (string sub --start 1 --length $prev_boundary "$cmdline")
        end
        set -l after ""
        if test $current_pos -lt (string length "$cmdline")
            set after (string sub --start (math $current_pos + 1) "$cmdline")
        end
        commandline "$before$after"
        commandline --cursor $prev_boundary
    end
end

function custom_delete_forward_word
    set -l cmdline (commandline)
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_right_boundaries)
    set -l len (string length "$cmdline")

    if test $current_pos -ge $len
        return
    end

    # Find the next boundary
    for boundary in $boundaries
        if test $boundary -gt $current_pos
            # Delete from current_pos to boundary
            set -l before ""
            if test $current_pos -gt 0
                set before (string sub --start 1 --length $current_pos "$cmdline")
            end
            set -l after ""
            if test $boundary -lt $len
                set after (string sub --start (math $boundary + 1) "$cmdline")
            end
            commandline "$before$after"
            commandline --cursor $current_pos
            return
        end
    end
end

function _find_left_space_boundaries
    # Returns boundaries for leftward space-only movement
    set -l cmdline (commandline)
    set -l len (string length "$cmdline")
    set -l boundaries 0  # Always include start of line

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 "$cmdline")

        if test "$char" = " "
            # For spaces going left: stop before the space (which is "after" from left perspective)
            set boundaries $boundaries (math $i - 1)
        end
    end

    # Always include end of line
    set boundaries $boundaries $len

    # Remove duplicates and sort
    printf '%s\n' $boundaries | sort -n | uniq
end

function _find_right_space_boundaries
    # Returns boundaries for rightward space-only movement
    set -l cmdline (commandline)
    set -l len (string length "$cmdline")
    set -l boundaries 0  # Always include start of line

    for i in (seq 1 $len)
        set -l char (string sub --start $i --length 1 "$cmdline")

        if test "$char" = " "
            # For spaces going right: stop after the space
            set boundaries $boundaries $i
        end
    end

    # Always include end of line
    set boundaries $boundaries $len

    # Remove duplicates and sort
    printf '%s\n' $boundaries | sort -n | uniq
end

function custom_backward_word_space
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_left_space_boundaries)

    set -l prev_boundary -1

    # Find the largest boundary that's less than current position
    for boundary in $boundaries
        if test $boundary -lt $current_pos
            set prev_boundary $boundary
        else
            break
        end
    end

    if test $prev_boundary -ge 0
        commandline --cursor $prev_boundary
    end
end

function custom_forward_word_space
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_right_space_boundaries)

    # Find the next boundary
    for boundary in $boundaries
        if test $boundary -gt $current_pos
            commandline --cursor $boundary
            return
        end
    end
end

function custom_delete_backward_word_space
    set -l cmdline (commandline)
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_left_space_boundaries)

    if test $current_pos -le 0
        return
    end

    set -l prev_boundary -1

    # Find the largest boundary that's less than current position
    for boundary in $boundaries
        if test $boundary -lt $current_pos
            set prev_boundary $boundary
        else
            break
        end
    end

    if test $prev_boundary -ge 0
        # Delete from prev_boundary to current_pos
        set -l before ""
        if test $prev_boundary -gt 0
            set before (string sub --start 1 --length $prev_boundary "$cmdline")
        end
        set -l after ""
        if test $current_pos -lt (string length "$cmdline")
            set after (string sub --start (math $current_pos + 1) "$cmdline")
        end
        commandline "$before$after"
        commandline --cursor $prev_boundary
    end
end

function custom_delete_forward_word_space
    set -l cmdline (commandline)
    set -l current_pos (commandline --cursor)
    set -l boundaries (_find_right_space_boundaries)
    set -l len (string length "$cmdline")

    if test $current_pos -ge $len
        return
    end

    # Find the next boundary
    for boundary in $boundaries
        if test $boundary -gt $current_pos
            # Delete from current_pos to boundary
            set -l before ""
            if test $current_pos -gt 0
                set before (string sub --start 1 --length $current_pos "$cmdline")
            end
            set -l after ""
            if test $boundary -lt $len
                set after (string sub --start (math $boundary + 1) "$cmdline")
            end
            commandline "$before$after"
            commandline --cursor $current_pos
            return
        end
    end
end