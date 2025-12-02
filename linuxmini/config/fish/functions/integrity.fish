function integrity
    set -l config_dir ~/.config/wireguard
    
    if test (count $argv) -lt 2
        echo "Usage: integrity up|down --se|--us"
        return 1
    end
    
    set -l action $argv[1]
    set -l server $argv[2]
    
    # Validate action
    if not contains $action up down
        echo "Error: Action must be 'up' or 'down'"
        echo "Usage: integrity up|down --se|--us"
        return 1
    end
    
    # Validate server and set config file
    set -l config_file
    switch $server
        case --se
            set config_file $config_dir/integrity2-SE.conf
        case --us
            set config_file $config_dir/integrity2-US.conf
        case '*'
            echo "Error: Server must be --se or --us"
            echo "Usage: integrity up|down --se|--us"
            return 1
    end
    
    # Execute the command
    wg-quick $action $config_file
end
