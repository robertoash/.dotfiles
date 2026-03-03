function cnn --description "Watch CNN via Xtream proxy"
    set -l proxy_server "$XTREAM_SERVER"
    set -l proxy_user "$XTREAM_USERNAME"
    set -l proxy_pass "$XTREAM_PASSWORD"

    if test -z "$proxy_server" -o -z "$proxy_user" -o -z "$proxy_pass"
        echo "❌ Missing xtream credentials (check sops-secrets service)" >&2
        return 1
    end

    # Find CNN 4K stream ID dynamically
    echo "🔍 Finding CNN 4K stream..."
    set -l stream_id (curl -s "$proxy_server/player_api.php?username=$proxy_user&password=$proxy_pass&action=get_live_streams" \
        | python3 -c "import sys, json; streams = json.load(sys.stdin); cnn = [s for s in streams if 'USA| CNN 4K' in s.get('name', '')]; print(cnn[0]['stream_id'] if cnn else '')")

    if test -z "$stream_id"
        echo "❌ CNN 4K stream not found" >&2
        return 1
    end

    set -l stream_url "$proxy_server/live/$proxy_user/$proxy_pass/$stream_id.ts"

    echo "🎬 Launching CNN 4K (stream ID: $stream_id)..."
    mpv --quiet \
        --force-window=immediate \
        --cache=yes \
        --cache-pause=no \
        --cache-secs=20 \
        --demuxer-max-bytes=100M \
        --title="CNN" \
        $stream_url
end
