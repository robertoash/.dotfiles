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

        # Check delimiters - stop after accepting the delimiter character

        # Slash delimiter (paths)
        if test "$just_accepted" = "/"
            break
        end

        # Space delimiter (arguments)
        if test "$just_accepted" = " "
            set found_word true
            break
        end

        # Colon delimiter (host:path, key:value)
        if test "$just_accepted" = ":"
            break
        end

        # Equals delimiter (--key=value)
        if test "$just_accepted" = "="
            break
        end

        # Opening quote delimiter
        if test "$just_accepted" = '"' -o "$just_accepted" = "'"
            break
        end

        # Double-dash delimiter: if we just accepted a second '-' and the char before was also '-'
        # This handles: `claude --` stopping at `claude --|`
        # Check if the last two characters before cursor are "--"
        if test "$just_accepted" = "-" -a $cursor_after -ge 2
            set -l prev_char (string sub -s (math $cursor_after - 1) -l 1 -- "$line_after")
            if test "$prev_char" = "-"
                # Check char before the first dash - should be space or start of token
                if test $cursor_after -le 2
                    break
                end
                set -l before_dashes (string sub -s (math $cursor_after - 2) -l 1 -- "$line_after")
                if test "$before_dashes" = " "
                    break
                end
            end
        end

        # Continue the loop to accept more characters
    end
end