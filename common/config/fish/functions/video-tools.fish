function video-tools
    argparse 'h/help' 'n/no-confirm' -- $argv

    if set -q _flag_help
        echo "video-tools - Interactive video processing tool"
        echo ""
        echo "Interactive menu-driven tool for:"
        echo "  • Downscaling and compressing videos"
        echo "  • Trimming videos with start/end timestamps"
        echo "  • Splitting videos into chunks at specified timestamps"
        echo ""
        echo "Usage:"
        echo "  video-tools                    # Interactive mode (single file)"
        echo "  video-tools file1.mp4 file2.mp4  # Batch downscale multiple files"
        echo "  video-tools *.mp4              # Batch downscale with glob"
        echo "  video-tools (fd -e mp4)        # Batch downscale with command substitution"
        echo "  video-tools --help             # Show this help"
        echo ""
        echo "Options:"
        echo "  -n, --no-confirm               Skip confirmations (auto-save all chunks, auto-delete on low space)"
        echo ""
        echo "Examples:"
        echo "  video-tools                    # Interactive: choose downscale, trim, or split"
        echo "  video-tools *.mp4              # Batch downscale all MP4 files"
        echo "  video-tools --no-confirm (fd -Hi --no-ignore-vcs -S +5G)  # Batch downscale, auto-delete on low space"
        return 0
    end

    # Store no-confirm flag for use in subfunctions
    if set -q _flag_no_confirm
        set -g _video_tools_no_confirm 1
    else
        set -g _video_tools_no_confirm 0
    end

    # Batch mode: if files are provided as arguments
    if test (count $argv) -gt 0
        _video_tools_batch $argv
    else
        # Interactive mode: single file
        _video_tools_interactive
    end

    # Clean up global flag
    set -e _video_tools_no_confirm
end

function _video_tools_interactive
    # Main menu
    echo "Video Tools"
    echo "==========="
    echo ""
    echo "1) Downscale video"
    echo "2) Trim video"
    echo "3) Split video"
    echo "4) Exit"
    echo ""
    read -P "Select option (1-4): " choice

    switch $choice
        case 1
            _video_tools_downscale_single
        case 2
            _video_tools_trim_single
        case 3
            _video_tools_split_single
        case 4
            echo "Exiting..."
            return 0
        case '*'
            echo "Invalid choice. Exiting."
            return 1
    end
end

function _video_tools_batch
    set files $argv

    echo ""
    echo "=== Batch Downscale Mode ==="
    echo "Found "(count $files)" file(s)"
    echo ""

    _video_tools_downscale_batch $files
end

function _video_tools_downscale_single
    echo ""
    echo "=== Video Downscaling ==="
    echo ""

    # Get input file
    set input_file (_video_tools_read_file "Enter input video file (or press Enter to browse with fzf)")
    if test $status -ne 0
        return 1
    end

    set input (realpath "$input_file")

    # Get configuration
    set config (_video_tools_ask_downscale_config "$input")
    if test $status -ne 0
        return 1
    end

    # Parse config
    set target_res $config[1]
    set use_best $config[2]
    set mode $config[3]
    set output_path $config[4]

    # Process the file
    _video_tools_process_downscale "$input" $target_res $use_best $mode "$output_path"
end

