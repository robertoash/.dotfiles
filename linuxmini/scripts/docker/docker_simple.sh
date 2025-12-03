#!/bin/bash

# First AWK command: Process ports and calculate max_ports_width
awk_output=$(awk -F '[[:space:]][[:space:]]+' '

# Function to process ports and return the combined port string

function process_ports(ports_str,    ports, tcp_ports, udp_ports, i, port_split, protocol, port_only) {
    split(ports_str, ports, ", ");
    tcp_ports = "";
    udp_ports = "";

    for (i in ports) {
        # Remove leading 0.0.0.0: or ::: in port mappings
        gsub(/(0.0.0.0:|:::)/, "", ports[i]);
        # If there is a port mapping (indicated by "->"), split and compare
        if (ports[i] ~ /->/) {
            split(ports[i], port_split, "->");
            # Extract and store protocol
            protocol = "";
            if (port_split[2] ~ /\/(tcp|udp)$/) {
                match(port_split[2], /\/(tcp|udp)$/);
                protocol = substr(port_split[2], RSTART, RLENGTH);
            }
            # Compare ports without protocol
            gsub(/\/(tcp|udp)$/, "", port_split[1]);
            gsub(/\/(tcp|udp)$/, "", port_split[2]);
            ports[i] = (port_split[1] == port_split[2]) ? port_split[1] protocol : ports[i];
        }
        # Remove protocol and append port
        port_only = ports[i];
        gsub(/\/(tcp|udp)$/, "", port_only);
        if (ports[i] ~ /\/tcp$/) {
            if (tcp_ports !~ port_only) {
                tcp_ports = tcp_ports (tcp_ports ? "," : "") port_only;
            }
        } else if (ports[i] ~ /\/udp$/) {
            if (udp_ports !~ port_only) {
                udp_ports = udp_ports (udp_ports ? "," : "") port_only;
            }
        }
    }
    # Append protocol at the end and combine ports
    combined_ports = "";
    if (tcp_ports != "") combined_ports = tcp_ports "/tcp";
    if (udp_ports != "") combined_ports = combined_ports (combined_ports ? "," : "") udp_ports "/udp";

    return combined_ports;
}

BEGIN { max_ports_width = 15; max_status_width = 10; }  # Initialize with minimum widths

NR > 1 {
    processed_ports = process_ports($6);
    print $1 "|" $5 "|" processed_ports "|" $NF;
    if (length(processed_ports) > max_ports_width) {
        max_ports_width = length(processed_ports);
    }
    if (length($5) > max_status_width) {
        max_status_width = length($5);
    }
}

END {
    print "MAX_WIDTH:" max_ports_width + 3 "|" max_status_width + 3;
}
' <(docker ps))

# Extract max_ports_width, max_status_width and remove them from the output
max_widths=$(echo "$awk_output" | grep "MAX_WIDTH:" | cut -d':' -f2)
max_ports_width=$(echo "$max_widths" | cut -d'|' -f1)
max_status_width=$(echo "$max_widths" | cut -d'|' -f2)
awk_output=$(echo "$awk_output" | grep -v "MAX_WIDTH:")

# Ensure widths are within their respective ranges
max_ports_width=$((max_ports_width > 60 ? 60 : max_ports_width))
max_ports_width=$((max_ports_width < 15 ? 15 : max_ports_width))
max_status_width=$((max_status_width > 30 ? 30 : max_status_width))
max_status_width=$((max_status_width < 10 ? 10 : max_status_width))

# Second AWK command: Print the data
echo "$awk_output" | awk -v max_ports_width="$max_ports_width" -v max_status_width="$max_status_width" -F '|' '
BEGIN {
    printf "%-15s %-" max_status_width "s %-" max_ports_width "s %-10s\n", "CONTAINER ID", "STATUS", "PORTS", "NAMES";
}
{
    printf "%-15s %-" max_status_width "s %-" max_ports_width "s %-10s\n", $1, $2, $3, $4;
}
'
