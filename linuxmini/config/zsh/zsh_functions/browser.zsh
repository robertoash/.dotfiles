b_zen() {
  if [ -z "$1" ]; then
      vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --app=$(bk_o --url)
      echo "Opening Buku Fuzzy Search"
  else
    case $1 in
      --help)
        echo "Usage: b_zen [OPTION] [INDEX/STRING/URL]"
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
        echo "  b_zen                             # Open Buku fuzzy search."
        echo "  b_zen 1                           # Open the Buku bookmark at index 1."
        echo "  b_zen string                      # Fuzzy search Buku bookmarks and open the first match for 'string'."
        echo "  b_zen --web https://example.com   # Open 'https://example.com'."
        echo "  b_zen --web example.com           # Open 'https://example.com'."
        return
        ;;
      --web)
        shift
        case $1 in
          https://*|http://*)
            vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app="$1"
            echo "Opening $1"
            return
            ;;
          *)
            vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app="https://$1"
            echo "Opening https://$1"
            return
            ;;
        esac
        ;;
      [0-9]*)
        vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app=$(bk_o --url "$1")
        echo "Opening Buku index $1"
        return
        ;;
      *)
        vivaldi --enable-features=UseOzonePlatform --ozone-platform=wayland --profile-directory="app_profile" --app=$(bk_o --url "$1")
        echo "Opening Buku first match for string '$1'"
        return
        ;;
    esac
  fi
}

no_paywall() {
  local paywall_url="https://www.removepaywall.com/search?url=$1"
  echo "Opening $paywall_url on qutebrowser"
  qute_profile rash "$paywall_url"
}
