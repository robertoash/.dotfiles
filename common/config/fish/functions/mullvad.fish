function mullvad
    # Check for DNS conflicts before connecting
    if test "$argv[1]" = "connect"
        # Check if Tailscale is managing DNS
        if grep -q "tailscale" /etc/resolv.conf 2>/dev/null
            echo "Error: Can't set DNS. Tailscale is connected and managing DNS." >&2
            echo "Disconnect Tailscale first: tailscale down" >&2
            return 1
        end
    end

    # Call real mullvad command
    command mullvad $argv
end
