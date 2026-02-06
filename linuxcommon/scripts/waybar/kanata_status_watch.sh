#!/usr/bin/env bash
# Watch kanata status file with watchexec
# watchexec runs at startup + on each file change

STATUS_FILE="/tmp/kanata_status.json"

# watchexec cats the file once at startup and once per change
exec watchexec -q --watch "$STATUS_FILE" cat "$STATUS_FILE"
