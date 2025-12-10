#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Get total physical memory in GB
TOTAL_BYTES=$(sysctl -n hw.memsize)
TOTAL_GB=$((TOTAL_BYTES / 1024 / 1024 / 1024))

# Get memory stats from vm_stat
VM_STAT=$(vm_stat)
PAGE_SIZE=$(echo "$VM_STAT" | head -1 | grep -o '[0-9]\+')

# Extract active and wired pages (this is "app memory" like btop shows)
PAGES_ACTIVE=$(echo "$VM_STAT" | grep "Pages active" | awk '{print $3}' | tr -d '.')
PAGES_WIRED=$(echo "$VM_STAT" | grep "Pages wired down" | awk '{print $4}' | tr -d '.')

# Calculate used memory in GB (active + wired)
USED_BYTES=$(( (PAGES_ACTIVE + PAGES_WIRED) * PAGE_SIZE ))
USED_GB=$((USED_BYTES / 1024 / 1024 / 1024))

/opt/homebrew/bin/sketchybar --set memory label="${USED_GB}/${TOTAL_GB}GB"
