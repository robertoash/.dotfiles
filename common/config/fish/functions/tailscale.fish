function tailscale
    # Check for DNS conflicts before enabling Tailscale DNS
    if test "$argv[1]" = "up"; or test "$argv[1]" = "set"
        # Check if trying to enable DNS (default for 'up', or explicit with 'set')
        set -l enable_dns 0

        if test "$argv[1]" = "up"
            # 'tailscale up' enables DNS by default unless --accept-dns=false
            set enable_dns 1
            for arg in $argv[2..-1]  # Check all args after 'up'
                if string match -q -- "*accept-dns=false*" $arg
                    set enable_dns 0
                    break
                end
            end
        else if test "$argv[1]" = "set"
            # Check if --accept-dns=true is specified
            for arg in $argv[2..-1]  # Check all args after 'set'
                if string match -q -- "*accept-dns=true*" $arg
                    set enable_dns 1
                    break
                end
            end
        end

        # If enabling DNS, check for Mullvad conflict
        if test $enable_dns -eq 1
            if command mullvad status 2>/dev/null | grep -q "Connected"
                echo "Error: Can't enable DNS. Mullvad VPN is connected and managing DNS." >&2
                echo "Disconnect Mullvad first: mullvad disconnect" >&2
                return 1
            end
        end
    end

    # Call real tailscale command - $argv expands to all arguments
    command tailscale $argv
end
