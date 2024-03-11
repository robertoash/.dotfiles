#!/bin/sh

mullvad_status=$(mullvad status)
extern_ip=$(curl -SsfL http://api.ipify.org/?format=text)

vpn_is_up() {
	if echo "$mullvad_status" | grep -q 'Connected'; then
        return 0
    else
        return 1
    fi
}

if vpn_is_up; then
	printf '{"text": "󰕥", "tooltip": "connected. ip is %s", "class": "vpn-connected"}\n' "$extern_ip"
else
	printf '{"text": "", "tooltip": "disconnected. ip is %s", "class": "vpn-disconnected"}\n' "$extern_ip"
	#printf '{}\n'
fi