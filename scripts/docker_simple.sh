#! /bin/bash
# Simple docker ps with combined ports

awk -F '[[:space:]][[:space:]]+' '
BEGIN {
    printf "%-15s %-25s %-60s %-10s\n", "CONTAINER ID", "STATUS", "PORTS", "NAMES";
}
(NR>1){
    split($6, ports, ", ");
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

    printf "%-15s %-25s %-60s %-10s\n", $1, $5, combined_ports, $NF
}' <(docker ps)
