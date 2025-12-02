function readlyvpn
    switch $argv[1]
        case start
            scutil --nc start "Readly-VPN"
        case stop
            scutil --nc stop "Readly-VPN"
        case status
            scutil --nc status "Readly-VPN"
        case '*'
            echo "Usage: readlyvpn [start|stop|status]"
            return 1
    end
end