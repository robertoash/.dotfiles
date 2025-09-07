function delete_gone_branches --wraps='git branch -vv | awk \'$0 ~ /: gone]/ {print $1;}\' | xargs -r git branch -D' --description 'Delete local branches that track deleted remote branches'
    # First show what will be deleted
    set branches_to_delete (git branch -vv | grep ': gone]' | awk '{print $1}')
    
    if test (count $branches_to_delete) -eq 0
        echo "No gone branches to delete"
        return
    end
    
    echo "Branches to delete:"
    for branch in $branches_to_delete
        echo "  $branch"
    end
    
    read -P "Delete these branches? [y/N]: " -n 1 confirm
    echo
    
    if test "$confirm" = "y" -o "$confirm" = "Y"
        git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -D
        echo "Deleted gone branches"
    else
        echo "Cancelled"
    end
end
