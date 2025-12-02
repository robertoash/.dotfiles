function downscale_video
    argparse 'h/help' 'f/force' 't/target-quality=' 'o/output-dir=' -- $argv
    
    if set -q _flag_help
        echo "downscale_video - Downscale video files to a target quality"
        echo ""
        echo "Usage:"
        echo "  downscale_video [OPTIONS] <input> [output]"
        echo "  downscale_video [OPTIONS] -o <output_dir> <input1> [input2] ..."
        echo "  downscale_video -f [OPTIONS] <input1> [input2] ..."
        echo ""
        echo "Options:"
        echo "  -h, --help                Show this help message"
        echo "  -f, --force               Overwrite the input file (no output file needed)"
        echo "  -o, --output-dir          Output directory for multiple inputs (appends _down to names)"
        echo "  -t, --target-quality      Target quality: 1440, 1080, or 720 (default: 1440)"
        echo ""
        echo "Description:"
        echo "  Downscales video files to the specified quality if they are larger."
        echo "  Uses hardware acceleration (VAAPI) when available, falls back to CPU encoding."
        echo "  If the video is already at or below the target quality, no processing occurs."
        echo ""
        echo "Examples:"
        echo "  downscale_video video.mp4 output.mp4              # Downscale to 1440p"
        echo "  downscale_video -t 720 video.mp4 output.mp4       # Downscale to 720p"
        echo "  downscale_video -f video.mp4                      # Overwrite original file"
        echo "  downscale_video -o /path/to/out video1.mp4 video2.mp4  # Multiple files to directory"
        return 0
    end
    
    if test (count $argv) -eq 0
        echo "Usage: downscale_video [-t/--target-quality 1440|1080|720] <input> [output]"
        echo "       downscale_video -f [-t quality] <input> ...  (overwrites input files)"
        echo "       downscale_video -o <output_dir> <input1> [input2] ..."
        echo "Try 'downscale_video --help' for more information."
        return 1
    end
    
    # Validate target resolution
    if set -q _flag_target_quality
        set target_res $_flag_target_quality
        if not contains $target_res 1440 1080 720
            echo "Error: target quality must be 1440, 1080, or 720"
            return 1
        end
    else
        set target_res 1440
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
        set output_dir (realpath $_flag_output_dir)
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
        set input (realpath $input_file)
        
        # Determine output path based on mode
        if test $mode = force
            set output (mktemp --suffix=.mp4)
        else if test $mode = multiple
            set basename (basename $input)
            set name (string replace -r '\.[^.]*$' '' $basename)
            set ext (string replace -r '^.*\.' '.' $basename)
            set output "$output_dir/$name"_down"$ext"
        else # single mode
            set output $single_output
        end
        
        set height (ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 $input)
        
        if test $height -gt $target_res
            set duration (ffprobe -v error -show_entries format=duration -of csv=p=0 $input)
            set duration_formatted (printf "%.0f" $duration | awk '{print int($1/3600)":"int(($1%3600)/60)":"int($1%60)}')
            echo "Processing: $input"
            echo "Downscaling video from $height\p to $target_res\p (Duration: $duration_formatted)..."
            set input_size (stat -c %s $input | numfmt --to=iec-i --suffix=B)
            echo "Input file size: $input_size"
            
            echo "Processing with hardware acceleration (VAAPI)..."
            if ffmpeg -loglevel error -stats -y -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -hwaccel_output_format vaapi -i $input \
                      -vf "scale_vaapi=-2:$target_res:format=nv12" -c:v h264_vaapi -qp 23 -c:a copy $output
                set ffmpeg_success $status
            else
                echo "Hardware acceleration failed, falling back to CPU encoding..."
                if ffmpeg -loglevel error -stats -y -i $input -vf "scale=-2:$target_res" -c:v libx264 -preset ultrafast -crf 23 -threads 0 -c:a copy $output
                    set ffmpeg_success $status
                else
                    set ffmpeg_success 1
                end
            end
            
            if test $ffmpeg_success -eq 0
                set output_size (stat -c %s $output | numfmt --to=iec-i --suffix=B)
                echo ""
                echo "Output file size: $output_size"
                if test $mode = force
                    trash-put $input
                    mv $output $input
                    echo "Successfully downscaled $input (original moved to trash)"
                else
                    echo "Successfully downscaled to $output"
                end
            else
                echo "Error processing $input"
                if test $mode = force
                    rm -f $output
                end
                return 1
            end
        else
            echo "Processing: $input"
            echo "Video height is $height pixels (already ≤{$target_res}p), skipping"
        end
        
        if test (count $inputs) -gt 1
            echo ""
        end
    end
end
