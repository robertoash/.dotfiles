#!/bin/bash
# ~/.config/scripts/iptv/upload_iptv_files_to_server.sh

set -euo pipefail

# ========== CONFIG ==========
SOURCE_DIR="/home/rash/.config/scripts/_cache/iptv/server_files/"
DESTINATION="dockerlab:/home/rash/docker/docker_data/iptv_server/html/"

LOG_FILE="/home/rash/.config/scripts/_logs/iptv/last_rsync_to_server.log"

# ========== SCRIPT ==========
echo "📦 Starting IPTV rsync deployment..." | tee "$LOG_FILE"

rsync -avz --delete "$SOURCE_DIR" "$DESTINATION" | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ Rsync completed successfully at $(date)" | tee -a "$LOG_FILE"
else
    echo "❌ Rsync failed with exit code $EXIT_CODE at $(date)" | tee -a "$LOG_FILE"
    exit $EXIT_CODE
fi
