function svtp --description "Browse and play SVT Play videos with fzf"
    set API_CONTENT "https://contento.svt.se/graphql"

    # Set mpv flags based on hostname
    set mpv_flags --really-quiet --no-terminal
    if test (hostname) = "linuxmini"
        set mpv_flags $mpv_flags --wayland-app-id=mpv-svtplay
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

    # If URL or search term provided, play directly
    if test (count $argv) -gt 0
        set input (string join " " $argv)

        # Check if it's already a full video URL (/video/...)
        if string match -q "http*" $input
            set url $input
            mpv $mpv_flags $url &; disown
            return 0
        else if string match -q "/video/*" $input
            set url "https://www.svtplay.se$input"
            mpv $mpv_flags $url &; disown
            return 0
        # For other paths or slugs, try to extract the actual video URL(s)
        else
            # Build the series/show page URL
            if string match -q "/*" $input
                set page_url "https://www.svtplay.se$input"
                set slug (echo $input | string replace "/" "")
            else
                set slug (string lower $input | string replace -a " " "-")
                set page_url "https://www.svtplay.se/$slug"
            end

            echo "Fetching from: $page_url" >&2

            # Fetch the page
            set page_content (curl -s "$page_url")

            # Extract all unique video URLs and filter by slug to avoid recommendations
            set video_urls (echo $page_content | grep -oP '"/video/[^"?]+' | string replace -a '"' '' | string replace -a '\\' '' | grep "/$slug" | sort -u)
            set video_count (echo $video_urls | wc -w)

            if test $video_count -eq 0
                echo "No videos found" >&2
                return 1
            else if test $video_count -eq 1
                # Single video - play directly
                set url "https://www.svtplay.se$video_urls"
                echo "Playing: $url" >&2
                mpv $mpv_flags $url &; disown
                return 0
            else
                # Multiple videos - it's a series, show in fzf
                echo "Found $video_count episodes" >&2

                # Create temp file with episodes
                set episodes_file (mktemp)

                # Extract episode titles and URLs
                for video_url in $video_urls
                    # Get the episode part from URL (last segment)
                    set episode_name (echo $video_url | awk -F'/' '{print $NF}' | string replace -a "-" " ")
                    echo "$episode_name\thttps://www.svtplay.se$video_url" >> $episodes_file
                end

                # Show in fzf
                set selected (cat $episodes_file | \
                    fzf --delimiter='\t' \
                        --with-nth=1 \
                        --preview 'echo {2}' \
                        --preview-window=down:3:wrap \
                        --prompt="Select episode > " \
                        --height=40%)

                rm -f $episodes_file

                if test -z "$selected"
                    echo "No episode selected" >&2
                    return 0
                end

                set url (echo $selected | awk -F '\t' '{print $NF}')
                echo "Playing: $url" >&2
                mpv $mpv_flags $url &; disown
                return 0
            end
        end
    end

    set tmpfile (mktemp)

    # Show main menu if no arguments
    echo "Loading menu..." >&2
    set menu_choice (printf "Popular\nCategories\nAll Content" | \
        fzf --prompt="Select > " \
            --height=40% \
            --header="SVT Play Browser")

    if test -z "$menu_choice"
        echo "No selection made" >&2
        rm -f $tmpfile
        return 0
    end

    # Handle menu choice
    switch $menu_choice
        case "Popular"
            echo "Fetching popular content..." >&2
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
                rm -f $tmpfile
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
        rm -f $tmpfile
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

    rm -f $tmpfile

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

    echo "Playing: $url" >&2
    mpv $mpv_flags $url &; disown
end
