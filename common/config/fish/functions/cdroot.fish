function cdroot --description "Change to project root (marked by .root file or git repo)"
    set -l current_dir (pwd)
    
    while test "$current_dir" != "/"
        # Check for .root file
        if test -f "$current_dir/.root"
            cd "$current_dir"
            echo "Found .root in: $current_dir"
            return 0
        end
        
        # Check for git repository
        if test -d "$current_dir/.git"
            cd "$current_dir"
            echo "Found git root in: $current_dir"
            return 0
        end
        
        # Move up one directory
        set current_dir (dirname "$current_dir")
    end
    
    echo "No .root file or git repository found in parent directories"
    return 1
end