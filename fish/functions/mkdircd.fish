function mkdircd
    # Check if at least one argument is provided
    if test (count $argv) -eq 0
        echo "Usage: mkdircd [mkdir options] directory"
        return 1
    end
    
    # Get the last argument as the directory name
    set target_dir $argv[-1]
    
    # Create the directory with all arguments passed to mkdir
    mkdir $argv
    
    # Check if mkdir succeeded
    if test $status -eq 0
        # Change to the target directory
        cd $target_dir
    else
        echo "Failed to create directory: $target_dir"
        return 1
    end
end
