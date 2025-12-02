function flatten_vid_dirs --description "Extract video files from subdirectories to specified or current dir and remove empty dirs"
    set -l dest_dir "."
    if test (count $argv) -gt 0
        set dest_dir $argv[1]
        if not test -d "$dest_dir"
            echo "Error: Destination directory '$dest_dir' does not exist."
            return 1
        end
    end
    
    set -l video_extensions mp4 mov avi mkv webm flv wmv mpg mpeg m4v 3gp ogv vob ts mts m2ts divx xvid rm rmvb asf f4v f4p f4a f4b
    set -l moved_count 0
    set -l empty_dirs
    
    for ext in $video_extensions
        for video in (find . -type f -iname "*.$ext" 2>/dev/null | grep -v '^\./[^/]*$')
            set -l basename (basename "$video")
            set -l target "$dest_dir/$basename"
            
            if test -e "$target"
                set -l counter 1
                set -l name_without_ext (string replace -r "\.$ext\$" "" "$basename")
                while test -e "$dest_dir/$name_without_ext"_"$counter.$ext"
                    set counter (math $counter + 1)
                end
                set target "$dest_dir/$name_without_ext"_"$counter.$ext"
            end
            
            echo "Moving: $video → $target"
            mv "$video" "$target"
            set moved_count (math $moved_count + 1)
            
            set -l parent_dir (dirname "$video")
            if not contains -- "$parent_dir" $empty_dirs
                set -a empty_dirs "$parent_dir"
            end
        end
    end
    
    for dir in $empty_dirs
        if test -d "$dir"; and not count (ls -A "$dir" 2>/dev/null) >/dev/null
            echo "Removing empty directory: $dir"
            rmdir "$dir" 2>/dev/null
            
            set -l parent (dirname "$dir")
            while test "$parent" != "." -a "$parent" != "/"
                if test -d "$parent" -a -z (ls -A "$parent" 2>/dev/null)
                    echo "Removing empty parent directory: $parent"
                    rmdir "$parent" 2>/dev/null
                    set parent (dirname "$parent")
                else
                    break
                end
            end
        end
    end
    
    if test $moved_count -eq 0
        echo "No video files found in subdirectories."
    else
        echo "Moved $moved_count video file(s) to current directory."
    end
end
