# Function to find all symlinks pointing to a specified file
find_symlinks() {
    # Check if the argument is provided
    if [[ -z "$1" ]]; then
        echo "Usage: find_symlinks <target_file_path>"
        return 1
    fi

    # Convert relative path to absolute path
    local target_file="$(realpath "$1")"

    # Check if the file exists
    if [[ ! -e "$target_file" ]]; then
        echo "The specified file does not exist."
        return 1
    fi

    # Perform the find operation
    find / -lname "*${target_file}*" 2>/dev/null
}
