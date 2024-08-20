b_zen() {
  if [ -z "$1" ]; then
      brave --app=$(bk_o --url)
      echo "Opening Buku Fuzzy Search"
  else
    case $1 in
      --help)
        echo "Usage: brave_zen [OPTION] [INDEX/STRING/URL]"
        echo "Open a URL or a Buku bookmark in Brave Browser Zen Mode."
        echo
        echo "Options:"
        echo "  --help    Display this help message."
        echo "  --buku    Open Zen Buku Bookmarks."
        echo
        echo "Usage without --buku:"
        echo "  - Without any argument: Opens Buku fuzzy search (fzf)."
        echo "  - With a URL (http:// or https://): Opens the specified URL in Zen Brave."
        echo "  - With a string (not a URL): Treats the string as a URL, prefixes (https://) and opens it."
        echo
        echo "Usage with --buku:"
        echo "  - Without any argument: Opens Buku fuzzy search (fzf)."
        echo "  - With an index: Opens the Buku bookmark at the specified index."
        echo "  - With a string: Fuzzy searches Buku bookmarks and opens the first match for the string."        echo "Examples:"
        echo
        echo "  brave_zen                     # Open Buku fuzzy search."
        echo "  brave_zen --buku              # Open Buku fuzzy search."
        echo "  brave_zen --buku 1            # Open the Buku bookmark at index 1."
        echo "  brave_zen 1                   # Open the Buku bookmark at index 1."
        echo "  brave_zen --buku string       # Fuzzy search Buku bookmarks and open the first match for 'string'."
        echo "  brave_zen https://example.com # Open 'https://example.com'."
        echo "  brave_zen example.com         # Open 'https://example.com'."
        return
        ;;
      --buku)
        shift
        if [ -z "$1" ]; then
            brave --app=$(bk_o --url)
            echo "Opening Buku Fuzzy Search"
        else
            brave --app=$(bk_o --url "$1")
            case $1 in
              [0-9]*)
                echo "Opening Buku index $1"
                return
                ;;
              *)
                echo "Opening Buku first match for string '$1'"
                return
                ;;
            esac
        fi
        ;;
      [0-9]*)
        brave --app=$(bk_o --url "$1")
        echo "Opening Buku index $1"
        return
        ;;
      https://*|http://*)
        brave --app="$1"
        echo "Opening $1"
        return
        ;;
      *)
        brave --app="https://$1"
        echo "Opening https://$1"
        return
        ;;
    esac
  fi
}
