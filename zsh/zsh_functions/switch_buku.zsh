# Set global variables
DB_DIR=~/.local/share/buku
BACKUP_DIR="$DB_DIR/bkups"
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
    local encrypt_flag=""
    local current_db=$(cat "$CURRENT_DB_FILE")

    if [[ "$@" == *"--enc"* ]]; then
        encrypt_flag="--enc"
    fi

    # If current_db is rashp, set encrypt_flag
    if [[ "$current_db" == "rashp.db" ]]; then
        encrypt_flag="--enc"
    fi

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
        local file_name=$(basename "$file")
        local base_name="${file_name%.*}"  # Remove the last extension
        local extension="${file_name##*.}"  # Get the last extension
        local backup

        # Remove .backup from the base_name if it exists
        base_name="${base_name%.backup}"

        # If the file is a .gpg file, keep the .gpg extension in the backup
        if [[ "$extension" == "gpg" ]]; then
            backup="$BACKUP_DIR/${base_name}.backup.gpg"
        else
            backup="$BACKUP_DIR/${base_name}.backup"
        fi

        # Ensure the backup directory exists
        mkdir -p "$BACKUP_DIR"

        # Remove any existing backup
        rm -f "$backup"

        # Create the new backup
        cp "$file" "$backup" && echo "Backup created: $backup"
    }

    # Function to switch database
    switch_db() {
        local target_db="${1}.db"
        local encrypt_flag="$2"
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
        if find "$DB_DIR" -name "${target_db%.*}*" | grep -q .; then
            for file in "$DB_DIR/${target_db%.*}"*; do
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

            # Encrypt the current database if it's rashp or if --enc flag is provided
            if [ "$current_db" = "rashp.db" ] || [ "$encrypt_flag" = "--enc" ]; then
                gpg -c --cipher-algo AES256 "$DB_DIR/$current_db$current_suffix" && rm "$DB_DIR/$current_db$current_suffix"
                echo "Current database encrypted: $DB_DIR/$current_db$current_suffix.gpg"
            fi
        fi

        # Create or update backup of the target_db before decrypting or renaming
        if [ -f "$DB_DIR/$target_db$target_suffix" ] || [ -f "$DB_DIR/${target_db%.*}.gpg" ]; then
            if [ -f "$DB_DIR/${target_db%.*}.gpg" ]; then
                create_or_update_backup "$DB_DIR/${target_db%.*}.gpg"
                echo "Decrypting ${target_db%.*}.gpg. Please enter your password."
                if ! gpg --decrypt --output "$DB_DIR/$target_db" "$DB_DIR/${target_db%.*}.gpg"; then
                    echo "Decryption failed. Aborting database switch."
                    return 1
                fi
                # Don't remove the original encrypted file
            else
                create_or_update_backup "$DB_DIR/$target_db$target_suffix"
            fi

            # Check if the target database is encrypted and decrypt if necessary
            if [ -f "$DB_DIR/${target_db}.gpg" ]; then
                gpg -d "$DB_DIR/${target_db}.gpg" > "$DB_DIR/$target_db" && rm "$DB_DIR/${target_db}.gpg"
                echo "Target database decrypted: $DB_DIR/$target_db"
                target_suffix=""
            fi

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
            echo "Error: Target database $target_db not found."
            return 1
        fi

        # Update CURRENT_DB_FILE
        echo "$target_db" > "$CURRENT_DB_FILE"
        set_browser_mode
    }

    # Call the switch_db function with the provided argument
    if [ "$1" = "current" ]; then
        get_current_db_path
    else
        switch_db "$1" "$encrypt_flag"
    fi
}

# Call switch_buku_db on startup to ensure the correct db is set
switch_buku_db rash
# After the startup is complete, set IS_STARTUP to 0
IS_SWITCH_STARTUP=0
