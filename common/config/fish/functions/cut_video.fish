function cut_video
    # Prompt for input video path (required)
    read -P "Input video path: " -c input_video
    
    if test -z "$input_video"
        echo "Error: Input video path is required"
        return 1
    end
    
    if not test -f "$input_video"
        echo "Error: Input video file does not exist: $input_video"
        return 1
    end
    
    # Prompt for start timestamp (optional)
    read -P "Start timestamp (optional, format HH:MM:SS or SS): " start_timestamp
    
    # Prompt for end timestamp (optional)
    read -P "End timestamp (optional, format HH:MM:SS or SS): " end_timestamp
    
    # Prompt for overwrite confirmation
    set overwrite ""
    while test "$overwrite" != "y" -a "$overwrite" != "n"
        read -P "Overwrite $input_video? [y/n]: " overwrite
        if test "$overwrite" != "y" -a "$overwrite" != "n"
            echo "Please enter 'y' or 'n'"
        end
    end
    
    # Set output file based on overwrite choice
    if test "$overwrite" = "y"
        set output_file "$input_video"
    else
        read -P "Output file: " -c output_file
        if test -z "$output_file"
            echo "Error: Output file is required"
            return 1
        end
    end
    
    # Build the ffmpeg command
    set ffmpeg_cmd "ffmpeg -i \"$input_video\""
    
    if test -n "$start_timestamp"
        set ffmpeg_cmd "$ffmpeg_cmd -ss $start_timestamp"
    end
    
    if test -n "$end_timestamp"
        set ffmpeg_cmd "$ffmpeg_cmd -to $end_timestamp"
    end
    
    set ffmpeg_cmd "$ffmpeg_cmd -c copy"
    
    # Handle overwriting scenario
    if test "$input_video" = "$output_file"
        # Create temp file for overwriting scenario
        set temp_file (mktemp --suffix=".$(string match -r '\.[^.]+$' -- $input_video | string sub -s 2)")
        set ffmpeg_cmd "$ffmpeg_cmd \"$temp_file\" && trash-put \"$input_video\" && mv \"$temp_file\" \"$output_file\""
    else
        set ffmpeg_cmd "$ffmpeg_cmd \"$output_file\""
    end
    
    # Output the command ready to run
    echo $ffmpeg_cmd
    
    # Put the command in the command line for easy execution
    commandline -r $ffmpeg_cmd
end