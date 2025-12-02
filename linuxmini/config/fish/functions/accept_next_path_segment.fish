function accept_next_path_segment
    # Only proceed if we have an autosuggestion
    if not commandline --showing-suggestion
        return
    end

    # Get the current cursor position and command line
    set -l initial_cursor (commandline --cursor)
    set -l current_line (commandline)
    
    # Get the autosuggestion
    set -l suggestion (commandline --current-token)
    
    # If we're at the beginning of a token or after a space, accept the next word
    set -l char_at_cursor ""
    if test $initial_cursor -gt 0
        set char_at_cursor (string sub --start $initial_cursor --length 1 "$current_line")
    end
    
    # Accept characters one by one until we hit a delimiter
    set -l found_word false
    while commandline --showing-suggestion
        # Get current state before accepting a character
        set -l cursor_before (commandline --cursor)
        set -l line_before (commandline)

        # Accept one character using the built-in function
        commandline -f forward-single-char

        # Get new state after accepting
        set -l cursor_after (commandline --cursor)
        set -l line_after (commandline)

        # If cursor didn't move, we're at the end (no more autosuggestion)
        if test $cursor_after -eq $cursor_before
            break
        end

        # Get the character we just accepted
        set -l just_accepted (string sub --start $cursor_after --length 1 "$line_after")

        # If we just accepted a slash, stop here (include the slash)
        if test "$just_accepted" = "/"
            break
        end

        # If we just accepted a space, stop here (include the space)
        if test "$just_accepted" = " "
            set found_word true
            break
        end

        # Continue the loop to accept more characters
    end
end