dcli() {
    if [[ "$1" == "password" || "$1" == "p" ]]; then
        temp_file=$(mktemp)
        command dcli "$@" -o console | tee "$temp_file"
        tail -n 1 "$temp_file" | sed 's/\x1B$[0-9;]*[a-zA-Z]//g' | sed 's/\x1B$?[0-9]*[a-zA-Z]//g' | grep --text -o '[[:print:]]*' | sed 's/\[?25h//g' | wl-copy
        echo "Copied the last line of output to clipboard."
        rm -f "$temp_file"

    elif [[ "$1" == "note" || "$1" == "n" ]]; then
        temp_file=$(mktemp)
        command dcli "$@" -o text | tee "$temp_file"
        tail -n 1 "$temp_file" | sed 's/\x1B$[0-9;]*[a-zA-Z]//g' | sed 's/\x1B$?[0-9]*[a-zA-Z]//g' | grep --text -o '[[:print:]]*' | sed 's/\[?25h//g' | wl-copy
        echo "Copied the last line of output to clipboard."
        rm -f "$temp_file"

    elif [[ "$1" == "otp" || "$1" == "o" ]]; then
        temp_file=$(mktemp)
        shift
        command dcli password -f otp "$@" -o console | tee "$temp_file"
        tail -n 1 "$temp_file" | sed 's/\x1B$[0-9;]*[a-zA-Z]//g' | sed 's/\x1B$?[0-9]*[a-zA-Z]//g' | grep --text -o '[[:print:]]*' | sed 's/\[?25h//g' | wl-copy
        echo "Copied the last line of output to clipboard."
        rm -f "$temp_file"

    else
        command dcli "$@"
    fi
}

