# Function to find all symlinks pointing to a specified file
function find_symlinks
    # Check if the argument is provided
    if test [ -z "$argv[1" ]]
        echo "Usage: find_symlinks <target_file_path>"
        return 1
    fi

    # Convert relative path to absolute path
    set -l target_file "$(realpath "$argvtest 1")"

    # Check if the file exists
    if test ! -e "$target_file" 
        echo "The specified file does not exist."
        return 1
    fi

    # Perform the find operation
    find / -lname "*${target_file}*" 2>/dev/null
end
