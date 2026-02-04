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

    # Helper function to monitor parallel downloads with live progress
    function monitor_downloads -a tmpdir
        # Remaining args are alternating: pid1 pid2 pid3... hash1|url1 hash2|url2...
        # Need to figure out where PIDs end and mappings begin
        # Strategy: Find first arg with '|' character
        set -l all_args $argv[2..-1]
        set -l pids
        set -l url_map
        set -l found_separator 0

        for arg in $all_args
            if string match -q "*|*" -- $arg
                set found_separator 1
            end

            if test $found_separator -eq 0
                set -a pids $arg
            else
                set -a url_map $arg
            end
        end

        set -l total_downloads (count $pids)
        set -l active_pids $pids
        set -l completed_hashes

        echo ""
        echo "Monitoring $total_downloads parallel downloads..."
        echo ""

        # Monitor loop
        set -l first_iteration 1
        while test (count $active_pids) -gt 0
            set -l active_line_count 0

            # Build output for all active downloads
            set -l output_lines

            for mapping in $url_map
                set -l parts (string split '|' $mapping)
                set -l url_hash $parts[1]
                set -l url $parts[2]
                set -l short_url (string sub -l 40 $url)
                set -l status_file "$tmpdir/$url_hash.status"
                set -l log_file "$tmpdir/$url_hash.log"

                # Skip if already completed
                if contains $url_hash $completed_hashes
                    continue
                end

                set -l line_text ""

                if test -f $status_file
                    # Download completed - print permanently and mark as done
                    set -l dl_status (cat $status_file)
                    if test "$dl_status" = "success"
                        set line_text "✅ [$url_hash] $short_url: Complete"
                    else
                        set line_text "❌ [$url_hash] $short_url: Failed"
                    end
                    echo $line_text
                    set -a completed_hashes $url_hash
                else if test -f $log_file
                    # Extract latest progress from log (look for download progress indicators)
                    # Check for yt-dlp format: [download]  26.7% of  430.74MiB at  296.05KiB/s ETA 18:12
                    set -l progress (tail -10 $log_file 2>/dev/null | grep -E '\[download\].*%' | tail -1 | string trim | string sub -l 80)

                    # If no yt-dlp progress, check for axel format: [ 26%]  ..........
                    if test -z "$progress"
                        set progress (tail -10 $log_file 2>/dev/null | grep -E '\[\s*[0-9]+%\]' | tail -1 | string trim | string sub -l 80)
                    end

                    if test -n "$progress"
                        set line_text "⬇️  $progress"
                    else
                        set line_text "⏳ [$url_hash] $short_url: Running..."
                    end
                    set -a output_lines $line_text
                    set active_line_count (math $active_line_count + 1)
                else
                    set line_text "⏳ [$url_hash] $short_url: Starting..."
                    set -a output_lines $line_text
                    set active_line_count (math $active_line_count + 1)
                end
            end

            # Print active downloads (will be rewritten)
            if test $active_line_count -gt 0
                # Move cursor up on subsequent iterations
                if test $first_iteration -eq 0
                    tput cuu $active_line_count
                end
                set first_iteration 0

                for line in $output_lines
                    printf "\r%s%s\n" (tput el) $line
                end
            end

            # Check which PIDs are still active
            set -l new_active_pids
            for pid in $active_pids
                if ps -p $pid >/dev/null 2>&1
                    set -a new_active_pids $pid
                end
            end
            set active_pids $new_active_pids

            # Sleep briefly before next update
            sleep 0.5
        end

        # Final check for any remaining completions
        for mapping in $url_map
            set -l parts (string split '|' $mapping)
            set -l url_hash $parts[1]
            set -l url $parts[2]
            set -l short_url (string sub -l 40 $url)
            set -l status_file "$tmpdir/$url_hash.status"

            if not contains $url_hash $completed_hashes
                if test -f $status_file
                    set -l dl_status (cat $status_file)
                    tput el
                    if test "$dl_status" = "success"
                        echo "✅ [$url_hash] $short_url: Complete"
                    else
                        echo "❌ [$url_hash] $short_url: Failed"
                    end
                end
            end
        end

        echo ""
    end

    # Helper function to build format string
    function build_format_string -a url -a quality -a yt_dlp
        # If quality is "bestvideo+bestaudio/best" (default), just return it
        if test "$quality" = "bestvideo+bestaudio/best"
            echo "$quality"
            return
        end

        # Build format string: try exact height first, then fall back to closest below target
        switch $quality
            case 720
                echo "bestvideo[height=720]+bestaudio/best[height=720]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            case 1080
                echo "bestvideo[height=1080]+bestaudio/best[height=1080]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
            case 1440
                echo "bestvideo[height=1440]+bestaudio/best[height=1440]/bestvideo[height<=1440]+bestaudio/best[height<=1440]/best"
            case 2160
                echo "bestvideo[height=2160]+bestaudio/best[height=2160]/bestvideo[height<=2160]+bestaudio/best[height<=2160]/best"
        end
    end

    echo "Starting downloads with fast method (parallel processing)..."

    # TIER 1: Try fast method first (yt-dlp + axel, no impersonation)
    set -l fast_pids
    set -l fast_tmpdir (mktemp -d)
    set -l fast_url_map

    for url in $urls
        if string match -q "*://*" -- $url
            # Build format string based on video orientation
            set -l format_str (build_format_string "$url" "$quality_format" "$yt_dlp_path")

            # Create unique temp file for this download's status and log
            set -l url_hash (echo -n $url | md5sum | cut -d' ' -f1)
            set -l status_file "$fast_tmpdir/$url_hash.status"
            set -l log_file "$fast_tmpdir/$url_hash.log"

            # Store mapping for monitoring
            set -a fast_url_map "$url_hash|$url"

            # Fast method - axel with 16 connections (run in background)
            # Use stdbuf to force unbuffered output for real-time progress
            fish -c "
                if stdbuf -oL -eL $yt_dlp_path -f '$format_str' --no-abort-on-error --add-metadata --external-downloader axel --external-downloader-args '-n 16' '$url' > '$log_file' 2>&1
                    echo 'success' > '$status_file'
                else
                    echo 'failed' > '$status_file'
                end
            " &
            set -a fast_pids $last_pid
        end
    end

    # Monitor downloads with live progress
    if test (count $fast_pids) -gt 0
        monitor_downloads $fast_tmpdir $fast_pids $fast_url_map
    end

    # Collect failed URLs from status files
    for url in $urls
        set -l url_hash (echo -n $url | md5sum | cut -d' ' -f1)
        set -l status_file "$fast_tmpdir/$url_hash.status"
        if test -f $status_file
            if string match -q "failed" (cat $status_file)
                echo "Fast method failed for: $url"
                set -a fast_failed_urls $url
            else
                echo "Fast method succeeded for: $url"
            end
        else
            # No status file means something went wrong
            set -a fast_failed_urls $url
        end
    end

    # Cleanup temp directory
    rm -rf $fast_tmpdir
    
    # TIER 2: Try medium method for fast failures (yt-dlp + axel + impersonation)
    if test (count $fast_failed_urls) -gt 0
        echo ""
        echo "Retrying failed downloads with fast method + browser impersonation (parallel)..."
        echo "Failed URLs from fast method: "(count $fast_failed_urls)

        set -l medium_pids
        set -l medium_tmpdir (mktemp -d)
        set -l medium_url_map

        for url in $fast_failed_urls
            # Build format string based on video orientation
            set -l format_str (build_format_string "$url" "$quality_format" "$yt_dlp_path")

            # Create unique temp file for this download's status and log
            set -l url_hash (echo -n $url | md5sum | cut -d' ' -f1)
            set -l status_file "$medium_tmpdir/$url_hash.status"
            set -l log_file "$medium_tmpdir/$url_hash.log"

            # Store mapping for monitoring
            set -a medium_url_map "$url_hash|$url"

            # Medium method - axel + impersonation + cookies (run in background)
            # Use stdbuf to force unbuffered output for real-time progress
            fish -c "
                if stdbuf -oL -eL $yt_dlp_path -f '$format_str' \
                            --no-abort-on-error \
                            --add-metadata \
                            --external-downloader axel \
                            --external-downloader-args '-n 8' \
                            --impersonate 'Edge:Windows' \
                            --cookies-from-browser firefox \
                            '$url' > '$log_file' 2>&1
                    echo 'success' > '$status_file'
                else
                    echo 'failed' > '$status_file'
                end
            " &
            set -a medium_pids $last_pid
        end

        # Monitor downloads with live progress
        if test (count $medium_pids) -gt 0
            monitor_downloads $medium_tmpdir $medium_pids $medium_url_map
        end

        # Collect failed URLs from status files
        for url in $fast_failed_urls
            set -l url_hash (echo -n $url | md5sum | cut -d' ' -f1)
            set -l status_file "$medium_tmpdir/$url_hash.status"
            if test -f $status_file
                if string match -q "failed" (cat $status_file)
                    echo "Fast+impersonation method failed for: $url"
                    set -a medium_failed_urls $url
                else
                    echo "Fast+impersonation method succeeded for: $url"
                end
            else
                # No status file means something went wrong
                set -a medium_failed_urls $url
            end
        end

        # Cleanup temp directory
        rm -rf $medium_tmpdir
    end
    
    # TIER 3: Try slow method for remaining failures (yt-dlp built-in downloader)
    if test (count $medium_failed_urls) -gt 0
        echo ""
        echo "Retrying remaining failed downloads with slower method (parallel)..."
        echo "Failed URLs from medium method: "(count $medium_failed_urls)

        set -l slow_pids
        set -l slow_tmpdir (mktemp -d)
        set -l slow_url_map
        set -l final_failed_urls

        for url in $medium_failed_urls
            # Build format string based on video orientation
            set -l format_str (build_format_string "$url" "$quality_format" "$yt_dlp_path")

            # Create unique temp file for this download's status and log
            set -l url_hash (echo -n $url | md5sum | cut -d' ' -f1)
            set -l status_file "$slow_tmpdir/$url_hash.status"
            set -l log_file "$slow_tmpdir/$url_hash.log"

            # Store mapping for monitoring
            set -a slow_url_map "$url_hash|$url"

            # Slow method - yt-dlp built-in with all compatibility features (run in background)
            # Use stdbuf to force unbuffered output for real-time progress
            fish -c "
                if stdbuf -oL -eL $yt_dlp_path -f '$format_str' \
                            --concurrent-fragments 4 \
                            --no-abort-on-error \
                            --legacy-server-connect \
                            --add-metadata \
                            --no-check-certificates \
                            --impersonate 'Edge:Windows' \
                            --cookies-from-browser firefox \
                            --username '$SP_USER' \
                            --password '$SP_PASS' \
                            --socket-timeout 30 \
                            --retry-sleep linear=1::2 \
                            --fragment-retries 5 \
                            '$url' > '$log_file' 2>&1
                    echo 'success' > '$status_file'
                else
                    echo 'failed' > '$status_file'
                end
            " &
            set -a slow_pids $last_pid
        end

        # Monitor downloads with live progress
        if test (count $slow_pids) -gt 0
            monitor_downloads $slow_tmpdir $slow_pids $slow_url_map
        end

        # Collect results from status files
        for url in $medium_failed_urls
            set -l url_hash (echo -n $url | md5sum | cut -d' ' -f1)
            set -l status_file "$slow_tmpdir/$url_hash.status"
            if test -f $status_file
                if string match -q "failed" (cat $status_file)
                    echo "Slower method also failed for: $url"
                    set -a final_failed_urls $url
                else
                    echo "Slower method succeeded for: $url"
                end
            else
                # No status file means something went wrong
                echo "Slower method also failed for: $url"
                set -a final_failed_urls $url
            end
        end

        # Cleanup temp directory
        rm -rf $slow_tmpdir
    end
    
    # Summary
    echo ""
    if test (count $fast_failed_urls) -eq 0
        echo "✅ All downloads completed successfully with fast method!"
    else if test (count $medium_failed_urls) -eq 0
        echo "✅ All downloads completed! Some required browser impersonation."
        echo "📊 Download summary:"
        echo "  • Fast method: "(math (count $urls) - (count $fast_failed_urls))" successful"
        echo "  • Fast+impersonation method: "(count $fast_failed_urls)" successful"
    else
        set -l fast_success (math (count $urls) - (count $fast_failed_urls))
        set -l medium_success (math (count $fast_failed_urls) - (count $medium_failed_urls))
        set -l slow_success 0
        set -l total_failed 0

        if test (count $medium_failed_urls) -gt 0
            set slow_success (math (count $medium_failed_urls) - (count $final_failed_urls))
            set total_failed (count $final_failed_urls)
        end

        if test $total_failed -eq 0
            echo "✅ All downloads completed!"
        else
            echo "⚠️  Some downloads failed"
        end

        echo "📊 Download summary:"
        echo "  • Fast method: $fast_success successful"
        echo "  • Fast+impersonation method: $medium_success successful"

        if test (count $medium_failed_urls) -gt 0
            echo "  • Slow method: $slow_success successful"
        end

        if test $total_failed -gt 0
            echo "  • Failed completely: $total_failed"
            echo ""
            echo "Failed URLs:"
            for url in $final_failed_urls
                echo "  - $url"
            end
        end
    end
end
