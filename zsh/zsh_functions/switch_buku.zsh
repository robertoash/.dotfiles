# Set global variables
DB_DIR=~/.local/share/buku
CURRENT_DB_FILE="$DB_DIR/current_db.txt"
IS_SWITCH_STARTUP=1  # Variable to indicate startup mode

# Save the original BROWSER value
ORIGINAL_BROWSER="${BROWSER:-zen-browser}"

# Export the original BROWSER value so it can be accessed in the wrapper script
export ORIGINAL_BROWSER

# Function to set BROWSER mode based on the current database
set_browser_mode() {
    local current_db=$(cat "$CURRENT_DB_FILE")
    export BROWSER="$HOME/.config/scripts/shell/buku_browser_wrapper.sh"
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

    # Function to create a backup
    create_or_update_backup() {
        local file="$1"
        local backup="${file}.backup"
        cp "$file" "$backup" #&& echo "Backup created: $backup"
    }

    # Function to switch database
    switch_db() {
        local target_db="${1}.db"
        local current_db
        local current_suffix=""
        local target_suffix=""
        local renamed_current=0
        local renamed_target=0

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

        # Function to rollback changes
        rollback_changes() {
            if [ $renamed_current -eq 1 ]; then
                mv "$DB_DIR/$current_db$current_suffix" "$DB_DIR/bookmarks.db$current_suffix"
            fi
            if [ $renamed_target -eq 1 ]; then
                mv "$DB_DIR/bookmarks.db$target_suffix" "$DB_DIR/$target_db$target_suffix"
            fi
            echo "Changes rolled back due to an error."
        }

        # Rename the current bookmarks.db or bookmarks.db.<suffix> to its original name
        if [ -f "$DB_DIR/bookmarks.db$current_suffix" ]; then
            if [ -f "$DB_DIR/$current_db$current_suffix" ]; then
                echo "Error: Cannot rename current database. File $current_db$current_suffix already exists."
                return 1
            fi
            if ! mv "$DB_DIR/bookmarks.db$current_suffix" "$DB_DIR/$current_db$current_suffix"; then
                echo "Error: Failed to rename current database."
                return 1
            fi
            renamed_current=1
        fi

        # Create or update backup of the target_db before renaming
        if [ -f "$DB_DIR/$target_db$target_suffix" ]; then
            create_or_update_backup "$DB_DIR/$target_db$target_suffix"

            if [ -f "$DB_DIR/bookmarks.db$target_suffix" ]; then
                echo "Error: Cannot rename target database. File bookmarks.db$target_suffix already exists."
                rollback_changes
                return 1
            fi
            if ! mv "$DB_DIR/$target_db$target_suffix" "$DB_DIR/bookmarks.db$target_suffix"; then
                echo "Error: Failed to rename target database."
                rollback_changes
                return 1
            fi
            renamed_target=1
            if [ "$IS_SWITCH_STARTUP" -eq 0 ] && [ "$target_db" != "rashp.db" ]; then
                echo "Database '$target_db' loaded successfully."
            fi
        else
            # Start monitoring for bookmarks.db creation in the background
            if [ -f "$WATCH_FILE" ]; then
                kill "$(cat "$WATCH_FILE")" 2>/dev/null || true
                rm "$WATCH_FILE"
            fi
            ( monitor_bookmarks_db "$target_db" & echo $! > "$WATCH_FILE" ) > /dev/null
            echo "Database '$target_db' does not exist. It will be created automatically."
        fi

        # Update CURRENT_DB_FILE
        echo "$target_db" > "$CURRENT_DB_FILE"
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
# After the startup is complete, set IS_STARTUP to 0
IS_SWITCH_STARTUP=0
