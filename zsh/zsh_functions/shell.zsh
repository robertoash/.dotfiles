# Search for files only
fff() {
    local exclude_file="$HOME/.config/fd/.fdignore"
    local excludes=()

    if [[ -f "$exclude_file" ]]; then
        while IFS= read -r pattern || [[ -n "$pattern" ]]; do
            [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
            excludes+=(--exclude "$pattern")
        done < "$exclude_file"
    fi

    local search_pattern=""
    local search_path="$HOME"  # Default search path

    # Handle help flag
    if [[ "$1" == "--help" ]]; then
        echo "Usage: fff [search_pattern] [search_path]"
        echo "Searches for files interactively using fzf."
        return
    fi

    # Handle arguments (any order)
    for arg in "$@"; do
        if [[ -d "$arg" ]]; then
            search_path="$arg"
        else
            search_pattern="$arg"
        fi
    done

    local selection
    selection=$(fd -H --type f --follow "${excludes[@]}" "$search_pattern" "$search_path" 2>/dev/null | \
        fzf --height 40% --reverse --preview 'bat --style=numbers --color=always {} || cat {}')

    if [[ -z "$selection" ]]; then
        echo "No file selected." >&2
        return 1
    fi

    xdg-open "$selection" || {
        echo "Failed to open $selection" >&2
        return 1
    }
}

# Search for directories only
ffd() {
    local exclude_file="$HOME/.config/fd/.fdignore"
    local excludes=()

    if [[ -f "$exclude_file" ]]; then
        while IFS= read -r pattern || [[ -n "$pattern" ]]; do
            [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
            excludes+=(--exclude "$pattern")
        done < "$exclude_file"
    fi

    local search_pattern=""
    local search_path="$HOME"  # Default search path

    # Handle help flag
    if [[ "$1" == "--help" ]]; then
        echo "Usage: ffd [search_pattern] [search_path]"
        echo "Searches for directories interactively using fzf."
        return
    fi

    # Handle arguments (any order)
    for arg in "$@"; do
        if [[ -d "$arg" ]]; then
            search_path="$arg"
        else
            search_pattern="$arg"
        fi
    done

    local selection
    selection=$(fd -H --type d --follow "${excludes[@]}" "$search_pattern" "$search_path" 2>/dev/null | \
        fzf --height 40% --reverse --preview 'eza -1 --color=always {}')

    if [[ -z "$selection" ]]; then
        echo "No directory selected." >&2
        return 1
    fi

    cd "$selection" || {
        echo "Failed to change directory to $selection" >&2
        return 1
    }
}

# Snake case all files in a dir
snake_case_all() {
  # Check if a directory argument is provided
  if [[ -z "$1" ]]; then
    echo "Usage: snake_case_all <directory>"
    echo "Renames all files in the specified directory by:"
    echo "- Removing content inside and including square brackets"
    echo "- Removing apostrophes only if surrounded by letters"
    echo "- Removing opening and closing parentheses"
    echo "- Trimming leading and trailing spaces"
    echo "- Converting names to lowercase and replacing spaces with underscores"
    echo "- Removing leading and trailing underscores"
    return 1
  fi

  local dir="$1"

  # Check if the argument is a valid directory
  if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' is not a valid directory."
    return 1
  fi

  # Process each file in the specified directory
  for file in "$dir"/*; do
    if [[ -f "$file" ]]; then
      # Extract filename without path
      filename="${file##*/}"

      # Separate base name and extension
      extension=""
      if [[ "$filename" == *.* ]]; then
        base_name="${filename%.*}"  # Everything before the last dot
        extension=".${filename##*.}" # Everything after the last dot (including the dot)
      else
        base_name="$filename"  # No extension case
      fi

      # Remove content inside square brackets (including brackets)
      base_name="${base_name//\[*\]/}"

      # Remove opening and closing parentheses
      base_name="${base_name//[\(\)]/}"

      # Trim leading/trailing spaces
      base_name="${base_name#"${base_name%%[![:space:]]*}"}"
      base_name="${base_name%"${base_name##*[![:space:]]}"}"

      # Remove apostrophes only if surrounded by letters
      base_name=$(echo "$base_name" | tr -d "'")


      # Convert to lowercase and replace spaces and other separators with underscores
      base_name=$(echo "$base_name" | tr '[:upper:]' '[:lower:]' | tr -s ' _' '_')

      # Remove **all** leading and trailing underscores
      base_name=$(echo "$base_name" | sed 's/^_*\|_*$//g')

      # Rename file only if the new name is different
      if [[ "$filename" != "$base_name$extension" ]]; then
        mv -i "$file" "$dir/$base_name$extension"
      fi
    fi
  done
}

empty_file() {
  if [[ -z "$1" ]]; then
    echo "Usage: empty_file /path/to/file"
    return 1
  fi

  if [[ -f "$1" ]]; then
    : > "$1"
    echo "Emptied: $1"
  else
    echo "File does not exist: $1"
    return 1
  fi
}
