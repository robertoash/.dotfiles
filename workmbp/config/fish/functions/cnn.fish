function cnn --description "Watch CNN via Xtream proxy"
    # Read credentials from sops secrets
    set -l secrets_dir "$XDG_RUNTIME_DIR/secrets"

    if not test -d "$secrets_dir"
        echo "❌ Secrets directory not found: $secrets_dir" >&2
        echo "Set up the secrets directory or set XDG_RUNTIME_DIR appropriately" >&2
        return 1
    end

    set -l proxy_server "http://linuxmini:8080"
    set -l proxy_user (cat "$secrets_dir/xtream/proxy-users/user2/username" 2>/dev/null)
    set -l proxy_pass (cat "$secrets_dir/xtream/proxy-users/user2/password" 2>/dev/null)

    if test -z "$proxy_user" -o -z "$proxy_pass"
        echo "❌ Failed to read proxy credentials from sops" >&2
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
