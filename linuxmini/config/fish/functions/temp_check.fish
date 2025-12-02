function temp_check
    set -l device "/dev/sda"  # default device
    set -l interval 0         # default no loop
    
    # Parse arguments
    set -l i 1
    while test $i -le (count $argv)
        switch $argv[$i]
            case -n
                if test $i -eq (count $argv)
                    echo "Error: -n requires a seconds argument"
                    return 1
                end
                set interval $argv[(math $i + 1)]
                if not string match -qr '^[0-9]+$' $interval
                    echo "Error: interval must be a positive integer"
                    return 1
                end
                set i (math $i + 1)  # skip the next argument
            case '*'
                set device $argv[$i]
        end
        set i (math $i + 1)
    end
    
    # Check if device exists before running smartctl
    if not test -e $device
        echo "Warning: Device $device does not exist"
        return 1
    end
    
    if test $interval -eq 0
        # Single run
        echo "Checking temperature for $device:"
        sudo smartctl -a $device | rg temp
    else
        # Loop mode
        echo "Monitoring temperature for $device every $interval seconds (Ctrl+C to stop):"
        while true
            echo "--- $(date) ---"
            sudo smartctl -a $device | rg temp
            sleep $interval
        end
    end
end
