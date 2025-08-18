function downscale_video
    argparse 'f/force' 't/target-resolution=' -- $argv
    
    if test (count $argv) -eq 0 -o (count $argv) -gt 2
        echo "Usage: downscale_video [-t/--target-resolution 1440|1080|720] <input> [output]"
        echo "       downscale_video -f [-t resolution] <input>  (overwrites input file)"
        return 1
    end
    
    # Validate target resolution
    if set -q _flag_target_resolution
        set target_res $_flag_target_resolution
        if not contains $target_res 1440 1080 720
            echo "Error: target resolution must be 1440, 1080, or 720"
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
        if ffmpeg -y -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -hwaccel_output_format vaapi -i $input \
                  -vf "scale_vaapi=-2:$target_res:format=nv12" -c:v h264_vaapi -qp 23 -c:a copy $output 2>/dev/null
            or ffmpeg -y -i $input -vf "scale=-2:$target_res" -c:v libx264 -preset ultrafast -crf 23 -threads 0 -c:a copy $output
            if test $overwrite_mode = true
                mv $output $input
                echo "Successfully downscaled and overwrote $input"
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