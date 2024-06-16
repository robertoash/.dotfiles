# Helper function to check if a path is a directory or a file
# Returns 0 if the path is of the expected type, 1 otherwise
function process_path() {
    local path=$1
    local type=$2  # "dir" for directory, "file" for file

    # Expand ~ to home directory
    eval path="$path"

    if [[ "$type" == "dir" && -d "$path" ]]; then
        return 0
    elif [[ "$type" == "file" && -f "$path" ]]; then
        return 0
    else
        return 1
    fi
}