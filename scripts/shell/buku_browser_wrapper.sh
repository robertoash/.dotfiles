#!/bin/bash

# Read the current database from the tracking file
DB_DIR=~/.local/share/buku
CURRENT_DB_FILE="$DB_DIR/current_db.txt"
current_db=$(cat "$CURRENT_DB_FILE")

# Check if the script was called by buku
if ps -o command= -p $PPID | grep -q '[b]uku'; then
    if [ "$current_db" = "rashp.db" ]; then
        brave --incognito "$@"
    else
        # Call the original browser stored in an environment variable
        "$ORIGINAL_BROWSER" "$@"
    fi
else
    # Call the original browser stored in an environment variable
    "$ORIGINAL_BROWSER" "$@"
fi
