function down_d --description 'Download videos with yt-dlp, 3-tier fallback: fast -> fast+impersonation -> slow+compatible'
    set -l yt_dlp_path "/home/rash/.local/bin/yt-dlp"
    set -l fast_failed_urls
    set -l medium_failed_urls
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
    
    # TIER 1: Try fast method first (yt-dlp + axel, no impersonation)
    for arg in $processed_args
        if string match -q "*://*" -- $arg
            echo "Trying fast method for: $arg"
            
            # Fast method - axel with 16 connections
            if not eval $yt_dlp_path -f bestvideo+bestaudio/best --no-abort-on-error --add-metadata --external-downloader axel --external-downloader-args "'-n 16'" $arg
                echo "Fast method failed for: $arg"
                set -a fast_failed_urls $arg
            else
                echo "Fast method succeeded for: $arg"
            end
        end
    end
    
    # TIER 2: Try medium method for fast failures (yt-dlp + axel + impersonation)
    if test (count $fast_failed_urls) -gt 0
        echo ""
        echo "Retrying failed downloads with fast method + browser impersonation..."
        echo "Failed URLs from fast method: "(count $fast_failed_urls)
        
        for url in $fast_failed_urls
            echo "Trying fast+impersonation method for: $url"
            
            # Medium method - axel + impersonation + cookies
            if not eval $yt_dlp_path -f bestvideo+bestaudio/best \
                        --no-abort-on-error \
                        --add-metadata \
                        --external-downloader axel \
                        --external-downloader-args "'-n 8'" \
                        --impersonate Edge:Windows \
                        --cookies-from-browser firefox \
                        $url
                echo "Fast+impersonation method failed for: $url"
                set -a medium_failed_urls $url
            else
                echo "Fast+impersonation method succeeded for: $url"
            end
        end
    end
    
    # TIER 3: Try slow method for remaining failures (yt-dlp built-in downloader)
    if test (count $medium_failed_urls) -gt 0
        echo ""
        echo "Retrying remaining failed downloads with slower method (sp_d)..."
        echo "Failed URLs from medium method: "(count $medium_failed_urls)
        
        for url in $medium_failed_urls
            echo "Trying slower method for: $url"
            
            # Slow method - yt-dlp built-in with all compatibility features
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
    
    # Summary
    if test (count $fast_failed_urls) -eq 0
        echo ""
        echo "✅ All downloads completed successfully with fast method!"
    else if test (count $medium_failed_urls) -eq 0
        echo ""
        echo "✅ All downloads completed! Some required browser impersonation."
        echo "📊 Download summary:"
        echo "  • Fast method: "(math (count $processed_args) - (count $fast_failed_urls))" successful"
        echo "  • Fast+impersonation method: "(count $fast_failed_urls)" successful"
    else
        echo ""
        echo "📊 Download summary:"
        set -l fast_success (math (count $processed_args) - (count $fast_failed_urls))
        set -l medium_success (math (count $fast_failed_urls) - (count $medium_failed_urls))
        set -l slow_attempts (count $medium_failed_urls)
        
        echo "  • Fast method: $fast_success successful"
        echo "  • Fast+impersonation method: $medium_success successful"
        echo "  • Slow method attempts: $slow_attempts"
    end
end