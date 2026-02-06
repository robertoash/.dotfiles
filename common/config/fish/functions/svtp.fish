function svtp --description "Browse and play SVT Play videos with fzf"
    set API_CONTENT "https://contento.svt.se/graphql"

    # Check for debug flag
    set debug_mode 0
    if contains -- --debug $argv
        set debug_mode 1
        set argv (string match -v -- --debug $argv)
    end

    # Set mpv flags based on hostname and debug mode
    if test $debug_mode -eq 1
        set mpv_flags
    else
        set mpv_flags --really-quiet --no-terminal
    end
    if test (hostname) = "linuxmini"
        set mpv_flags $mpv_flags --wayland-app-id=mpv-svtplay
    end

    # Helper function to play a video URL (handles live streams via SVT API)
    function _play_video
        set url $argv[1]
        set debug $argv[2]
        set flags $argv[3..-1]

        # Extract video ID from URL
        set video_id (echo $url | grep -oP '/video/\K[^/]+')

        if test -n "$video_id"
            # Check SVT API for stream info
            echo "Checking stream info..." >&2
            set api_response (curl -s "https://api.svt.se/videoplayer-api/video/$video_id")
            set is_live (echo $api_response | jq -r '.live // false')

            if test "$is_live" = "true"
                # Live stream - get HLS URL from API (not cmaf)
                set hls_url (echo $api_response | jq -r '.videoReferences[] | select(.format == "hls") | .url')

                if test -n "$hls_url"
                    # Verify the URL is accessible before handing to mpv
                    if curl -sf "$hls_url" >/dev/null 2>&1
                        echo "Starting live stream..." >&2
                        if test "$debug" = "1"
                            mpv $flags "$hls_url"
                        else
                            mpv $flags "$hls_url" &
                            disown
                            if not hypr-window-ops window-wait --pid $last_pid
                                echo "svtp: Playback failed. Run with --debug for details." >&2
                                return 1
                            end
                        end
                        return 0
                    else
                        echo "Live stream URL unavailable, falling back to yt-dlp..." >&2
                    end
                end
            end
        end

        # Not a live stream or couldn't get HLS URL - use yt-dlp via mpv
        echo "Starting playback..." >&2
        if test "$debug" = "1"
            mpv $flags $url
        else
            mpv $flags $url &
            disown
            if not hypr-window-ops window-wait --pid $last_pid
                echo "svtp: Playback failed. Run with --debug for details." >&2
                return 1
            end
        end
        return 0
    end

    # Function to fetch all selections from startForSvtPlay
    function _get_selections
        echo '{"query":"{startForSvtPlay{selections{id name}}}"}' | \
            curl -s -X POST "https://contento.svt.se/graphql" \
                -H "Content-Type: application/json" \
                -d @- | \
                jq -r '.data.startForSvtPlay.selections[] | "\(.id)\t\(.name)"'
    end

    # Function to fetch content from a specific selection
    function _get_content_from_selection
        set selection_id $argv[1]

        printf '%s' "{\"query\":\"{selectionById(id:\\\"$selection_id\\\"){items{item{__typename...on TvSeries{id name longDescription urls{svtplay}}...on Episode{id name longDescription parent{name} urls{svtplay}}...on Single{id name longDescription urls{svtplay}}...on TvShow{id name longDescription urls{svtplay}}...on KidsTvShow{id name longDescription urls{svtplay}}}}}}\"}" | \
            curl -s -X POST "https://contento.svt.se/graphql" \
                -H "Content-Type: application/json" \
                -d @- | \
            jq -r '.data.selectionById.items[].item | select(.urls.svtplay) | if .parent then "\(.parent.name) - \(.name)\t\(.longDescription[0:100] // "")\thttps://www.svtplay.se\(.urls.svtplay)" else "\(.name // "No title")\t\(.longDescription[0:100] // "")\thttps://www.svtplay.se\(.urls.svtplay)" end'
    end

    # Function to fetch ALL content from ALL selections (most comprehensive)
    function _get_all_content
        echo '{"query":"{startForSvtPlay{selections{items{item{__typename...on TvSeries{name longDescription urls{svtplay}}...on TvShow{name longDescription urls{svtplay}}...on Episode{name longDescription urls{svtplay}}...on Single{name longDescription urls{svtplay}}...on KidsTvShow{name longDescription urls{svtplay}}}}}}}"}' | \
            curl -s -X POST "https://contento.svt.se/graphql" \
                -H "Content-Type: application/json" \
                -d @- | \
            jq -r '.data.startForSvtPlay.selections[].items[].item | select(.urls) | "\(.name)\t\(.longDescription[0:150] // "")\thttps://www.svtplay.se\(.urls.svtplay)"'
    end

    # Function to search for content by keyword
    function _search_content
        set search_term $argv[1]
        echo '{"query":"{searchPage(query:\"'$search_term'\",maxHits:100){flat{hits{teaser{name description item{urls{svtplay}}}categoryTeaser{heading slug}}}}}"}' | \
            curl -s -X POST "https://contento.svt.se/graphql" \
                -H "Content-Type: application/json" \
                -d @- | \
            jq -r '.data.searchPage.flat.hits[] | if .teaser then .teaser | select(.item.urls.svtplay) | "\(.name)\t\(.description[0:100] // "")\thttps://www.svtplay.se\(.item.urls.svtplay)" elif .categoryTeaser then .categoryTeaser | "\(.heading | gsub("<em>|</em>";"";"g"))\t[Category]\thttps://www.svtplay.se/\(.slug)" else empty end'
    end

    # If URL or search term provided, play directly
    if test (count $argv) -gt 0
        set input (string join " " $argv)

        # Check if it's already a full video URL (/video/...)
        if string match -q "http*" -- $input
            set url $input
        else if string match -q "/video/*" -- $input
            set url "https://www.svtplay.se$input"
        else
            set url ""
        end

        # If we have a direct video URL, play it
        if test -n "$url"
            _play_video $url $debug_mode $mpv_flags
            return 0
        end

        # Search for content using the SVT API
        echo "Searching for: $input" >&2
        set tmpfile (mktemp)
        _search_content "$input" > $tmpfile

        if test ! -s $tmpfile
            echo "No results found for '$input'" >&2
            command rm -f $tmpfile
            return 1
        end

        set result_count (wc -l < $tmpfile)

        if test $result_count -eq 1
            # Single result - play directly
            set url (cat $tmpfile | awk -F '\t' '{print $NF}')
            command rm -f $tmpfile
            _play_video $url $debug_mode $mpv_flags
            return 0
        else
            # Multiple results - show in fzf
            echo "Found $result_count results" >&2
            set selected (cat $tmpfile | \
                fzf --delimiter='\t' \
                    --with-nth=1 \
                    --preview 'echo {2}; echo; echo {3}' \
                    --preview-window=down:3:wrap \
                    --prompt="Select > " \
                    --height=40%)

            command rm -f $tmpfile

            if test -z "$selected"
                echo "No selection made" >&2
                return 0
            end

            set url (echo $selected | awk -F '\t' '{print $NF}')
            _play_video $url $debug_mode $mpv_flags
            return 0
        end
    end

    set tmpfile (mktemp)

    # Show main menu if no arguments
    echo "Loading menu..." >&2
    set menu_choice (printf "Editor's Pick\nCategories\nAll Content" | \
        fzf --prompt="Select > " \
            --height=40% \
            --header="SVT Play Browser")

    if test -z "$menu_choice"
        echo "No selection made" >&2
        command rm -f $tmpfile
        return 0
    end

    # Handle menu choice
    switch $menu_choice
        case "Editor's Pick"
            echo "Fetching editor's picks..." >&2
            # Fetch from the "Populärt" (popular_start) selection
            _get_content_from_selection "popular_start" | sort -u > $tmpfile

        case "Categories"
            # Show category submenu
            echo "Loading categories..." >&2
            set category (_get_selections | \
                fzf --delimiter='\t' \
                    --with-nth=2 \
                    --prompt="Select category > " \
                    --height=40%)

            if test -z "$category"
                echo "No category selected" >&2
                command rm -f $tmpfile
                return 0
            end

            set selection_id (echo $category | cut -f1)
            set selection_name (echo $category | cut -f2)
            echo "Fetching content from $selection_name..." >&2
            _get_content_from_selection $selection_id | sort -u > $tmpfile

        case "All Content"
            echo "Fetching all available content (this may take a moment)..." >&2
            _get_all_content | sort -u > $tmpfile
    end

    if test ! -s $tmpfile
        echo "No results found" >&2
        command rm -f $tmpfile
        return 1
    end

    # Use fzf to select content
    set selected (cat $tmpfile | \
        fzf --delimiter='\t' \
            --with-nth=1 \
            --preview 'echo {2}; echo; echo {3}' \
            --preview-window=down:3:wrap \
            --prompt="Select video > " \
            --height=40%)

    command rm -f $tmpfile

    if test -z "$selected"
        echo "No selection made" >&2
        return 0
    end

    # Extract URL and play in mpv
    set url (echo $selected | awk -F '\t' '{print $NF}')

    if test -z "$url"
        echo "Could not extract URL" >&2
        return 1
    end

    _play_video $url $debug_mode $mpv_flags
end
