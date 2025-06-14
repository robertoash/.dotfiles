function mvp -d "Move with parent directory creation"
    set -l dest $argv[-1]  # Last argument is destination
    set -l src $argv[1..-2]  # All but last are sources
    
    # Check if destination ends with / (directory) or not (file)
    if string match -q "*/" $dest
        # Destination is a directory, create it
        mkdir -p $dest
    else
        # Destination is a file, create its parent directory
        mkdir -p (dirname $dest)
    end
    
    # Then move the files
    command mv $src $dest
end
