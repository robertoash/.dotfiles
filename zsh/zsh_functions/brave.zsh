brave_zen() {
  if [ -z "$1" ]; then
      brave --app=$(bk_o --url)
      echo "Opening Buku Fuzzy Search"
  else
    case $1 in
      --buku)
        shift
        if [ -z "$1" ]; then
            brave --app=$(bk_o --url)
            echo "Opening Buku Fuzzy Search"
        else
            brave --app=$(bk_o --url "$1")
            echo "Opening Buku index $1"
        fi
        return
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
