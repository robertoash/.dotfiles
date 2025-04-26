#!/bin/bash

# --- Step 1: Run remote IPTV parser ---
echo "🔄 Running remote IPTV parser..."
ssh root@dockerlab 'python3 /root/dev/setup_files/iptv_server/iptv_m3u_gen.py'
if [ $? -ne 0 ]; then
    echo "❌ Failed running remote IPTV parser!"
    exit 1
fi

# --- Step 2: Run backup script locally ---
echo "💾 Running local backup script..."
run_bkup_script --script iptv
if [ $? -ne 0 ]; then
    echo "❌ Backup script failed!"
    exit 1
fi

# --- Step 3: Sync IPTV JSON ---
echo "🔄 Syncing IPTV JSON locally..."
~/.config/scripts/rofi/rofi_iptv.py --sync-json
if [ $? -ne 0 ]; then
    echo "❌ IPTV JSON sync failed!"
    exit 1
fi

echo "✅ Full IPTV refresh completed successfully! 🎉"
