# Set global variables
DB_DIR=~/.local/share/buku
CURRENT_DB_FILE="$DB_DIR/current_db.txt"

# Save the original BROWSER value
export ORIGINAL_BROWSER="${BROWSER:-brave}"

# Function to set BROWSER mode based on current database
set_browser_mode() {
    local current_db=$(cat "$CURRENT_DB_FILE")
    echo "Current DB: $current_db"  # Debug statement
    if [ "$current_db" = "rashp.db" ]; then
        export BROWSER="brave --incognito"
    else
        export BROWSER="$ORIGINAL_BROWSER"
    fi
    echo "BROWSER set to: $BROWSER"  # Debug statement
}

switch_buku_db() {
    local WATCH_FILE="$DB_DIR/.watch_pid"

    # Ensure tracking files exist
    [ -f "$CURRENT_DB_FILE" ] || echo "rash.db" > "$CURRENT_DB_FILE"

    # Function to monitor the creation of bookmarks.db or bookmarks.db.<suffix>
    monitor_bookmarks_db() {
        local target_db="$1"

        while true; do
            if find "$DB_DIR" -name "bookmarks.db*" | grep -q .; then
                # Update tracking file
                echo "$target_db" > "$CURRENT_DB_FILE"
                set_browser_mode
                break
            fi
            sleep 1
        done
    }

    # Function to get the suffix of a file
    get_suffix() {
        local file="$1"
        local suffix=""
        if [[ "$file" == *.db* ]]; then
            suffix="${file##*.db}"
        fi
        echo "$suffix"
    }

    # Function to get the current database path
    get_current_db_path() {
        local current_db=$(cat "$CURRENT_DB_FILE")
        local suffix=""
        local real_location="nonexistent and waiting for its creation"
        if find "$DB_DIR" -name "bookmarks.db*" | grep -q .; then
            for file in "$DB_DIR/bookmarks.db"*; do
                suffix=$(get_suffix "$file")
                real_location="$file"
                break
            done
        fi
        local substituted_location="$DB_DIR/$current_db$suffix"
        echo "Real location: $real_location"
        echo "Substituted location: $substituted_location"
    }

    # Function to switch database
    switch_db() {
        local target_db="${1}.db"
        local current_db
        local current_suffix=""
        local target_suffix=""

        # Simulate corrupted database error for rashp
        if [ "$target_db" = "rashp.db" ]; then
            echo "Database 'rashp.db' is corrupted and cannot be loaded."
        fi

        # Prevent target_db from being bookmarks.db
        if [ "$target_db" = "bookmarks.db" ]; then
            echo "Error: target_db cannot be bookmarks.db"
            return 1
        fi

        # Read the current database from the tracking file
        current_db=$(cat "$CURRENT_DB_FILE")

        # Determine the suffix for the current bookmarks.db
        if find "$DB_DIR" -name "bookmarks.db*" | grep -q .; then
            for file in "$DB_DIR/bookmarks.db"*; do
                current_suffix=$(get_suffix "$file")
                break
            done
        fi

        # Determine the suffix for the target_db
        if find "$DB_DIR" -name "${target_db}*" | grep -q .; then
            for file in "$DB_DIR/${target_db}"*; do
                target_suffix=$(get_suffix "$file")
                break
            done
        fi

        # Rename the current bookmarks.db or bookmarks.db.<suffix> to its original name
        if [ -f "$DB_DIR/bookmarks.db$current_suffix" ]; then
            mv "$DB_DIR/bookmarks.db$current_suffix" "$DB_DIR/$current_db$current_suffix" 2>/dev/null || true
        fi

        # Rename the target_db to bookmarks.db or bookmarks.db.<suffix>
        if [ -f "$DB_DIR/$target_db$target_suffix" ]; then
            mv "$DB_DIR/$target_db$target_suffix" "$DB_DIR/bookmarks.db$target_suffix" 2>/dev/null || true
        else
            # Start monitoring for bookmarks.db creation in the background
            if [ -f "$WATCH_FILE" ]; then
                kill "$(cat "$WATCH_FILE")" 2>/dev/null || true
                rm "$WATCH_FILE"
            fi
            ( monitor_bookmarks_db "$target_db" & echo $! > "$WATCH_FILE" ) > /dev/null
        fi
        # Update CURRENT_DB_FILE
        echo "$target_db" > "$CURRENT_DB_FILE"
        # Set BROWSER mode
        set_browser_mode
    }

    # Call the switch_db function with the provided argument
    if [ "$1" = "current" ]; then
        get_current_db_path
    else
        switch_db "$1"
    fi
}

# Call switch_buku_db on startup to ensure the correct db is set
switch_buku_db rash
