function downscale_video
    argparse 'h/help' 'f/force' 't/target-quality=' -- $argv
    
    if set -q _flag_help
        echo "downscale_video - Downscale video files to a target quality"
        echo ""
        echo "Usage:"
        echo "  downscale_video [OPTIONS] <input> [output]"
        echo "  downscale_video -f [OPTIONS] <input>"
        echo ""
        echo "Options:"
        echo "  -h, --help                Show this help message"
        echo "  -f, --force               Overwrite the input file (no output file needed)"
        echo "  -t, --target-quality      Target quality: 1440, 1080, or 720 (default: 1440)"
        echo ""
        echo "Description:"
        echo "  Downscales video files to the specified quality if they are larger."
        echo "  Uses hardware acceleration (VAAPI) when available, falls back to CPU encoding."
        echo "  If the video is already at or below the target quality, no processing occurs."
        echo ""
        echo "Examples:"
        echo "  downscale_video video.mp4 output.mp4          # Downscale to 1440p"
        echo "  downscale_video -t 720 video.mp4 output.mp4   # Downscale to 720p"
        echo "  downscale_video -f video.mp4                  # Overwrite original file"
        echo "  downscale_video -f -t 1080 video.mp4          # Overwrite, downscale to 1080p"
        return 0
    end
    
    if test (count $argv) -eq 0 -o (count $argv) -gt 2
        echo "Usage: downscale_video [-t/--target-quality 1440|1080|720] <input> [output]"
        echo "       downscale_video -f [-t quality] <input>  (overwrites input file)"
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
    
    set input (realpath $argv[1])
    
    if set -q _flag_force
        if test (count $argv) -ne 1
            echo "Error: -f/--force flag requires exactly one argument"
            return 1
        end
        set output (mktemp --suffix=.mp4)
        set overwrite_mode true
    else if test (count $argv) -eq 2
        set output $argv[2]
        set overwrite_mode false
    else
        echo "Error: Output file required when not using -f/--force"
        return 1
    end
    
    set height (ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 $input)
    
    if test $height -gt $target_res
        echo "Downscaling video from {$height}p to {$target_res}p..."
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
            if test $overwrite_mode = true
                trash-put $input
                mv $output $input
                echo "Successfully downscaled $input (original moved to trash)"
            else
                echo "Successfully downscaled to $output"
            end
        else
            if test $overwrite_mode = true
                rm -f $output
            end
            return 1
        end
    else
        echo "Video height is $height pixels (already ≤{$target_res}p)"
        if test $overwrite_mode = true
            rm -f $output
        end
    end
end
