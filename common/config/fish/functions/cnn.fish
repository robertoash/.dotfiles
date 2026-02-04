function cnn -d "Launch CNN stream with rofi_xtream MPV parameters"
    mpv \
        --force-window=immediate \
        --cache=yes \
        --cache-pause=no \
        --cache-secs=20 \
        --demuxer-max-bytes=100M \
        --demuxer-max-back-bytes=1M \
        --network-timeout=60 \
        --stream-lavf-o=reconnect=1 \
        --stream-lavf-o=reconnect_streamed=1 \
        --stream-lavf-o=reconnect_delay_max=5 \
        --stream-lavf-o=follow_redirects=1 \
        --user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36' \
        --http-header-fields='Accept: */*' \
        --referrer=http://uri69635.cdn-kok.me \
        --wayland-app-id=cnn_stream \
        --title='CNN Live' \
        http://uri69635.cdn-kok.me/live/48f07785de/f165bbc27a/324963.ts
end
