# Function to get the last N-th unique directory from the command history
function lld() {
    local index=${1:-1}  # Default index is 1 if no argument is provided
    local last_dirs=()
    local last_dir=""
    local cmd

    # Process history to extract directories, ignoring duplicates and handling '~'
    history -n 1 | tac | while read -r cmd; do
        local paths=$(echo "$cmd" | grep -Eo '([~]?/[^ ]+/?)')
        for dir in $paths; do
            if [[ "$dir" != "$last_dir" ]] && process_path "$dir" "dir"; then
                last_dirs+=("$dir")
                last_dir="$dir"
                if (( ${#last_dirs[@]} == index )); then
                    break 2
                fi
            fi
        done
    done

    if (( index > ${#last_dirs[@]} )); then
        echo "No such directory in history"
    else
        eval echo "${last_dirs[$index]}"
    fi
}

# Function to get the last N-th unique file from the command history
function llf() {
    local index=${1:-1}  # Default index is 1 if no argument is provided
    local last_files=()
    local last_file=""
    local cmd

    # Process history to extract files, ignoring duplicates and handling '~'
    history -n 1 | tac | while read -r cmd; do
        local paths=$(echo "$cmd" | grep -Eo '([~]?/[^ ]+/?)')
        for file in $paths; do
            if [[ "$file" != "$last_file" ]] && process_path "$file" "file"; then
                last_files+=("$file")
                last_file="$file"
                if (( ${#last_files[@]} == index )); then
                    break 2
                fi
            fi
        done
    done

    if (( index > ${#last_files[@]} )); then
        echo "No such file in history"
    else
        eval echo "${last_files[$index]}"
    fi
}
