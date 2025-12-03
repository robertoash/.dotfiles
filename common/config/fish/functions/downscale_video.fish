function downscale_video
    argparse 'h/help' 'f/force' 't/target-quality=' 'o/output-dir=' 's/steps=' 'r/recursive' 'b/best' -- $argv

    if set -q _flag_help
        echo "downscale_video - Downscale and compress video files"
        echo ""
        echo "Options:"
        echo "  -t, --target-quality      Quality: 2160/1440/1080/720 (default: 1440, refers to short side)"
        echo "  -s, --steps N             Go down N quality steps (e.g., 4K->1080 is 2 steps)"
        echo "  -b, --best                Optimal compression: slower, ~50% smaller, visually lossless"
        echo "  -f, --force               Overwrite input file (original moved to trash)"
        echo "  -r, --recursive DIR       Process all videos in directory recursively"
        echo "  -o, --output-dir DIR      Save multiple files to directory (appends _down)"
        echo ""
        echo "Examples:"
        echo "  downscale_video -t 1080 --best -f video.mp4       # Downscale to 1080p, best compression"
        echo "  downscale_video --best -f video.mp4               # Re-encode only (no downscale), 50% smaller"
        echo "  downscale_video --steps 1 -f (fd -S +4g)          # Reduce all large videos by 1 step"
        echo "  downscale_video -r --best ~/Videos                # Recursively optimize all videos"
        echo ""
        echo "Notes:"
        echo "  - Uses VAAPI hardware acceleration by default (fast), --best uses CPU (slower, smaller)"
        echo "  - Skips videos already at/below target quality"
        echo "  - Works with both horizontal and vertical videos"
        return 0
    end
    
    if test (count $argv) -eq 0
        echo "Usage: downscale_video [OPTIONS] <input> [output]"
        echo ""
        echo "Common patterns:"
        echo "  downscale_video -t 1080 --best -f video.mp4    # Downscale + best compression"
        echo "  downscale_video --best -f video.mp4            # Re-encode for smaller size"
        echo "  downscale_video -r --best ~/Videos             # Recursively optimize all"
        echo ""
        echo "Run 'downscale_video --help' for all options"
        return 1
    end

    # Handle recursive mode
    if set -q _flag_recursive
        if test (count $argv) -ne 1
            echo "Error: -r/--recursive requires exactly one directory argument"
            return 1
        end
        if not test -d $argv[1]
            echo "Error: '$argv[1]' is not a directory"
            return 1
        end

        set video_dir (realpath "$argv[1]")
        echo "Searching for video files in $video_dir recursively..."

        # Find all video files recursively
        set video_files (fd -t f -e mp4 -e mkv -e avi -e mov -e webm -e flv -e wmv -e m4v . "$video_dir")

        if test (count $video_files) -eq 0
            echo "No video files found in $video_dir"
            return 0
        end

        echo "Found "(count $video_files)" video file(s)"
        echo ""

        # Set force mode for recursive processing
        set _flag_force 1
        set argv $video_files
    end
    
    # Check for conflicting options
    if set -q _flag_target_quality; and set -q _flag_steps
        echo "Error: cannot use both -t/--target-quality and -s/--steps together"
        return 1
    end

    # Check if using best compression settings
    if set -q _flag_best
        set use_best 1
    else
        set use_best 0
    end

    # Define quality levels (height in pixels)
    set quality_levels 2160 1440 1080 720

    # Validate target resolution or set default
    if set -q _flag_target_quality
        set target_res $_flag_target_quality
        if not contains $target_res 2160 1440 1080 720
            echo "Error: target quality must be 2160, 1440, 1080, or 720"
            return 1
        end
        set use_steps 0
        set has_explicit_target 1
    else if set -q _flag_steps
        # Steps will be calculated per-video based on current height
        set steps_down $_flag_steps
        if not string match -qr '^[0-9]+$' $steps_down
            echo "Error: --steps must be a positive number"
            return 1
        end
        set use_steps 1
        set has_explicit_target 1
    else
        # No explicit target - use 1440 as default, but allow --best to skip downscaling
        set target_res 1440
        set use_steps 0
        set has_explicit_target 0
    end
    
    # Handle different modes: force, output-dir (multiple inputs), or single input/output
    if set -q _flag_force
        if test (count $argv) -lt 1
            echo "Error: -f/--force flag requires at least one input file"
            return 1
        end
        if set -q _flag_output_dir
            echo "Error: -f/--force and -o/--output-dir cannot be used together"
            return 1
        end
        set inputs $argv
        set mode force
    else if set -q _flag_output_dir
        if test (count $argv) -lt 1
            echo "Error: -o/--output-dir requires at least one input file"
            return 1
        end
        if not test -d $_flag_output_dir
            echo "Error: Output directory '$_flag_output_dir' does not exist"
            return 1
        end
        set inputs $argv
        set output_dir (realpath "$_flag_output_dir")
        set mode multiple
    else
        if test (count $argv) -eq 1
            echo "Error: Output file required when not using -f/--force or -o/--output-dir"
            return 1
        else if test (count $argv) -eq 2
            set inputs $argv[1]
            set single_output $argv[2]
            set mode single
        else
            echo "Error: Multiple inputs require -o/--output-dir flag"
            return 1
        end
    end
    
    # Process each input file
    for input_file in $inputs
        set input (realpath "$input_file")
        
        # Determine output path based on mode
        if test $mode = force
            set output (mktemp --suffix=.mp4)
        else if test $mode = multiple
            set basename (basename "$input")
            set name (string replace -r '\.[^.]*$' '' $basename)
            set ext (string replace -r '^.*\.' '.' $basename)
            set output "$output_dir/$name"_down"$ext"
        else # single mode
            set output $single_output
        end
        
        # Get both width and height to handle vertical videos correctly
        set width (ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$input" | string trim | head -n1)
        set height (ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$input" | string trim | head -n1)

        # Validate that we got valid dimensions
        if test -z "$width" -o -z "$height"
            echo "Processing: $input"
            echo "Error: Could not determine video dimensions. File may be corrupt or not a valid video."
            if test (count $inputs) -gt 1
                echo ""
            end
            continue
        end

        # Use the shorter dimension (quality levels refer to the short side)
        if test $width -lt $height
            set short_dim $width
        else
            set short_dim $height
        end
        set is_vertical (test $height -gt $width; and echo 1; or echo 0)

        # Calculate target resolution based on steps if needed
        if test $use_steps -eq 1
            # Find current position in quality levels
            set current_idx 0
            for i in (seq 1 (count $quality_levels))
                if test $short_dim -ge $quality_levels[$i]
                    set current_idx $i
                    break
                end
            end

            # If video is smaller than 720p, skip it
            if test $current_idx -eq 0
                echo "Processing: $input"
                echo "Video resolution is $width"x"$height pixels (smaller than 720p), skipping"
                if test (count $inputs) -gt 1
                    echo ""
                end
                continue
            end

            # Calculate target index (go down N steps)
            set target_idx (math $current_idx + $steps_down)

            # Cap at 720p (last element)
            if test $target_idx -gt (count $quality_levels)
                set target_idx (count $quality_levels)
            end

            set target_res $quality_levels[$target_idx]

            # If we're already at or below target, skip
            if test $short_dim -le $target_res
                echo "Processing: $input"
                echo "Video resolution is $width"x"$height pixels (already at or below target after $steps_down steps), skipping"
                if test (count $inputs) -gt 1
                    echo ""
                end
                continue
            end
        end

        # Process if we need to downscale OR if --best is set (re-encode at same resolution)
        set needs_processing 0
        if test $short_dim -gt $target_res -a $has_explicit_target -eq 1
            set needs_processing 1
            set needs_scaling 1
        else if test $use_best -eq 1
            set needs_processing 1
            set needs_scaling 0
        end

        if test $needs_processing -eq 1
            set duration (ffprobe -v error -show_entries format=duration -of csv=p=0 "$input" | string trim | head -n1)
            set duration_formatted (printf "%.0f" $duration | awk '{printf "%d:%02d:%02d", int($1/3600), int(($1%3600)/60), int($1%60)}')
            echo "Processing: $input"

            # Only check codec/bitrate when re-encoding without scaling (--best without downscaling)
            if test $needs_scaling -eq 0
                # Check codec - skip if already using efficient codec
                set source_codec (ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$input" | string trim | head -n1)
                if string match -qi "*hevc*" $source_codec; or string match -qi "*h265*" $source_codec; or string match -qi "*av1*" $source_codec
                    echo "Video uses efficient codec ($source_codec), re-encoding to H.264 would increase file size. Skipping."
                    if test (count $inputs) -gt 1
                        echo ""
                    end
                    continue
                end

                # Check bitrate and estimate potential savings
                set source_bitrate (ffprobe -v error -show_entries format=bit_rate -of csv=p=0 "$input" | string trim | head -n1)
                if test -n "$source_bitrate"
                    # Calculate expected bitrate for CRF 20 (~0.15 bits per pixel per frame at 30fps)
                    # CRF 20 is "visually lossless" quality, needs higher bitrate than moderate quality
                    set total_pixels (math $width \* $height)
                    set expected_bitrate (math $total_pixels \* 0.15 \* 30)

                    # If already H.264 at or below expected bitrate, skip
                    if string match -q "h264" $source_codec
                        if test "$source_bitrate" -le "$expected_bitrate"
                            set bitrate_mbps (printf "%.2f" (math $source_bitrate / 1000000))
                            set expected_mbps (printf "%.2f" (math $expected_bitrate / 1000000))
                            echo "Video already well-compressed H.264 ($bitrate_mbps Mbps vs $expected_mbps Mbps expected for CRF 20). Skipping."
                            if test (count $inputs) -gt 1
                                echo ""
                            end
                            continue
                        end
                    end

                    # Check if expected savings would be at least 20%
                    if test "$source_bitrate" -gt "$expected_bitrate"
                        set expected_savings_pct (math "round(($source_bitrate - $expected_bitrate) / $source_bitrate * 100)")
                        if test $expected_savings_pct -lt 20
                            set bitrate_mbps (printf "%.2f" (math $source_bitrate / 1000000))
                            set expected_mbps (printf "%.2f" (math $expected_bitrate / 1000000))
                            echo "Re-encoding would only save ~$expected_savings_pct% ($bitrate_mbps → $expected_mbps Mbps). Skipping (minimum 20% required)."
                            if test (count $inputs) -gt 1
                                echo ""
                            end
                            continue
                        end
                    end

                    # Fallback: skip if bitrate is very low regardless of codec
                    if test "$source_bitrate" -lt 3000000
                        set bitrate_mbps (printf "%.2f" (math $source_bitrate / 1000000))
                        echo "Video already efficiently compressed (bitrate: $bitrate_mbps Mbps). Skipping."
                        if test (count $inputs) -gt 1
                            echo ""
                        end
                        continue
                    end
                end
            end

            # Determine scale filter based on orientation (only if scaling)
            if test $needs_scaling -eq 1
                if test $is_vertical -eq 1
                    set scale_filter_vaapi "scale_vaapi=$target_res:-2:format=nv12"
                    set scale_filter_cpu "scale=$target_res:-2"
                    echo "Downscaling vertical video from $width"x"$height to $target_res"x"? (Duration: $duration_formatted)..."
                else
                    set scale_filter_vaapi "scale_vaapi=-2:$target_res:format=nv12"
                    set scale_filter_cpu "scale=-2:$target_res"
                    echo "Downscaling horizontal video from $width"x"$height to ?"x"$target_res (Duration: $duration_formatted)..."
                end
            else
                # No scaling, just re-encoding
                echo "Re-encoding $width"x"$height video for optimal compression (Duration: $duration_formatted)..."
            end

            set input_size (stat -c %s "$input" | numfmt --to=iec-i --suffix=B)
            echo "Input file size: $input_size"

            # Show expected compression results if we have bitrate info
            if test -n "$source_bitrate"
                set current_bitrate_mbps (printf "%.2f" (math $source_bitrate / 1000000))

                # Calculate expected output bitrate and size
                if test $needs_scaling -eq 1
                    # When downscaling, estimate based on new resolution
                    set new_pixels (math $target_res \* $target_res \* 16 / 9)  # Approximate for 16:9
                    set expected_out_bitrate (math $new_pixels \* 0.15 \* 30)
                else
                    # When re-encoding at same resolution
                    set total_pixels (math $width \* $height)
                    set expected_out_bitrate (math $total_pixels \* 0.15 \* 30)
                end

                set expected_bitrate_mbps (printf "%.2f" (math $expected_out_bitrate / 1000000))
                set expected_size_bytes (math "round($expected_out_bitrate / 8 * $duration)")
                set expected_size (echo $expected_size_bytes | numfmt --to=iec-i --suffix=B)
                set expected_savings_pct (math "round(($source_bitrate - $expected_out_bitrate) / $source_bitrate * 100)")

                echo ""
                echo "Expected compression:"
                echo "  Bitrate: $current_bitrate_mbps Mbps → $expected_bitrate_mbps Mbps"
                echo "  File size: $input_size → ~$expected_size (~$expected_savings_pct% reduction)"
                echo ""
            end

            # Choose encoding method based on --best flag
            if test $use_best -eq 1
                # Use optimal CPU encoding settings for best compression
                if test $needs_scaling -eq 1
                    set vf_option "-vf"
                    set vf_value "$scale_filter_cpu"
                else
                    set vf_option ""
                    set vf_value ""
                end

                if test -n "$vf_option"
                    ffmpeg -loglevel error -stats -y -i "$input" $vf_option $vf_value \
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
                # Use existing fast encoding with hardware acceleration
                echo "Processing with hardware acceleration (VAAPI)..."
                ffmpeg -loglevel error -stats -y -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -hwaccel_output_format vaapi -i "$input" \
                          -vf "$scale_filter_vaapi" -c:v h264_vaapi -qp 23 -c:a copy "$output"
                set ffmpeg_success $status
                if test $ffmpeg_success -ne 0
                    echo "Hardware acceleration failed, falling back to CPU encoding..."
                    ffmpeg -loglevel error -stats -y -i "$input" -vf "$scale_filter_cpu" -c:v libx264 -preset ultrafast -crf 23 -threads 0 -c:a copy "$output"
                    set ffmpeg_success $status
                end
            end
            
            if test $ffmpeg_success -eq 0
                set output_size (stat -c %s "$output" | numfmt --to=iec-i --suffix=B)
                echo ""
                echo "Output file size: $output_size"
                if test $mode = force
                    trash-put "$input"
                    mv "$output" "$input"
                    echo "Successfully downscaled $input (original moved to trash)"
                else
                    echo "Successfully downscaled to $output"
                end
            else
                echo "Error processing $input"
                if test $mode = force
                    rm -f "$output"
                end
                return 1
            end
        else
            echo "Processing: $input"
            echo "Video resolution is $width"x"$height (short side: $short_dim pixels, already ≤{$target_res}p), skipping"
        end
        
        if test (count $inputs) -gt 1
            echo ""
        end
    end
end
