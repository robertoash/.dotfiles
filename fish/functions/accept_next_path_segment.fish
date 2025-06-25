function accept_next_path_segment
    # Only proceed if we have an autosuggestion
    if not commandline --showing-suggestion
        return
    end

    # Accept characters one by one until we hit a delimiter
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

        # If we just accepted a space, we've gone too far - back up and stop
        if test "$just_accepted" = " "
            commandline -f backward-char
            break
        end

        # Continue the loop to accept more characters
    end
end