function down_d --description 'Download videos with yt-dlp, 3-tier fallback: fast -> fast+impersonation -> slow+compatible'
    set -l yt_dlp_path "/home/rash/.local/bin/yt-dlp"
    set -l fast_failed_urls
    set -l medium_failed_urls
    set -l quality_format "bestvideo+bestaudio/best"
    set -l urls

    # Parse arguments
    set -l i 1
    while test $i -le (count $argv)
        set -l arg $argv[$i]

        switch $arg
            case -h --help
                echo "Usage: down_d [OPTIONS] URL [URL...]"
                echo ""
                echo "Download videos with yt-dlp using a 3-tier fallback strategy."
                echo ""
                echo "Options:"
                echo "  -q, --quality QUALITY  Preferred video quality: 720, 1080, 1440, or 2160"
                echo "                         Downloads exact quality if available, closest above if not,"
                echo "                         or best available if no higher quality exists"
                echo "  -h, --help            Show this help message"
                echo ""
                echo "Examples:"
                echo "  down_d https://example.com/video"
                echo "  down_d -q 1080 https://example.com/video"
                echo "  down_d --quality 720 url1 url2 url3"
                return 0

            case -q --quality
                set i (math $i + 1)
                if test $i -gt (count $argv)
                    echo "Error: --quality requires a value (720, 1080, 1440, or 2160)"
                    return 1
                end

                set -l target_quality $argv[$i]
                switch $target_quality
                    case 720 1080 1440 2160
                        # Quality will be resolved per-video based on orientation
                        set quality_format $target_quality
                    case '*'
                        echo "Error: Invalid quality '$target_quality'. Must be 720, 1080, 1440, or 2160"
                        return 1
                end

            case '*'
                # It's a URL
                set -a urls $arg
        end

        set i (math $i + 1)
    end

    # Check if we have any URLs
    if test (count $urls) -eq 0
        echo "Error: No URLs provided"
        echo "Run 'down_d --help' for usage information"
        return 1
    end

    # Helper function to build format string
    function build_format_string -a url -a quality -a yt_dlp
        # If quality is "bestvideo+bestaudio/best" (default), just return it
        if test "$quality" = "bestvideo+bestaudio/best"
            echo "$quality"
            return
        end

        # Build format string: try format_id matching, then exact dimensions, then caps
        # format_id matching works for sites that use quality in the ID (like "1080p_HD")
        # Dimension matching works for sites with detailed metadata
        switch $quality
            case 720
                echo "bestvideo[format_id*=720]+bestaudio/bestvideo[height=720]+bestaudio/bestvideo[width=720]+bestaudio/bestvideo[height<=720][width<=720]+bestaudio/best"
            case 1080
                echo "bestvideo[format_id*=1080]+bestaudio/bestvideo[height=1080]+bestaudio/bestvideo[width=1080]+bestaudio/bestvideo[height<=1080][width<=1080]+bestaudio/best"
            case 1440
                echo "bestvideo[format_id*=1440]+bestaudio/bestvideo[height=1440]+bestaudio/bestvideo[width=1440]+bestaudio/bestvideo[height<=1440][width<=1440]+bestaudio/best"
            case 2160
                echo "bestvideo[format_id*=2160]+bestaudio/bestvideo[height=2160]+bestaudio/bestvideo[width=2160]+bestaudio/bestvideo[height<=2160][width<=2160]+bestaudio/best"
        end
    end

    echo "Starting downloads with fast method..."

    # TIER 1: Try fast method first (yt-dlp + axel, no impersonation)
    for url in $urls
        if string match -q "*://*" -- $url
            echo "Trying fast method for: $url"

            # Build format string based on video orientation
            set -l format_str (build_format_string "$url" "$quality_format" "$yt_dlp_path")
            echo "Using format: $format_str"

            # Fast method - axel with 16 connections
            if not $yt_dlp_path -f $format_str --no-abort-on-error --add-metadata --external-downloader axel --external-downloader-args '-n 16' $url
                echo "Fast method failed for: $url"
                set -a fast_failed_urls $url
            else
                echo "Fast method succeeded for: $url"
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

            # Build format string based on video orientation
            set -l format_str (build_format_string "$url" "$quality_format" "$yt_dlp_path")

            # Medium method - axel + impersonation + cookies
            if not $yt_dlp_path -f $format_str \
                        --no-abort-on-error \
                        --add-metadata \
                        --external-downloader axel \
                        --external-downloader-args '-n 8' \
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

            # Build format string based on video orientation
            set -l format_str (build_format_string "$url" "$quality_format" "$yt_dlp_path")

            # Slow method - yt-dlp built-in with all compatibility features
            if not $yt_dlp_path -f $format_str \
                        --concurrent-fragments 4 \
                        --no-abort-on-error \
                        --legacy-server-connect \
                        --add-metadata \
                        --no-check-certificates \
                        --impersonate Edge:Windows \
                        --cookies-from-browser firefox \
                        --username "$SP_USER" \
                        --password "$SP_PASS" \
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
        echo "  • Fast method: "(math (count $urls) - (count $fast_failed_urls))" successful"
        echo "  • Fast+impersonation method: "(count $fast_failed_urls)" successful"
    else
        echo ""
        echo "📊 Download summary:"
        set -l fast_success (math (count $urls) - (count $fast_failed_urls))
        set -l medium_success (math (count $fast_failed_urls) - (count $medium_failed_urls))
        set -l slow_attempts (count $medium_failed_urls)

        echo "  • Fast method: $fast_success successful"
        echo "  • Fast+impersonation method: $medium_success successful"
        echo "  • Slow method attempts: $slow_attempts"
    end
end
