function cargo_update_all --wraps="cargo install --list | grep '^[^ ]' | cut -d' ' -f1 | xargs -n1 cargo install --force" --description "alias cargo_update_all cargo install --list | grep '^[^ ]' | cut -d' ' -f1 | xargs -n1 cargo install --force"
  cargo install --list | grep '^[^ ]' | cut -d' ' -f1 | xargs -n1 cargo install --force $argv
        
end