function _video_tools_downscale_batch
    set files $argv

    echo ""
    echo "=== Batch Downscale Configuration ==="
    echo ""

    # Ask for target quality
    echo "Target quality options:"
    echo "  1) 2160p (4K)"
    echo "  2) 1440p (2K)"
    echo "  3) 1080p (Full HD)"
    echo "  4) 720p (HD)"
    echo "  5) Keep original (re-encode only)"
    echo ""
    read -P "Select target quality (1-5): " quality_choice

    switch $quality_choice
        case 1
            set target_res 2160
        case 2
            set target_res 1440
        case 3
            set target_res 1080
        case 4
            set target_res 720
        case 5
            set target_res 0
        case '*'
            echo "Invalid choice"
            return 1
    end

    # Ask for compression quality
    echo ""
    read -P "Use best compression? (slower, ~50% smaller, visually lossless) [y/N]: " best_choice
    if string match -qi "y*" -- $best_choice
        set use_best 1
    else
        set use_best 0
    end

    # Ask for output handling
    echo ""
    echo "Output options:"
    echo "  1) Overwrite originals (trash if space available, else delete with confirmation)"
    echo "  2) Save with _processed suffix"
    echo ""
    read -P "Select output option (1-2): " output_choice

    switch $output_choice
        case 1
            set mode force
        case 2
            set mode suffix
        case '*'
            echo "Invalid choice"
            return 1
    end

    # Process all files
    echo ""
    echo "Processing "(count $files)" file(s)..."
    echo ""

    for input_file in $files
        if not test -f "$input_file"
            echo "Skipping '$input_file' (not found)"
            echo ""
            continue
        end

        set input (realpath "$input_file")

        # Generate output path based on mode
        if test $mode = force
            set output_path (mktemp --suffix=.mp4)
        else
            set basename (basename "$input")
            set name (string replace -r '\.[^.]*$' '' $basename)
            set ext (string replace -r '^.*\.' '.' $basename)
            set dir (dirname "$input")
            set output_path "$dir/$name"_processed"$ext"
        end

        _video_tools_process_downscale "$input" $target_res $use_best $mode "$output_path"

        if test $status -eq 0
            echo ""
        end
    end

    echo "Batch processing complete!"
end

function _video_tools_trim_single
    echo ""
    echo "=== Video Trimming ==="
    echo ""

    # Get input file
    set input_file (_video_tools_read_file "Enter input video file (or press Enter to browse with fzf)")
    if test $status -ne 0
        return 1
    end

    set input (realpath "$input_file")

    # Show duration
    set duration (ffprobe -v error -show_entries format=duration -of csv=p=0 "$input" | string trim | head -n1)
    if test -z "$duration"
        echo "Error: Could not determine video duration"
        return 1
    end

    set duration_formatted (printf "%.0f" $duration | awk '{printf "%d:%02d:%02d", int($1/3600), int(($1%3600)/60), int($1%60)}')
    echo ""
    echo "Video duration: $duration_formatted"
    echo ""

    # Get timestamps and output
    set config (_video_tools_ask_trim_config)
    if test $status -ne 0
        return 1
    end

    set start_time $config[1]
    set end_time $config[2]

    # Get output file
    read -P "Enter output filename (or full path): " output_file
    if test -z "$output_file"
        echo "Error: No output file specified"
        return 1
    end

    # If it's just a filename (no directory separator), place in same dir as input
    if not string match -q "*/*" -- "$output_file"
        set input_dir (dirname "$input")
        set output "$input_dir/$output_file"
    else
        set output (realpath "$output_file")
    end

    # Process
    _video_tools_process_trim "$input" "$start_time" "$end_time" "$output"
end

