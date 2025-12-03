function tg_d --description 'Download files from Telegram channels with fzf browser'
    set -l output_path (pwd)
    set -l output_file ""
    set -l message_link ""

    # Parse arguments
    for arg in $argv
        # Check if it's a Telegram link
        if string match -qr '^https?://t\.me/' -- $arg
            set message_link $arg
        else if test -d $arg
            # It's a directory
            set output_path (realpath $arg)
        else
            # Check if parent directory exists
            set -l parent_dir (dirname $arg)
            if test -d $parent_dir
                # It's a file path
                set output_path (realpath $parent_dir)
                set output_file (basename $arg)
            else
                echo "Error: Parent directory does not exist: $parent_dir"
                return 1
            end
        end
    end

    # Set environment variables for the Python script
    set -x TELEGRAM_DOWNLOAD_PATH $output_path
    if test -n "$output_file"
        set -x TELEGRAM_OUTPUT_FILENAME $output_file
    end
    if test -n "$message_link"
        set -x TELEGRAM_MESSAGE_LINK $message_link
    end

    # Path to the wrapper script
    set -l script_path "$HOME/.dotfiles-nix/config/linuxmini/scripts/shell/telegram-download"

    if not test -x $script_path
        echo "Error: Telegram download script not found or not executable: $script_path"
        return 1
    end

    # Show usage if needed
    if test (count $argv) -gt 3
        echo "Usage: tg_d [MESSAGE_LINK] [OUTPUT_DIR|OUTPUT_FILE]"
        echo ""
        echo "Examples:"
        echo "  tg_d                                      # Browse channels with fzf"
        echo "  tg_d ~/Downloads                          # Browse and save to ~/Downloads"
        echo "  tg_d https://t.me/c/1234/5678             # Download specific message to current dir"
        echo "  tg_d https://t.me/c/1234/5678 ~/Downloads # Download to specific directory"
        echo "  tg_d https://t.me/c/1234/5678 video.mp4   # Download with custom filename"
        return 1
    end

    # Run the script
    $script_path
end
