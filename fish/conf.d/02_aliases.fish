# ~/.config/fish/conf.d/02_aliases.fish
# Aliases Configuration

# Core System
## Shell & Environment
alias free_space="lsblk -o NAME,SIZE,FSAVAIL,MOUNTPOINT"
alias reset="reset && neofetch"
alias rr='clear && exec fish'
alias sudo="sudo "
alias fish_reload="source ~/.config/fish/config.fish"
alias snk_here="snake_case_all ."

## Package Management
alias yay_total="yay -Syu --devel"
alias yay_update="yayupdate"

# Applications
## Atuin
alias atuin_clean="atuin history prune"

## Backup Tools
alias bkup_all="bkup_packages; bkup_system; bkup_servers; bkup_buku"
alias bkup_buku="bash ~/.config/scripts/backup/run_buku_bkup.sh"
alias bkup_oldhp="bash ~/.config/scripts/backup/run_oldhp_bkup.sh"
alias bkup_packages="~/.config/scripts/backup/bkup_packages.py"
alias bkup_proxmox="bash ~/.config/scripts/backup/run_proxmox_bkup.sh"
alias bkup_servers="bash ~/.config/scripts/backup/run_oldhp_bkup.sh && bash ~/.config/scripts/backup/run_proxmox_bkup.sh"
alias bkup_system='~/.config/scripts/backup/snapshot_storage.py -s "backup_$(date +%Y%m%d_%H%M)"'

## Buku Bookmarks
alias bk="buku --suggest"
alias bka="bk -w" # Buku add (interactive)
alias bkd="bk -d" # Buku delete
alias bke="bk -w"
alias bkl="bk -p" # Buku list
alias bkll="bk -l" # Buku lock
alias bklu="bk -k" # Buku unlock
alias bko="bk_o" # Buku with fzf
alias bks="bk --np -s" # Buku search (no prompt)
alias bksp="bk -s" # Buku search (prompt)
alias bkw="bk -w --tag ''" # Buku write

### Buku Database Functions
alias bk_c="switch_buku_db current"
alias bk_p="switch_buku_db rashp"
alias bk_r="switch_buku_db rash"
alias bk_s="switch_buku_db"

### DCLI
alias dcli="~/.config/scripts/shell/dcli_wrapper.py"

### SGPT
alias gs="sgpt -s --no-interaction"
alias gsi="sgpt -s --interaction"
alias gd="sgpt -d"
alias gtc="sgpt -c"

## Docker
alias drdp="bash ~/.config/scripts/docker/docker_redeploy_container.sh"
alias dsp="bash ~/.config/scripts/docker/docker_simple.sh"

## Dust
alias dust="dust -r"

## Exa File Listing
alias ll="exa --all --color=always --icons --group-directories-first --git -Hah"
alias lll="ll -l -a"
alias llr="exa --color=always --icons --git -HahlTR"
alias llrl="llr -L"
alias lls="lll -s size"

## File Management
alias yz="yazi"

## Git Tools
alias delete_gone_branches="git branch -vv | awk '\$0 ~ /: gone]/ {print \$1;}' | xargs -r git branch -D"
alias lg="lazygit"
alias lzd="lazydocker"

## Media
alias cnn="~/scripts/secrets/launch_iptv.py --cnn"
alias zathura="zathura --fork --config-dir ~/.config/zathura"

## Monitoring
alias monitor_key_presses="stdbuf -oL wev | grep --line-buffered 'sym'"
alias monitor_keys_filtered="wev -f wl_pointer:motion -F wl_pointer:enter -F wl_pointer:leave -F wl_keyboard:enter -F wl_keyboard:leave -F wl_pointer:frame -F xdg_surface -F wl_data_offer -F wl_data_device -F xdg_toplevel"
alias monitor_keys_full="wev"
alias monitor_mouse_presses="wev -f wl_pointer:button"
alias monitor_windows="xprop"

## Mullvad VPN
alias mcon="mullvad connect"
alias mdis="mullvad disconnect"
alias mst="mullvad status"

## Notes & Text
alias note="notesh -f ~/notes/quick.json"

## Rsync
alias rs='rsync -ah --itemize-changes --partial --progress --stats'
alias rsdry='rsync -ah --itemize-changes --progress --stats --dry-run'
alias rsmv='rsync -ah --progress --stats --remove-source-files'

## Server
alias iptvparse='ssh root@dockerlab "python3 /root/dev/setup_files/iptv_server/iptv_m3u_gen.py"'

## SVT Text
alias svtti="svttext -colors -interactive"
alias svttc="svttext -colors"
alias svttci="svtti"
alias svttic="svtti"

# Gcalcli
alias "gcal"="gcalcli"
alias "gcal_a"="gcal agenda"

## Scripts
alias cgrid="python3 ~/.config/scripts/shell/color_grid.py"

## Spotify_player
alias spt="spotify_player"

## System Tools
alias code="code-insiders"
alias hyprland="Hyprland"
alias jless="fx"
alias mega="mega-cmd"
alias purge_script_logs='python3 ~/.config/scripts/shell/purge_script_logs.py'
alias xeyes="xprop"

## Video Download
alias sp_d="/home/rash/.local/bin/yt-dlp -f bestvideo+bestaudio/best -N 16 --no-abort-on-error --legacy-server-connect --add-metadata --no-check-certificates --impersonate Edge:Windows --cookies-from-browser firefox --username \$SP_USER --password \$SP_PASS"
alias yt_best="yt-dlp -f best"
alias yt_d="/home/rash/.local/bin/yt-dlp -f bestvideo+bestaudio/best --no-abort-on-error --add-metadata --external-downloader axel --external-downloader-args '-n 16'"
