#!/usr/bin/env bash
file="$1"
width="${2:-$((COLUMNS/2))}"
height="${3:-$((LINES/2))}"

if [[ -d "$file" ]]; then
    eza --all --oneline --icons=always --color=always --group-directories-first "$file"
elif file --mime-type "$file" | grep -q image/; then
    chafa --format symbols --size "${width}x${height}" --dither diffusion --dither-intensity 1.0 "$file"
elif file --mime-type "$file" | grep -q video/; then
    {
        thumb_file=$(mktemp --suffix=.jpg)
        ffmpegthumbnailer -i "$file" -o "$thumb_file" -s 0 2>/dev/null
        chafa --format symbols --size "${width}x$((height/2))" --dither diffusion --dither-intensity 1.0 "$thumb_file"
        rm -f "$thumb_file"
        echo -e "\n=== Video Info ===\n"
        mediainfo --Inform="General;File: %FileName%.%FileExtension%\nSize: %FileSize/String%\nDuration: %Duration/String%\nFrame Rate: %FrameRate% fps" "$file"
        mediainfo --Inform="Video;Resolution: %Width%x%Height%" "$file"
    }
else
    bat --style=numbers --color=always --line-range :500 "$file" || cat "$file"
fi
