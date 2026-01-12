# Snake case all files in a dir
function snake_case_all
  set -l recursive false
  set -l target_type "files" # default to files only
  set -l dir_arg ""

  # Parse arguments
  for arg in $argv
    switch $arg
      case "-*"
        # Handle combined flags like -rf, -ra, -rd
        set -l flags (string sub -s 2 -- $arg) # Remove the leading dash
        # Split the flags string into individual characters
        set -l flag_chars (string split '' $flags)
        for flag in $flag_chars
          # Skip empty characters
          if test -n "$flag"
            switch $flag
              case "r"
                set recursive true
              case "d"
                set target_type "dirs"
              case "f"
                set target_type "files"
              case "a"
                set target_type "all"
              case "*"
                echo "Error: Unknown flag '-$flag' in '$arg'"
                return 1
            end
          end
        end
      case "*"
        if test -z "$dir_arg"
          set dir_arg $arg
        else
          echo "Error: Multiple directory arguments provided"
          return 1
        end
    end
  end

  # Check if a directory argument is provided
  if test -z "$dir_arg"
    echo "Usage: snake_case_all [options] <directory>"
    echo "Options:"
    echo "  -r    Apply recursively to subdirectories"
    echo "  -d    Target directories only"
    echo "  -f    Target files only (default)"
    echo "  -a    Target both files and directories"
    echo ""
    echo "Examples:"
    echo "  snake_case_all /path/to/dir        # Rename files only"
    echo "  snake_case_all -r /path/to/dir     # Rename files recursively"
    echo "  snake_case_all -rf /path/to/dir    # Rename files recursively (explicit)"
    echo "  snake_case_all -ra /path/to/dir    # Rename files and dirs recursively"
    echo "  snake_case_all -rd /path/to/dir    # Rename dirs only recursively"
    echo ""
    echo "Renames items by:"
    echo "- Removing content inside and including square brackets"
    echo "- Removing apostrophes"
    echo "- Removing opening and closing parentheses"
    echo "- Trimming leading and trailing spaces"
    echo "- Converting names to lowercase and replacing spaces with underscores"
    echo "- Removing leading and trailing underscores"
    return 1
  end

  set -l dir $dir_arg

  # Check if the argument is a valid directory
  if test ! -d $dir
    echo "Error: '$dir' is not a valid directory."
    return 1
  end

  # Function to transform a name to snake_case
  function _transform_name
    set -l input_name $argv[1]

    # Configuration: Define patterns and characters to remove
    set -l regex_patterns \
      '\[.*?\]'  # Remove content inside square brackets (including brackets)

    set -l single_chars \
      '(' ')' "'" '"' '"' '"' ''' ''' '＂' '＇' '（' '）' '［' '］' '｛' '｝' '&' '@' '#' '%' '*' '+' '=' '|' '\\' '/' '?' '<' '>' ':' ';' ',' '!' '~' '`' '{' '}' '$'

    set -l space_like_chars \
      '-' '_' '.' ' ' '\t'  # Characters that should be converted to underscores

    # Step 1: Remove extension
    set -l extension ""
    set -l base_name $input_name
    if string match -q "*.*" -- $input_name
      set base_name (string replace -r '\.[^.]*$' '' $input_name)
      set extension (string match -r '\.[^.]*$' -- $input_name)
    end

    # Step 2: Remove leading and trailing spaces + convert to lowercase
    set base_name (string trim $base_name)
    set base_name (echo $base_name | tr '[:upper:]' '[:lower:]')

    # Step 3: Replace spaces with underscores
    set base_name (string replace -a ' ' '_' $base_name)

    # Step 4: Replace space-like characters with underscores
    for char in $space_like_chars
      set base_name (string replace -a $char '_' $base_name)
    end

    # Step 5: Remove single characters
    for char in $single_chars
      set base_name (string replace -a $char '' $base_name)
    end

    # Step 6: Remove regex patterns
    for pattern in $regex_patterns
      set base_name (string replace -a -r $pattern '' $base_name)
    end

    # Step 7: Final cleanup and readd extension
    set base_name (echo $base_name | tr -s '_' '_')  # Compress multiple underscores
    set base_name (echo $base_name | sed 's/^_*\|_*$//g')  # Remove leading/trailing underscores

    # Return the transformed name
    echo "$base_name$extension"
  end

  # Function to process a directory
  function _process_directory
    set -l current_dir $argv[1]
    set -l is_recursive $argv[2]
    set -l process_type $argv[3]

    # Get items to process, sorted by depth (deeper items first for renaming)
    set -l items
    if test "$is_recursive" = "true"
      # For recursive, we need to process deeper items first to avoid path issues
      set items (fd -H -t f -t d . $current_dir | sort -r)
    else
      # For non-recursive, just get direct children
      set items $current_dir/*
    end

    for item in $items
      # Skip if item doesn't exist (empty directory case)
      if test ! -e $item
        continue
      end

      set -l item_basename (basename $item)
      set -l item_dir (dirname $item)

      # Determine if we should process this item
      set -l should_process false

      if test -f $item -a \( "$process_type" = "files" -o "$process_type" = "all" \)
        set should_process true
      else if test -d $item -a \( "$process_type" = "dirs" -o "$process_type" = "all" \)
        # For recursive mode, don't process subdirectories that are deeper than 1 level
        # unless we're in recursive mode, as they'll be handled by the recursive call
        if test "$is_recursive" = "false"
          # Non-recursive: only process direct children
          if test (dirname $item) = $current_dir
            set should_process true
          end
        else
          # Recursive: process all directories
          set should_process true
        end
      end

      if test "$should_process" = "true"
        set -l new_name (_transform_name $item_basename)

        # Rename item only if the new name is different
        if test "$item_basename" != "$new_name"
          set -l final_name $new_name
          set -l new_path $item_dir/$final_name

          # If target exists, find the first available sequential name
          if test -e $new_path
            set -l counter 1
            set -l base_part $new_name
            set -l ext_part ""

            # Separate extension if present
            if string match -q "*.*" -- $new_name
              set base_part (string replace -r '\.[^.]*$' '' $new_name)
              set ext_part (string match -r '\.[^.]*$' -- $new_name)
            end

            # Try sequential numbers until we find an available name
            while test -e $new_path
              set final_name "$base_part"_"$counter""$ext_part"
              set new_path $item_dir/$final_name
              set counter (math $counter + 1)

              # Safety check to prevent infinite loops
              if test $counter -gt 1000
                echo "Error: Too many conflicts for '$item', giving up after 1000 attempts"
                break
              end
            end
          end

          # Perform the rename if we found an available name
          if test ! -e $new_path
            mv "$item" "$new_path"
            if test "$final_name" != "$new_name"
              echo "Renamed: $item -> $new_path (conflict resolved)"
            else
              echo "Renamed: $item -> $new_path"
            end
          else
            echo "Error: Could not find available name for '$item'"
          end
        end
      end
    end
  end

  # Call the processing function
  _process_directory $dir $recursive $target_type
end