function _video_tools_split_single
    echo ""
    echo "=== Video Splitting ==="
    echo ""

    # Get input file
    set input_file (_video_tools_read_file "Enter input video file (or press Enter to browse with fzf)")
    if test $status -ne 0
        return 1
    end

    set input (realpath "$input_file")

    # Get video duration
    set duration (ffprobe -v error -show_entries format=duration -of csv=p=0 "$input" | string trim | head -n1)
    if test -z "$duration"
        echo "Error: Could not determine video duration"
        return 1
    end

    set duration_formatted (printf "%.0f" $duration | awk '{printf "%d:%02d:%02d", int($1/3600), int(($1%3600)/60), int($1%60)}')
    echo ""
    echo "Video duration: $duration_formatted"
    echo ""
    echo "Timestamp format examples:"
    echo "  • 1:23:45 (1 hour, 23 minutes, 45 seconds)"
    echo "  • 5:30 (5 minutes, 30 seconds)"
    echo "  • 23:06.040 (23 minutes, 6.040 seconds)"
    echo "  • 90 (90 seconds)"
    echo "  • 90.5 (90.5 seconds)"
    echo ""
    echo "Enter split timestamps (space or comma separated):"
    echo "  Example: 1:30 5:00 10:30"
    echo ""
    read -P "Timestamps: " timestamps_input

    if test -z "$timestamps_input"
        echo "Error: No timestamps specified"
        return 1
    end

    # Parse timestamps (replace commas with spaces, then split)
    set timestamps_input (string replace -a ',' ' ' $timestamps_input)
    set timestamps (string split -n ' ' $timestamps_input)

    # Convert timestamps to seconds for sorting
    set -l timestamp_seconds
    for ts in $timestamps
        # Skip empty entries
        if test -z "$ts"
            continue
        end

        set seconds (_video_tools_timestamp_to_seconds $ts)
        if test $status -ne 0
            echo "Error: Invalid timestamp '$ts'"
            return 1
        end
        set -a timestamp_seconds $seconds
    end

    # Sort timestamps
    set sorted_seconds (printf '%s\n' $timestamp_seconds | sort -n)

    # Build chunk list: start to first, first to second, ..., last to end
    set -l chunk_starts
    set -l chunk_ends

    # First chunk: start to first timestamp
    set -a chunk_starts "0"
    set -a chunk_ends $sorted_seconds[1]

    # Middle chunks: timestamp i to timestamp i+1
    for i in (seq 1 (math (count $sorted_seconds) - 1))
        set -a chunk_starts $sorted_seconds[$i]
        set idx_next (math $i + 1)
        set -a chunk_ends $sorted_seconds[$idx_next]
    end

    # Last chunk: last timestamp to end
    set -a chunk_starts $sorted_seconds[-1]
    set -a chunk_ends ""

    # Extract base name and extension
    set basename (basename "$input")
    set name (string replace -r '\.[^.]*$' '' $basename)
    set ext (string replace -r '^.*(\.[^.]*)$' '$1' $basename)
    set dir (dirname "$input")

    echo ""
    echo "Will create "(count $chunk_starts)" chunk(s)"
    echo ""

    # First pass: show all chunks and get confirmation for each
    set -l chunks_to_save
    for i in (seq 1 (count $chunk_starts))
        set start $chunk_starts[$i]
        set end $chunk_ends[$i]

        # Format timestamps for display
        set start_fmt (_video_tools_seconds_to_timestamp $start)
        if test -n "$end"
            set end_fmt (_video_tools_seconds_to_timestamp $end)
            set chunk_desc "Chunk $i: $start_fmt to $end_fmt"
        else
            set chunk_desc "Chunk $i: $start_fmt to end"
        end

        echo "$chunk_desc"

        # Ask for confirmation unless --no-confirm
        if test $_video_tools_no_confirm -eq 1
            set -a chunks_to_save $i
            echo "  Will save (auto-confirmed)"
        else
            read -P "  Save this chunk? [Y/n]: " save_choice
            if test -z "$save_choice"; or string match -qi "y*" -- $save_choice
                set -a chunks_to_save $i
                echo "  Will save"
            else
                echo "  Will skip"
            end
        end
    end

    # Check if any chunks will be saved
    if test (count $chunks_to_save) -eq 0
        echo ""
        echo "No chunks selected. Exiting."
        return 0
    end

    # Ask about deleting original
    echo ""
    echo "Output options:"
    echo "  1) Delete original after split"
    echo "  2) Keep original intact"
    echo ""
    read -P "Select output option (1-2): " output_choice

    set should_delete_original 0
    switch $output_choice
        case 1
            set should_delete_original 1
        case 2
            set should_delete_original 0
        case '*'
            echo "Invalid choice, keeping original intact"
            set should_delete_original 0
    end

    # Second pass: process selected chunks
    echo ""
    echo "Processing "(count $chunks_to_save)" chunk(s)..."
    echo ""

    for i in $chunks_to_save
        set start $chunk_starts[$i]
        set end $chunk_ends[$i]

        # Format timestamps for display
        set start_fmt (_video_tools_seconds_to_timestamp $start)
        if test -n "$end"
            set end_fmt (_video_tools_seconds_to_timestamp $end)
        else
            set end_fmt "end"
        end

        echo "Processing chunk $i ($start_fmt to $end_fmt)..."

        set output "$dir/$name"_"$i$ext"
        _video_tools_process_trim "$input" "$start" "$end" "$output"
        if test $status -ne 0
            echo "  Warning: Failed to save chunk $i"
        end
        echo ""
    end

    # Handle original file deletion
    if test $should_delete_original -eq 1
        # Skip confirmation if --no-confirm is set
        if test $_video_tools_no_confirm -eq 1
            command rm "$input"
            echo "Original file deleted."
        else
            # Ask for final confirmation
            read -P "Really delete original file? [y/N]: " final_confirm
            if string match -qi "y*" -- $final_confirm
                command rm "$input"
                echo "Original file deleted."
            else
                echo "Original file kept."
            end
        end
    end

    echo "Splitting complete!"
