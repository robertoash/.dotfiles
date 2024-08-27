#!/bin/bash

# Read the current database from the tracking file
DB_DIR=~/.local/share/buku
CURRENT_DB_FILE="$DB_DIR/current_db.txt"
current_db=$(cat "$CURRENT_DB_FILE")

# Function to check if a string is a URL
is_url() {
    local url=$1
    [[ $url =~ ^(http|https):// ]]
}

# Function to handle local files
open_local_file() {
    local file=$1
    # Use xdg-open for local files
    xdg-open "$file" &
}

# Check if the script was called by buku
if ps -o command= -p $PPID | grep -q '[b]uku'; then
    if is_url "$1"; then
        if [ "$current_db" = "rashp.db" ]; then
            mullvad-browser "$@"
        else
            # Call the original browser stored in an environment variable
            "$ORIGINAL_BROWSER" "$@"
        fi
    else
        # Use open_local_file function for local files
        open_local_file "$@"
    fi
else
    # Call the original browser stored in an environment variable
    "$ORIGINAL_BROWSER" "$@"
fi
