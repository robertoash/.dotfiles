function xtream --description "Browse and watch Xtream IPTV channels with fzf"
    set -l proxy_server "$XTREAM_SERVER"
    set -l proxy_user "$XTREAM_USERNAME"
    set -l proxy_pass "$XTREAM_PASSWORD"

    if test -z "$proxy_server" -o -z "$proxy_user" -o -z "$proxy_pass"
        echo "❌ Missing xtream credentials (check sops-secrets service)" >&2
        return 1
    end

    echo "🔍 Loading channels..." >&2

    # Fetch streams and format for fzf
    set -l selection (curl -s "$proxy_server/player_api.php?username=$proxy_user&password=$proxy_pass&action=get_live_streams" \
        | python3 -c "
import sys, json
streams = json.load(sys.stdin)
for s in streams:
    # Format: stream_id|channel_name
    print(f\"{s['stream_id']}|{s['name']}\")
" | fzf --prompt="Select channel: " \
        --preview-window=hidden \
        --height=40% \
        --reverse)

    if test -z "$selection"
        echo "❌ No channel selected" >&2
        return 1
    end

    # Extract stream ID and name
    set -l stream_id (echo $selection | cut -d'|' -f1)
    set -l channel_name (echo $selection | cut -d'|' -f2-)

    set -l stream_url "$proxy_server/live/$proxy_user/$proxy_pass/$stream_id.ts"

    echo "🎬 Launching: $channel_name"
    mpv --quiet \
        --force-window=immediate \
        --cache=yes \
        --cache-pause=no \
        --cache-secs=20 \
        --demuxer-max-bytes=100M \
        --title="$channel_name" \
        $stream_url
end
