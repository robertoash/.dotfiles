#!/usr/bin/env bash

choices="🧠 ChatGPT
🔍 Perplexity
🎞️ SVT Play
🎬 Max
🎵 YouTube
🧿 Overseerr
🧬 GitHub
📺 CNN
🧠 Claude"

choice=$(echo "$choices" | rofi -dmenu -i -p "Launch App:")

launch() {
  brave --new-window \
    --enable-features=UseOzonePlatform \
    --ozone-platform=wayland \
    --profile-directory="AppProfile" \
    --app="$1"
}

trigger() {
  python3 ~/.config/scripts/secrets/launch_iptv.py --"$1"
}

case "$choice" in
  "🧠 ChatGPT") launch "https://chatgpt.com/" ;;
  "🔍 Perplexity") launch "https://perplexity.ai" ;;
  "🎞️ SVT Play") launch "https://svtplay.se" ;;
  "🎬 Max") launch "https://max.com" ;;
  "🎵 YouTube") launch "https://www.youtube.com" ;;
  "🧿 Overseerr") launch "https://watchlist.rashlab.net" ;;
  "🧬 GitHub") launch "https://github.com" ;;
  "📺 CNN") trigger "cnn" ;;
  "🧠 Claude") launch "https://claude.ai" ;;
  *) exit 1 ;;
esac
