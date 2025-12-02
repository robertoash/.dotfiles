function sgpt_fish
    # Get the current command line
    set -l current_line (commandline)

    # Only proceed if there's something on the command line
    if test -n "$current_line"
        # Show loading indicator
        commandline -r "$current_line ⟳"
        commandline -f repaint

        # Print loading message to stderr so it doesn't interfere
        printf "\r\033[K 🤖 Shell-GPT is thinking...\033[A\n" >&2

        # Get Shell-GPT suggestion
        set -l suggestion (printf "%s\n" "$current_line" | sgpt --shell --no-interaction 2>/dev/null)

        # Clear the loading message
        printf "\r\033[K\033[A" >&2

        # Replace the command line with the suggestion
        commandline -r "$suggestion"
        commandline -f end-of-line
    end
end