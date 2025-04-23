#!/usr/bin/env bash

hosts=$(awk '
BEGIN { host = ""; hostname = "" }

/^Host / {
  if (host != "" || hostname != "")
    print (host != "" ? host : hostname)
  host = $2
  hostname = ""
  next
}

/^Hostname / {
  hostname = $2
}

END {
  if (host != "" || hostname != "")
    print (host != "" ? host : hostname)
}
' ~/.ssh/config)

choice=$(printf "%s\n" "$hosts" | rofi -dmenu -p "SSH")

[ -n "$choice" ] && exec kitty ssh "$choice"
