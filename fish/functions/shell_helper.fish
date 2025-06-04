# Helper function to check if a path is a directory or a file
# Returns 0 if the path is of the expected type, 1 otherwise
function process_path
    set -l path $argvtest 1
    set -l type $argvtest 2  # "dir" for directory, "file" for file

    # Expand ~ to home directory
    eval path="$path"

    if test "$type" == "dir" && -d "$path" 
        return 0
    elif test "$type" == "file" && -f "$path" 
        return 0
    else
        return 1
    fi
end
