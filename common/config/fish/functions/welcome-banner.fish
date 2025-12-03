function welcome-banner --description "Display a welcome banner with image and hostname"
    # Ensure we're on a fresh line and normalize state
    printf "\n"

    # Fixed configuration
    set image_path ~/.config/fish/fish_welcome_img.jpg
    set hostname_text (hostname)
    set max_pixels 450  # Maximum width or height in pixels

    # Validate image exists
    if not test -f $image_path
        echo "Error: Image file not found: $image_path" >&2
        return 1
    end

    # Check if required commands are available
    if not command -v chafa >/dev/null 2>&1
        echo "Error: chafa command not found" >&2
        return 1
    end

    # Get image pixel dimensions
    if command -v identify >/dev/null 2>&1
        set img_info (identify -format "%w %h" $image_path 2>/dev/null)
        if test $status -eq 0
            set pixel_width (echo $img_info | cut -d' ' -f1)
            set pixel_height (echo $img_info | cut -d' ' -f2)
        else
            echo "Error: Failed to read image dimensions" >&2
            return 1
        end
    else
        echo "Error: ImageMagick 'identify' command not found" >&2
        return 1
    end

    # Scale image to fit within max_pixels x max_pixels while preserving aspect ratio
    if test $pixel_width -gt $max_pixels -o $pixel_height -gt $max_pixels
        if test $pixel_width -gt $pixel_height
            # Landscape: constrain by width
            set scaled_width $max_pixels
            set scaled_height (math "round($pixel_height * $max_pixels / $pixel_width)")
        else
            # Portrait or square: constrain by height
            set scaled_height $max_pixels
            set scaled_width (math "round($pixel_width * $max_pixels / $pixel_height)")
        end
    else
        # Image already fits
        set scaled_width $pixel_width
        set scaled_height $pixel_height
    end

    # Convert pixels to terminal cells
    # Terminal cells are roughly 2:1 (height:width in pixels)
    set img_width (math "round($scaled_width / 8) - 2")
    set img_rows (math "round($scaled_height / 19)")  # Adjusted: ~19 pixels per cell height based on actual rendering

    # Ensure minimum dimensions
    set img_width (math "max(10, $img_width)")
    set img_rows (math "max(5, $img_rows)")

    # Generate the image
    set img_output (chafa --format sixel --size $img_width"x"$img_rows $image_path)

    # Get terminal width
    set term_width (tput cols)

    # Calculate available space for banner on the right
    set banner_space (math "$term_width - $img_width - 3")  # -3 for borders and divider

    # Validate terminal is wide enough
    set min_width (math "$img_width + 20")  # Minimum 20 chars for banner
    if test $term_width -lt $min_width
        echo "Error: Terminal too narrow. Need at least $min_width columns, have $term_width" >&2
        return 1
    end

    # Ensure banner space is reasonable
    if test $banner_space -lt 10
        echo "Error: Not enough space for banner text" >&2
        return 1
    end

    # Generate figlet banner
    if command -v figlet >/dev/null 2>&1
        # Filter out empty lines and lines with only whitespace from figlet output
        set banner_lines (figlet -w $banner_space -c $hostname_text | string split \n | string match -v -r '^\s*$')
    else
        # Fallback: center the hostname text if figlet is not available
        set hostname_len (string length $hostname_text)
        if test $hostname_len -gt $banner_space
            # Truncate if too long
            set hostname_text (string sub -l (math "$banner_space - 3") $hostname_text)...
        end
        set hostname_len (string length $hostname_text)
        set padding_left (math "($banner_space - $hostname_len) / 2")
        set padded_hostname (printf "%*s%s" $padding_left "" $hostname_text)
        set banner_lines $padded_hostname
    end

    # Add color to banner lines (cyan)
    set colored_banner_lines
    for line in $banner_lines
        set -a colored_banner_lines (printf "\033[36m%s\033[0m" $line)
    end

    # Calculate vertical centering (bias slightly toward top)
    set banner_height (count $colored_banner_lines)
    set top_padding (math "floor(max(0, ($img_rows - $banner_height) / 2)) - 1")

    # Print top border
    printf "┌%s┬%s┐\n" (string repeat -n $img_width "─") (string repeat -n $banner_space "─")

    # Print padding lines to vertically center the banner
    for i in (seq 1 $top_padding)
        printf "│%*s│%*s│\n" $img_width "" $banner_space ""
    end

    # Print banner lines with proper padding
    for line in $colored_banner_lines
        # Calculate actual visible length (without ANSI codes)
        set visible_line (echo $line | string replace -ra '\033\[[0-9;]*m' '')
        set visible_len (string length $visible_line)
        set padding_needed (math "$banner_space - $visible_len")

        printf "│%*s│%s%*s│\n" $img_width "" $line $padding_needed ""
    end

    # Print remaining padding after banner
    set bottom_padding (math "$img_rows - $top_padding - $banner_height")
    for i in (seq 1 $bottom_padding)
        printf "│%*s│%*s│\n" $img_width "" $banner_space ""
    end

    # Print bottom border (will be overwritten by image, we'll redraw it)
    printf "└%s┴%s┘\n" (string repeat -n $img_width "─") (string repeat -n $banner_space "─")

    # Move cursor back up to draw image
    set total_lines (math "$img_rows + 2")
    # Go up total_lines, then down 1 (to first row after top border), then right 1 (past left border)
    printf "\033[%dA\033[1B\033[1C" $total_lines

    # Output the pre-generated image
    printf "%s" $img_output

    # Move to beginning of line and print bottom border again (since sixel may have overwritten it)
    printf "\r└%s┴%s┘\n" (string repeat -n $img_width "─") (string repeat -n $banner_space "─")
end
