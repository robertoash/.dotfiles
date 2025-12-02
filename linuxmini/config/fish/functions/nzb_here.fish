function nzb_here
    set current_dir (pwd)  # Evaluate pwd once at the start
    for file in $argv
        if test "$SECURE_SHELL" = "1"
            # Secure mode: no logging, no intermediate files, no traces
            if nzbget -c ~/.config/nzbget/nzbget.conf \
                -o DestDir="$current_dir" \
                -o WriteLog=none \
                -o InterDir=/tmp/nzbget-temp-(random) \
                -o TempDir=/tmp/nzbget-temp-(random) \
                -o QueueDir=/tmp/nzbget-queue-(random) \
                -o LogFile=/dev/null \
                -o ErrorTarget=none \
                -o WarningTarget=none \
                -o InfoTarget=none \
                -o DetailTarget=none \
                -o DebugTarget=none \
                $file
                # Delete .nzb file on success
                rm $file
                echo "Downloaded and deleted: $file"
            else
                echo "Failed to download: $file (keeping file)"
            end
        else
            # Normal mode
            if nzbget -c ~/.config/nzbget/nzbget.conf -o DestDir="$current_dir" $file
                # Delete .nzb file on success
                rm $file
                echo "Downloaded and deleted: $file"
            else
                echo "Failed to download: $file (keeping file)"
            end
        end
    end
end
