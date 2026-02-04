function down_d --description 'Download videos with yt-dlp, 3-tier fallback with rich progress display'
    # Simple wrapper around Python implementation
    python3 ~/.local/bin/down_d_impl.py $argv
end
