#!/bin/bash
# ~/.config/scripts/iptv/full_iptv_refresh.sh

set -euo pipefail

# ========== Start Timer ==========
start_time=$(date +%s)

echo "🔄 Running IPTV parser..."
~/.config/scripts/iptv/iptv_m3u_gen.py
if [ $? -ne 0 ]; then
    echo "❌ IPTV parser failed!"
    exit 1
fi

echo "💾 Sending IPTV files to server..."
~/.config/scripts/iptv/upload_iptv_files_to_server.sh
if [ $? -ne 0 ]; then
    echo "❌ Backup script failed!"
    exit 1
fi

# ========== End Timer ==========
end_time=$(date +%s)
duration=$((end_time - start_time))

minutes=$((duration / 60))
seconds=$((duration % 60))

echo "✅ Full IPTV refresh completed in ${minutes} min ${seconds} sec."
