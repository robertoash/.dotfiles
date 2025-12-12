#!/usr/bin/env bash
file="$1"

# Get width and height from fzf environment variables or fallback to terminal size
width="${FZF_PREVIEW_COLUMNS:-${COLUMNS:-80}}"
height="${FZF_PREVIEW_LINES:-${LINES:-40}}"

# Max dimensions to prevent oversized images
MAX_WIDTH=120
MAX_HEIGHT=50

# Skip labels like yazi does
skip_label() {
    local line="$1"
    case "$line" in
        "Complete name"*|"CompleteName_Last"*|"Unique ID"*|"File size"*|"Format/Info"*|"Codec ID/Info"*|"MD5 of the unencoded content"*) return 0 ;;
        *) return 1 ;;
    esac
}

# Count mediainfo lines to reserve space
count_mediainfo_lines() {
    local file="$1"
    local count=0
    while IFS= read -r line; do
        if [[ "$line" =~ ^([^:]+)\ *:\ *(.+)$ ]]; then
            local label="${BASH_REMATCH[1]}"
            if ! skip_label "$label"; then
                ((count++))
            fi
        elif [[ "$line" != "General" && -n "$line" ]]; then
            ((count++))
        fi
    done < <(mediainfo "$file" 2>/dev/null)
    echo "$count"
}

# Function to show image with best available method
show_image() {
    local img="$1"
    local w="$2"
    local h="$3"

    # Apply max constraints
    w=$((w > MAX_WIDTH ? MAX_WIDTH : w))
    h=$((h > MAX_HEIGHT ? MAX_HEIGHT : h))

    chafa --size "${w}x${h}" "$img"
}

if [[ -d "$file" ]]; then
    eza --all --oneline --icons=always --color=always --group-directories-first "$file"
elif file --mime-type "$file" | grep -q image/; then
    # Limit image to max 60% of height to ensure metadata space
    img_height=$((height * 60 / 100))
    img_height=$((img_height > MAX_HEIGHT ? MAX_HEIGHT : img_height))

    show_image "$file" "$width" "$img_height"

    # Collect and format mediainfo output
    while IFS= read -r line; do
        if [[ "$line" =~ ^([^:]+)\ *:\ *(.+)$ ]]; then
            label="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            if ! skip_label "$label"; then
                printf "\e[1m%s:\e[0m \e[34m%s\e[0m\n" "$label" "$value"
            fi
        elif [[ "$line" != "General" && -n "$line" ]]; then
            printf "\e[32m%s\e[0m\n" "$line"
        fi
    done < <(mediainfo "$file" 2>/dev/null)
elif file --mime-type "$file" | grep -q -E 'video/|audio/'; then
    is_video=false
    file --mime-type "$file" | grep -q video/ && is_video=true

    # Limit thumbnail to max 50% of height for videos
    img_height=$((height * 50 / 100))
    img_height=$((img_height > MAX_HEIGHT ? MAX_HEIGHT : img_height))

    # Show thumbnail for videos
    if $is_video; then
        thumb_file=$(mktemp --suffix=.jpg)
        ffmpegthumbnailer -i "$file" -o "$thumb_file" -s 0 2>/dev/null && {
            show_image "$thumb_file" "$width" "$img_height"
        }
        rm -f "$thumb_file"
    fi

    # Full mediainfo output with formatting
    while IFS= read -r line; do
        if [[ "$line" =~ ^([^:]+)\ *:\ *(.+)$ ]]; then
            label="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            if ! skip_label "$label"; then
                printf "\e[1m%s:\e[0m \e[34m%s\e[0m\n" "$label" "$value"
            fi
        elif [[ "$line" != "General" && -n "$line" ]]; then
            printf "\e[32m%s\e[0m\n" "$line"
        fi
    done < <(mediainfo "$file" 2>/dev/null)
else
    bat --style=numbers --color=always --line-range :500 "$file" || cat "$file"
fi
