function bzen
    if test (count $argv) -eq 0
        vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --app=(bko --url)
        echo "Opening Buku Fuzzy Search"
    else
        switch $argv[1]
            case --help
                echo "Usage: bzen [OPTION] [INDEX/STRING/URL]"
                echo "Open a URL or a Buku bookmark in vivaldi Browser Zen Mode."
                echo
                echo "Options:"
                echo "  --help    Display this help message."
                echo "  --web     Open a URL or string as a URL."
                echo
                echo "Usage without --web:"
                echo "  - Without any argument: Opens Buku fuzzy search (fzf)."
                echo "  - With an index: Opens the Buku bookmark at the specified index in Zen mode."
                echo "  - With a string: Fuzzy searches Buku bookmarks and opens the first match for the string in Zen Mode."
                echo
                echo "Usage with --web:"
                echo "  - With a URL (http:// or https://): Opens the specified URL in Zen vivaldi."
                echo "  - With a string (not a URL): Treats the string as a URL, prefixes (https://) and opens it."
                echo
                echo "Examples:"
                echo
                echo "  bzen                             # Open Buku fuzzy search."
                echo "  bzen 1                           # Open the Buku bookmark at index 1."
                echo "  bzen string                      # Fuzzy search Buku bookmarks and open the first match for 'string'."
                echo "  bzen --web https://example.com   # Open 'https://example.com'."
                echo "  bzen --web example.com           # Open 'https://example.com'."
                return
            case --web
                set -l url $argv[2]
                if string match -q "https://*" "$url" || string match -q "http://*" "$url"
                    vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app="$url"
                    echo "Opening $url"
                else
                    vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app="https://$url"
                    echo "Opening https://$url"
                end
                return
            case '*'
                if string match -qr '^\d+$' $argv[1]
                    vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app=(bko --url "$argv[1]")
                    echo "Opening Buku index $argv[1]"
                else
                    vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app=(bko --url "$argv[1]")
                    echo "Opening Buku first match for string '$argv[1]'"
                end
        end
    end
end