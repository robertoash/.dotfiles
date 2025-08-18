function downscale_video
    argparse 'f/force' -- $argv
    
    if test (count $argv) -eq 0 -o (count $argv) -gt 2
        echo "Usage: downscale_video <input> [output]"
        echo "       downscale_video -f <input>  (overwrites input file)"
        return 1
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
    
    if test $height -gt 1440
        if ffmpeg -y -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 -hwaccel_output_format vaapi -i $input \
                  -vf "scale_vaapi=-1:1440:format=nv12" -c:v h264_vaapi -qp 23 -c:a copy $output 2>/dev/null
            or ffmpeg -y -i $input -vf "scale=-2:1440" -c:v libx264 -preset ultrafast -crf 23 -threads 0 -c:a copy $output
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
        echo "Video height is $height pixels (already ≤1440p)"
        if test $overwrite_mode = true
            rm -f $output
        end
    end
end