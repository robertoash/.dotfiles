brave_zen() {
  if [[ "$1" != https://* ]]; then
    brave --app="https://$1"
  else
    brave --app="$1"
  fi
}