end

function _video_tools_timestamp_to_seconds
    set ts $argv[1]

    # Handle HH:MM:SS, MM:SS, or seconds (with optional decimal parts)
    set parts (string split ':' $ts)
    set count (count $parts)

    # Strip leading zeros from each part to avoid octal interpretation, preserving decimals
    for i in (seq 1 (count $parts))
        if string match -qr '\.' -- $parts[$i]
            # Contains decimal point - strip leading zeros but keep '0' before decimal if needed
            set parts[$i] (string replace -r '^0+([1-9]|0?\.)' '$1' $parts[$i])
            # Ensure we have a leading zero before decimal point
            if string match -qr '^\.' -- $parts[$i]
                set parts[$i] "0$parts[$i]"
            end
        else
            # No decimal - strip leading zeros normally
            set parts[$i] (string replace -r '^0+' '' $parts[$i])
            # If empty (was all zeros), set to 0
            test -z "$parts[$i]"; and set parts[$i] 0
        end
    end

    if test $count -eq 1
        # Just seconds
        echo $parts[1]
    else if test $count -eq 2
        # MM:SS
        set seconds (math "$parts[1] * 60 + $parts[2]")
        echo $seconds
    else if test $count -eq 3
        # HH:MM:SS
        set seconds (math "$parts[1] * 3600 + $parts[2] * 60 + $parts[3]")
        echo $seconds
    else
        return 1
    end
end

function _video_tools_seconds_to_timestamp
    set total_seconds $argv[1]

    set hours (math "floor($total_seconds / 3600)")
    set remaining (math "$total_seconds % 3600")
    set minutes (math "floor($remaining / 60)")
    set seconds (math "$remaining % 60")

    if test $hours -gt 0
        printf "%d:%02d:%02d" $hours $minutes $seconds
    else
        printf "%d:%02d" $minutes $seconds
    end
end

function _video_tools_read_file
    set prompt $argv[1]

    read -P "$prompt: " -S input_file

    # If empty, launch fzf
    if test -z "$input_file"
        set input_file (fd -Hi --no-ignore-vcs --follow . | \
                        fzf --height 40% --reverse --border --prompt "Select video file: " \
                            --preview 'ffprobe -v error -show_entries format=duration,format=size,stream=width,height,codec_name -of default=noprint_wrappers=1 {} 2>/dev/null | head -20' \
                            --preview-window=right:50%:wrap)

        if test -z "$input_file"
            echo "Error: No file selected"
            return 1
        end
    end

    # Validate file exists
    if not test -f "$input_file"
        echo "Error: File '$input_file' not found"
        return 1
    end

    echo "$input_file"
end

