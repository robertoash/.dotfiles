# Function to switch the database symlink
switch_buku_db() {
    local db_name="$1"
    ln -sf "$HOME/.local/share/buku/${db_name}.db" "$HOME/.local/share/buku/bookmarks.db"
    echo "Switched Buku database to: $HOME/.local/share/buku/${db_name}.db"
}