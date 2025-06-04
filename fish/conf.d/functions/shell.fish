# Snake case all files in a dir
function snake_case_all
  # Check if a directory argument is provided
  if test -z "$argv[1]"
    echo "Usage: snake_case_all <directory>"
    echo "Renames all files in the specified directory by:"
    echo "- Removing content inside and including square brackets"
    echo "- Removing apostrophes only if surrounded by letters"
    echo "- Removing opening and closing parentheses"
    echo "- Trimming leading and trailing spaces"
    echo "- Converting names to lowercase and replacing spaces with underscores"
    echo "- Removing leading and trailing underscores"
    return 1
  end

  set -l dir $argv[1]

  # Check if the argument is a valid directory
  if test ! -d $dir
    echo "Error: '$dir' is not a valid directory."
    return 1
  end

  # Process each file in the specified directory
  for file in $dir/*
    if test -f $file
      # Extract filename without path
      set filename (basename $file)

      # Separate base name and extension
      set extension ""
      if string match -q "*.*" $filename
        set base_name (string replace -r '\.[^.]*$' '' $filename)  # Everything before the last dot
        set extension (string match -r '\.[^.]*$' $filename) # Everything after the last dot (including the dot)
      else
        set base_name $filename  # No extension case
      end

      # Remove content inside square brackets (including brackets)
      set base_name (string replace -a -r '\[.*?\]' '' $base_name)

      # Remove opening and closing parentheses
      set base_name (string replace -a '(' '' $base_name)
      set base_name (string replace -a ')' '' $base_name)

      # Trim leading/trailing spaces
      set base_name (string trim $base_name)

      # Remove apostrophes
      set base_name (string replace -a "'" '' $base_name)

      # Convert to lowercase and replace spaces and other separators with underscores
      set base_name (echo $base_name | tr '[:upper:]' '[:lower:]' | tr -s ' _' '_')

      # Remove **all** leading and trailing underscores
      set base_name (echo $base_name | sed 's/^_*\|_*$//g')

      # Rename file only if the new name is different
      if test "$filename" != "$base_name$extension"
        mv -i $file $dir/$base_name$extension
      end
    end
  end
end

function empty_file
  if test -z "$argv[1]"
    echo "Usage: empty_file /path/to/file"
    return 1
  end

  if test -f $argv[1]
    : > $argv[1]
    echo "Emptied: $argv[1]"
  else
    echo "File does not exist: $argv[1]"
    return 1
  end
end
