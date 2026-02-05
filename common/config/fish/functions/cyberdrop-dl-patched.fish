function cyberdrop-dl-patched --wraps=cyberdrop-dl-patched --description 'Wrapper for cyberdrop-dl-patched with dotfiles config'
    # Use config from dotfiles (symlinked), appdata in ~/.config/cyberdrop-dl/AppData
    command cyberdrop-dl-patched \
        --appdata-folder ~/.config/cyberdrop-dl/AppData \
        --config-file ~/.config/cyberdrop-dl/settings.yaml \
        $argv
end