function _video_tools_ask_downscale_config
    set input $argv[1]

    # Get video dimensions
    set width (ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$input" | string trim | head -n1)
    set height (ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$input" | string trim | head -n1)

    if test -z "$width" -o -z "$height"
        echo "Error: Could not determine video dimensions"
        return 1
    end

    # Determine short dimension
    if test $width -lt $height
        set short_dim $width
    else
        set short_dim $height
    end

    echo ""
    echo "Current resolution: $width x $height (short side: $short_dim px)"
    echo ""

    # Ask for target quality
    echo "Target quality options:"
    echo "  1) 2160p (4K)"
    echo "  2) 1440p (2K)"
    echo "  3) 1080p (Full HD)"
    echo "  4) 720p (HD)"
    echo "  5) Keep original (re-encode only)"
    echo ""
    read -P "Select target quality (1-5): " quality_choice

    switch $quality_choice
        case 1
            set target_res 2160
        case 2
            set target_res 1440
        case 3
            set target_res 1080
        case 4
            set target_res 720
        case 5
            set target_res 0
        case '*'
            echo "Invalid choice"
            return 1
    end

    # Ask for compression quality
    echo ""
    read -P "Use best compression? (slower, ~50% smaller, visually lossless) [y/N]: " best_choice
    if string match -qi "y*" -- $best_choice
        set use_best 1
    else
        set use_best 0
    end

    # Ask for output handling
    echo ""
    echo "Output options:"
    echo "  1) Overwrite original (trash if space available, else delete with confirmation)"
    echo "  2) Save as new file"
    echo ""
    read -P "Select output option (1-2): " output_choice

    switch $output_choice
        case 1
            set output_path (mktemp --suffix=.mp4)
            set mode force
        case 2
            read -P "Enter output filename (or full path): " output_file
            if test -z "$output_file"
                echo "Error: No output file specified"
                return 1
            end
            # If it's just a filename (no directory separator), place in same dir as input
            if not string match -q "*/*" -- "$output_file"
                set input_dir (dirname "$input")
                set output_path "$input_dir/$output_file"
            else
                set output_path (realpath "$output_file")
            end
            set mode save
        case '*'
            echo "Invalid choice"
            return 1
    end

    # Return config as space-separated values
    echo $target_res $use_best $mode "$output_path"
end

function _video_tools_ask_trim_config
    echo "Timestamp format examples:"
    echo "  • 1:23:45 (1 hour, 23 minutes, 45 seconds)"
    echo "  • 5:30 (5 minutes, 30 seconds)"
    echo "  • 23:06.040 (23 minutes, 6.040 seconds)"
    echo "  • 90 (90 seconds)"
    echo "  • 90.5 (90.5 seconds)"
    echo ""

    # Get start timestamp
    read -P "Enter start timestamp (or press Enter for beginning): " start_time
    if test -z "$start_time"
        set start_time "0"
    end

    # Get end timestamp
    read -P "Enter end timestamp (or press Enter for end): " end_time

    # Return config
    echo "$start_time" "$end_time"
end

function _video_tools_process_downscale
    set input $argv[1]
    set target_res $argv[2]
    set use_best $argv[3]
    set mode $argv[4]
    set output $argv[5]

    # Get video dimensions
    set width (ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$input" | string trim | head -n1)
    set height (ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$input" | string trim | head -n1)

    if test -z "$width" -o -z "$height"
        echo "Processing: $input"
        echo "Error: Could not determine video dimensions"
        return 1
    end

    # Determine short dimension and orientation
    if test $width -lt $height
        set short_dim $width
        set is_vertical 1
    else
        set short_dim $height
        set is_vertical 0
    end

    # Determine if scaling is needed
    if test $target_res -eq 0
        # Keep original resolution
        set needs_scaling 0
        set actual_target $short_dim
    else if test $short_dim -le $target_res
        set needs_scaling 0
        set actual_target $short_dim
        echo "Processing: $input"
        echo "Video $width"x"$height already at or below target ($target_res"p"), re-encoding only"
    else
        set needs_scaling 1
        set actual_target $target_res
    end

    # Get duration and size
    set duration (ffprobe -v error -show_entries format=duration -of csv=p=0 "$input" | string trim | head -n1)
    set duration_formatted (printf "%.0f" $duration | awk '{printf "%d:%02d:%02d", int($1/3600), int(($1%3600)/60), int($1%60)}')
    set input_size (stat -c %s "$input" | numfmt --to=iec-i --suffix=B)

    echo "Processing: $input"
    echo "Input: $width"x"$height, $input_size, $duration_formatted"

    # Determine scale filter
    if test $needs_scaling -eq 1
        if test $is_vertical -eq 1
            set scale_filter_vaapi "scale_vaapi=$actual_target:-2:format=nv12"
            set scale_filter_cpu "scale=$actual_target:-2"
        else
            set scale_filter_vaapi "scale_vaapi=-2:$actual_target:format=nv12"
            set scale_filter_cpu "scale=-2:$actual_target"
        end
    end

    # Execute encoding
    if test $use_best -eq 1
        # CPU encoding with best quality
        if test $needs_scaling -eq 1
            ffmpeg -loglevel error -stats -y -i "$input" -vf "$scale_filter_cpu" \
                      -c:v libx264 -preset slow -crf 20 -profile:v high -level 4.1 \
                      -c:a copy "$output"
            set ffmpeg_success $status
        else
            ffmpeg -loglevel error -stats -y -i "$input" \
                      -c:v libx264 -preset slow -crf 20 -profile:v high -level 4.1 \
                      -c:a copy "$output"
            set ffmpeg_success $status
        end
    else
        # Hardware accelerated encoding
        if test $needs_scaling -eq 1
            ffmpeg -loglevel error -stats -y -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -hwaccel_output_format vaapi -i "$input" \
                      -vf "$scale_filter_vaapi" -c:v h264_vaapi -qp 23 -c:a copy "$output"
            set ffmpeg_success $status
            if test $ffmpeg_success -ne 0
                echo "Hardware acceleration failed, falling back to CPU..."
                ffmpeg -loglevel error -stats -y -i "$input" -vf "$scale_filter_cpu" -c:v libx264 -preset ultrafast -crf 23 -threads 0 -c:a copy "$output"
                set ffmpeg_success $status
            end
        else
            # Re-encode only without scaling
            ffmpeg -loglevel error -stats -y -i "$input" \
                      -c:v libx264 -preset ultrafast -crf 23 -threads 0 -c:a copy "$output"
            set ffmpeg_success $status
        end
    end

    # Handle output
    if test $ffmpeg_success -eq 0
        set output_size_bytes (stat -c %s "$output")
        set output_size (echo $output_size_bytes | numfmt --to=iec-i --suffix=B)
        echo "Output: $output_size"

        if test $mode = force
            # Check if there's enough space to keep both files (for trash)
            set filesystem (df --output=target "$input" | tail -n1)
            set available_bytes (df --output=avail "$input" | tail -n1 | string trim)

            # Add 100MB buffer for safety (in bytes)
            set required_bytes (math $output_size_bytes + 104857600)

            if test $available_bytes -ge $required_bytes
                # Enough space, use trash for safety
                trash-put "$input"
                mv "$output" "$input"
                echo "Success! Original moved to trash."
            else
                # Not enough space, need to delete
                set available_human (echo $available_bytes | numfmt --to=iec-i --suffix=B)
                echo ""
                echo "Warning: Only $available_human available on filesystem"
                echo "Not enough space to keep original in trash."

                # Check if no-confirm flag is set
                if test $_video_tools_no_confirm -eq 1
                    command rm "$input"
                    mv "$output" "$input"
                    echo "Success! Original deleted (auto-confirmed)."
                else
                    read -P "Permanently delete original? [y/N]: " confirm

                    if string match -qi "y*" -- $confirm
                        command rm "$input"
                        mv "$output" "$input"
                        echo "Success! Original deleted."
                    else
                        echo "Cancelled. Keeping temporary file: $output"
                        return 1
                    end
                end
            end
        else if test $mode = suffix
            echo "Saved to: $output"
        else
            echo "Saved to: $output"
        end
    else
        echo "Error: Processing failed"
        if test $mode = force
            command rm -f "$output"
        end
        return 1
    end
end

function _video_tools_process_trim
    set input $argv[1]
    set start_time $argv[2]
    set end_time $argv[3]
    set output $argv[4]

    echo "Processing: $input"

    # Build ffmpeg command
    set ffmpeg_cmd ffmpeg -loglevel error -stats -y

    # Add start time if specified
    if test "$start_time" != "0"
        set ffmpeg_cmd $ffmpeg_cmd -ss $start_time
    end

    set ffmpeg_cmd $ffmpeg_cmd -i "$input"

    # Add end time if specified
    if test -n "$end_time"
        set ffmpeg_cmd $ffmpeg_cmd -to $end_time
    end

    # Copy streams without re-encoding for speed
    set ffmpeg_cmd $ffmpeg_cmd -c copy "$output"

    # Execute
    eval $ffmpeg_cmd
    set ffmpeg_success $status

    if test $ffmpeg_success -eq 0
        set output_size (stat -c %s "$output" | numfmt --to=iec-i --suffix=B)
        set output_duration (ffprobe -v error -show_entries format=duration -of csv=p=0 "$output" | string trim | head -n1)
        set output_duration_formatted (printf "%.0f" $output_duration | awk '{printf "%d:%02d:%02d", int($1/3600), int(($1%3600)/60), int($1%60)}')

        echo "Success! Saved to: $output"
        echo "Output: $output_size, $output_duration_formatted"
    else
        echo "Error: Trimming failed"
        return 1
    end
end
