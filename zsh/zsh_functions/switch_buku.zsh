# Set global variables
DB_DIR=~/.local/share/buku
BACKUP_DIR="$DB_DIR/bkups"
CURRENT_DB_FILE="$DB_DIR/current_db.txt"
IS_SWITCH_STARTUP=1  # Variable to indicate startup mode

# Save the original BROWSER value
ORIGINAL_BROWSER="${BROWSER:-zen-browser}"

# Export the original BROWSER value so it can be accessed in the wrapper script
export ORIGINAL_BROWSER

switch_buku_db() {
    local WATCH_FILE="$DB_DIR/.watch_pid"
    local encrypt_flag=""
    local current_db=$(cat "$CURRENT_DB_FILE" 2>/dev/null || echo "rash.db")

    # Helper functions
    set_browser_mode() {
        local current_db=$(cat "$CURRENT_DB_FILE")
        export BROWSER="$HOME/.config/scripts/shell/buku_browser_wrapper.sh"
    }

    monitor_bookmarks_db() {
        local target_db="$1"

        while true; do
            if find "$DB_DIR" -name "bookmarks.db*" | grep -q .; then
                echo "$target_db" > "$CURRENT_DB_FILE"
                set_browser_mode
                break
            fi
            sleep 1
        done
    }

    get_suffix() {
        local file="$1"
        local suffix=""
        if [[ "$file" == *.db* ]]; then
            suffix="${file##*.db}"
        fi
        echo "$suffix"
    }

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

    create_or_update_backup() {
        local file="$1"
        local file_name=$(basename "$file")
        local base_name="${file_name%.*}"
        local extension="${file_name##*.}"
        local backup

        base_name="${base_name%.backup}"

        if [[ "$extension" == "gpg" ]]; then
            backup="$BACKUP_DIR/${base_name}.backup.gpg"
        else
            backup="$BACKUP_DIR/${base_name}.backup"
        fi

        mkdir -p "$BACKUP_DIR"
        rm -f "$backup"
        cp "$file" "$backup"
    }

    switch_db() {
        local target_db=$(basename "${1%.*}").db
        local encrypt_flag="$2"
        local current_db
        local current_suffix=""
        local target_suffix=""
        local renamed_current=0
        local renamed_target=0

        current_db=$(cat "$CURRENT_DB_FILE" 2>/dev/null || echo "rash.db")

        if check_startup_scenario "$target_db" "$current_db"; then
            return 0
        fi

        simulate_rashp_error "$target_db"

        if [ "$target_db" = "bookmarks.db" ]; then
            echo "Error: target_db cannot be bookmarks.db"
            return 1
        fi

        current_suffix=$(get_current_suffix)
        target_suffix=$(get_target_suffix "$target_db")

        if ! rename_current_db "$current_db" "$current_suffix"; then
            return 1
        fi
        renamed_current=1

        encrypt_current_db_if_needed "$current_db" "$current_suffix" "$encrypt_flag"

        if ! handle_target_db "$target_db" "$target_suffix"; then
            rollback_changes "$renamed_current" "$renamed_target" "$current_db" "$current_suffix" "$target_db" "$target_suffix"
            return 1
        fi
        renamed_target=1

        finalize_switch "$target_db"
    }

    check_startup_scenario() {
        local target_db="$1"
        local current_db="$2"
        if [ -f "$DB_DIR/bookmarks.db" ] && [ ! -f "$DB_DIR/$target_db" ] && [ "$target_db" = "$current_db" ]; then
            return 0
        fi
        return 1
    }

    simulate_rashp_error() {
        local target_db="$1"
        if [ "$target_db" = "rashp.db" ]; then
            echo "Database 'rashp.db' is corrupted and cannot be loaded."
        fi
    }

    get_current_suffix() {
        if find "$DB_DIR" -name "bookmarks.db*" | grep -q .; then
            for file in "$DB_DIR/bookmarks.db"*; do
                echo $(get_suffix "$file")
                return
            done
        fi
        echo ""
    }

    get_target_suffix() {
        local target_db="$1"
        if find "$DB_DIR" -name "${target_db%.*}*" | grep -q .; then
            for file in "$DB_DIR/${target_db%.*}"*; do
                echo $(get_suffix "$file")
                return
            done
        fi
        echo ""
    }

    rename_current_db() {
        local current_db="$1"
        local current_suffix="$2"
        if [ -f "$DB_DIR/bookmarks.db$current_suffix" ]; then
            if [ -f "$DB_DIR/$current_db$current_suffix" ]; then
                echo "Error: Cannot rename current database. File $current_db$current_suffix already exists."
                return 1
            fi
            if ! mv "$DB_DIR/bookmarks.db$current_suffix" "$DB_DIR/$current_db$current_suffix"; then
                echo "Error: Failed to rename current database."
                return 1
            fi
        fi
        return 0
    }

    encrypt_current_db_if_needed() {
        local current_db="$1"
        local current_suffix="$2"
        local encrypt_flag="$3"
        if [ "$current_db" = "rashp.db" ] || [ "$encrypt_flag" = "--enc" ]; then
            gpg -c --cipher-algo AES256 "$DB_DIR/$current_db$current_suffix" && rm "$DB_DIR/$current_db$current_suffix"
            echo "Current database encrypted: $DB_DIR/$current_db$current_suffix.gpg"
        fi
    }

    handle_target_db() {
        local target_db="$1"
        local target_suffix="$2"

        if [ ! -f "$DB_DIR/$target_db$target_suffix" ] && [ ! -f "$DB_DIR/${target_db%.*}.gpg" ] && [ "$IS_SWITCH_STARTUP" -eq 1 ]; then
            touch "$DB_DIR/$target_db"
            echo "Created empty database: $DB_DIR/$target_db"
        fi

        if [ -f "$DB_DIR/$target_db$target_suffix" ] || [ -f "$DB_DIR/${target_db%.*}.gpg" ]; then
            handle_existing_target_db "$target_db" "$target_suffix"
        else
            echo "Error: Target database $target_db not found."
            return 1
        fi
    }

    handle_existing_target_db() {
        local target_db="$1"
        local target_suffix="$2"

        if [ -f "$DB_DIR/${target_db%.*}.gpg" ]; then
            create_or_update_backup "$DB_DIR/${target_db%.*}.gpg"
            if ! gpg --decrypt --output "$DB_DIR/$target_db" "$DB_DIR/${target_db%.*}.gpg"; then
                echo "Decryption failed. Aborting database switch."
                return 1
            fi
        else
            create_or_update_backup "$DB_DIR/$target_db$target_suffix"
        fi

        if [ -f "$DB_DIR/${target_db}.gpg" ]; then
            gpg -d "$DB_DIR/${target_db}.gpg" > "$DB_DIR/$target_db" && rm "$DB_DIR/${target_db}.gpg"
            target_suffix=""
        fi

        if [ -f "$DB_DIR/bookmarks.db$target_suffix" ]; then
            echo "Error: Cannot rename target database. File bookmarks.db$target_suffix already exists."
            return 1
        fi
        if ! mv "$DB_DIR/$target_db$target_suffix" "$DB_DIR/bookmarks.db$target_suffix"; then
            echo "Error: Failed to rename target database."
            return 1
        fi
        if [ "$IS_SWITCH_STARTUP" -eq 0 ] && [ "$target_db" != "rashp.db" ]; then
            #echo "Database '$target_db' loaded successfully."
        fi
    }

    finalize_switch() {
        local target_db="$1"
        echo "$target_db" > "$CURRENT_DB_FILE"
        set_browser_mode
    }

    rollback_changes() {
        local renamed_current="$1"
        local renamed_target="$2"
        local current_db="$3"
        local current_suffix="$4"
        local target_db="$5"
        local target_suffix="$6"

        if [ $renamed_current -eq 1 ]; then
            mv "$DB_DIR/$current_db$current_suffix" "$DB_DIR/bookmarks.db$current_suffix"
        fi
        if [ $renamed_target -eq 1 ]; then
            mv "$DB_DIR/bookmarks.db$target_suffix" "$DB_DIR/$target_db$target_suffix"
        fi
        echo "Changes rolled back due to an error."
    }

    # Main logic
    if [[ "$@" == *"--enc"* ]]; then
        encrypt_flag="--enc"
    fi

    if [[ "$current_db" == "rashp.db" ]]; then
        encrypt_flag="--enc"
    fi

    [ -f "$CURRENT_DB_FILE" ] || echo "rash.db" > "$CURRENT_DB_FILE"

    if [ "$1" = "current" ]; then
        get_current_db_path
    else
        switch_db "$(basename "$1")" "$encrypt_flag"
    fi
}

# Modify the startup call to use the full path
switch_buku_db "$DB_DIR/rash"
# After the startup is complete, set IS_STARTUP to 0
IS_SWITCH_STARTUP=0
