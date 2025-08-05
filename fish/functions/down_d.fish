function down_d --description 'Download videos with yt-dlp, fallback to slower method for failures'
    set -l yt_dlp_path "/home/rash/.local/bin/yt-dlp"
    set -l failed_urls
    set -l processed_args
    
    # Process arguments - wrap URLs in quotes if not already wrapped
    for arg in $argv
        # Check if argument looks like a URL and isn't already quoted
                if string match -q "*://*" -- $arg
                        # Check if already wrapped in quotes
                        if not string match -qr '^".*"$' -- $arg
                                set -a processed_args "\"$arg\""
                        else
                                set -a processed_args $arg
                        end
                else
                        set -a processed_args $arg
                end
        end
        
        echo "Starting downloads with fast method (yt_d)..."
        
        # Try yt_d method first for all URLs
        for arg in $processed_args
                if string match -q "*://*" -- $arg
                        echo "Trying fast method for: $arg"
                        
                        # yt_d method - fast with axel
                        if not eval $yt_dlp_path -f bestvideo+bestaudio/best --no-abort-on-error --add-metadata --external-downloader axel --external-downloader-args "'-n 16'" $arg
                                echo "Fast method failed for: $arg"
                                set -a failed_urls $arg
                        else
                                echo "Fast method succeeded for: $arg"
                        end
                end
        end
        
        # If there are failures, try sp_d method for failed URLs
        if test (count $failed_urls) -gt 0
                echo ""
                echo "Retrying failed downloads with slower method (sp_d)..."
                echo "Failed URLs: "(count $failed_urls)
                
                for url in $failed_urls
                        echo "Trying slower method for: $url"
                        
                        # sp_d method - optimized for speed
                        if not eval $yt_dlp_path -f bestvideo+bestaudio/best \
                                    --concurrent-fragments 4 \
                                    --no-abort-on-error \
                                    --legacy-server-connect \
                                    --add-metadata \
                                    --no-check-certificates \
                                    --impersonate Edge:Windows \
                                    --cookies-from-browser firefox \
                                    --username '$SP_USER' \
                                    --password '$SP_PASS' \
                                    --socket-timeout 30 \
                                    --retry-sleep linear=1::2 \
                                    --fragment-retries 5 \
                                    $url
                                echo "Slower method also failed for: $url"
                        else
                                echo "Slower method succeeded for: $url"
                        end
                end
        end
        
        if test (count $failed_urls) -eq 0
                echo ""
                echo "✅ All downloads completed successfully with fast method!"
        else
                echo ""
                echo "📊 Download summary:"
                echo "  • Fast method: "(math (count $processed_args) - (count $failed_urls))" successful"
                echo "  • Slow method attempts: "(count $failed_urls)
        end
end
