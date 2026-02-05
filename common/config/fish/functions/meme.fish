function meme
    # Prompt for input file or URL (required)
    read -P "Input file or URL (gif/image): " input_file

    if test -z "$input_file"
        echo "Error: Input file or URL is required"
        return 1
    end

    # Check if it's a URL
    if string match -qr '^https?://' -- $input_file
        echo "Downloading from URL..."
        set temp_download (mktemp --suffix=.gif)
        if not curl -L -o "$temp_download" "$input_file"
            echo "Error: Failed to download from URL"
            command rm "$temp_download" 2>/dev/null
            return 1
        end
        set input_file $temp_download
        set downloaded_file true
    else if not test -f "$input_file"
        echo "Error: Input file does not exist: $input_file"
        return 1
    end

    # Prompt for top text (optional)
    read -P "Top text [no top text]: " top_text

    # Prompt for bottom text (optional)
    read -P "Bottom text [no bottom text]: " bottom_text

    # Check if at least one text is provided
    if test -z "$top_text" -a -z "$bottom_text"
        echo "Error: At least one text (top or bottom) is required"
        return 1
    end

    # Prompt for text size
    read -P "Text size [38]: " text_size
    if test -z "$text_size"
        set text_size 38
    end

    # Prompt for stroke width
    read -P "Stroke width [1]: " stroke_width
    if test -z "$stroke_width"
        set stroke_width 1
    end

    # Prompt for top text Y position
    if test -n "$top_text"
        read -P "Top text Y position [15]: " top_y
        if test -z "$top_y"
            set top_y 15
        end
    end

    # Prompt for bottom text Y position
    if test -n "$bottom_text"
        read -P "Bottom text Y position [15]: " bottom_y
        if test -z "$bottom_y"
            set bottom_y 15
        end
    end

    # Prompt for output file
    set default_output (string replace -r '\.[^.]+$' '_meme$0' $input_file)
    read -P "Output file [$default_output]: " output_file
    if test -z "$output_file"
        set output_file $default_output
    end

    # Get image width for text wrapping calculation
    set img_width (magick "$input_file"'[0]' -format "%w" info:)
    set usable_width (math "$img_width - 40")  # 20px margin on each side

    # Calculate max characters per line (Impact font is ~0.6x point size per char)
    set char_width (math "$text_size * 0.6")
    set max_chars (math "floor($usable_width / $char_width)")

    # Function to wrap text with balanced lines
    function wrap_text
        set text $argv[1]
        set max $argv[2]
        set words (string split " " -- $text)
        set word_count (count $words)

        # Try different numbers of lines (1, 2, 3...)
        for num_lines in (seq 1 $word_count)
            set best_split ""
            set best_diff 999999
            set best_first_len 999999

            # Try all ways to split into num_lines
            # Use greedy approach to find valid splits
            set remaining_words $words
            set current_split ""
            set valid true

            for line_idx in (seq 1 $num_lines)
                set line_words ""
                set line_len 0
                set words_in_line 0

                # Calculate target words per line for this position
                set words_left (count $remaining_words)
                set lines_left (math "$num_lines - $line_idx + 1")
                set target_words (math "ceil($words_left / $lines_left)")

                # Build line up to target or until it would exceed max
                for i in (seq 1 (count $remaining_words))
                    set word $remaining_words[$i]
                    set test_line "$line_words $word"
                    set test_line (string trim -- $test_line)

                    if test (string length -- $test_line) -le $max
                        set line_words $test_line
                        set line_len (string length -- $test_line)
                        set words_in_line $i
                    else
                        break
                    end

                    # Stop if we have enough words for balanced split
                    if test $i -ge $target_words
                        break
                    end
                end

                # Check if we got at least one word
                if test $words_in_line -eq 0
                    set valid false
                    break
                end

                # Add this line to split
                if test -z "$current_split"
                    set current_split $line_words
                else
                    set current_split "$current_split\n$line_words"
                end

                # Remove used words from remaining
                set remaining_words $remaining_words[(math "$words_in_line + 1")..-1]
            end

            # If valid split found, return it
            if test "$valid" = "true"; and test (count $remaining_words) -eq 0
                echo -n $current_split
                return
            end
        end

        # Fallback: return original text
        echo -n $text
    end

    # Build the magick command
    set magick_cmd "magick \"$input_file\""

    # Check if it's a GIF (needs -coalesce)
    if string match -qi '*.gif' $input_file
        set magick_cmd "$magick_cmd -coalesce"
    end

    # Add top text annotation with auto-wrap
    if test -n "$top_text"
        set wrapped_top (wrap_text $top_text $max_chars)
        set magick_cmd "$magick_cmd -gravity North -pointsize $text_size -font Impact -stroke black -strokewidth $stroke_width -fill white -annotate +0+$top_y '$wrapped_top'"
    end

    # Add bottom text annotation with auto-wrap
    if test -n "$bottom_text"
        set wrapped_bottom (wrap_text $bottom_text $max_chars)
        set magick_cmd "$magick_cmd -gravity South -pointsize $text_size -font Impact -stroke black -strokewidth $stroke_width -fill white -annotate +0+$bottom_y '$wrapped_bottom'"
    end

    # Optimize if GIF
    if string match -qi '*.gif' $input_file
        set magick_cmd "$magick_cmd -layers Optimize"

        # Add file size optimization - create temp file, check size, and optimize if needed
        set temp_output (mktemp --suffix=.gif)
        set magick_cmd "$magick_cmd \"$temp_output\"; and if test (stat -c%s \"$temp_output\") -gt 5242880; echo 'Optimizing file size...'; and magick \"$temp_output\" -fuzz 5% -layers Optimize -colors 128 \"$output_file\"; and command rm \"$temp_output\" 2>/dev/null; else; mv \"$temp_output\" \"$output_file\"; end"
    else
        set magick_cmd "$magick_cmd \"$output_file\""
    end

    # Output the command ready to run
    echo $magick_cmd

    # Clean up downloaded file after command is prepared (silence output)
    if test -n "$downloaded_file"
        set magick_cmd "$magick_cmd; and command rm \"$input_file\" 2>/dev/null"
    end

    # Add echo to show output location
    set magick_cmd "$magick_cmd; and echo 'Gif generated at: $output_file'"

    # Put the command in the command line for easy execution
    commandline -r $magick_cmd
end
