# ~/.config/fish/conf.d/02_aliases.fish
# Aliases Configuration
# Core System
## Shell & Environment
alias rr='clear && exec fish'

## Backup Tools
alias bkup_all="bkup_packages; bkup_system; bkup_servers; bkup_buku"
alias bkup_buku="bash ~/.config/scripts/backup/run_buku_bkup.sh"
alias bkup_oldhp="bash ~/.config/scripts/backup/run_oldhp_bkup.sh"
alias bkup_packages="~/.config/scripts/backup/bkup_packages.py"
alias bkup_proxmox="bash ~/.config/scripts/backup/run_proxmox_bkup.sh"
alias bkup_servers="bash ~/.config/scripts/backup/run_oldhp_bkup.sh && bash ~/.config/scripts/backup/run_proxmox_bkup.sh"
alias bkup_system='~/.config/scripts/backup/snapshot_storage.py -s "backup_$(date +%Y%m%d_%H%M)"'

### DCLI
alias dcli="~/.config/scripts/shell/dcli_wrapper.py"

## Exa File Listing
alias ll="exa --all --color=always --icons --group-directories-first --git -Hah"
alias lll="exa --all --color=always --icons --group-directories-first --git -Hah -l -a"
alias llr="exa --color=always --icons --git -HahlTR"
alias llrl="exa --color=always --icons --git -HahlTR -L"
alias lls="exa --all --color=always --icons --group-directories-first --git -Hah -l -a -s size"

## Git Tools
alias delete_gone_branches="git branch -vv | awk '\$0 ~ /: gone]/ {print \$1;}' | xargs -r git branch -D"

## Media
alias cnn="~/scripts/secrets/launch_iptv.py --cnn"
alias zathura="zathura --fork --config-dir ~/.config/zathura"

## Monitoring
alias monitor_key_presses="stdbuf -oL wev | grep --line-buffered 'sym'"
alias monitor_keys_filtered="wev -f wl_pointer:motion -F wl_pointer:enter -F wl_pointer:leave -F wl_keyboard:enter -F wl_keyboard:leave -F wl_pointer:frame -F xdg_surface -F wl_data_offer -F wl_data_device -F xdg_toplevel"
alias monitor_keys_full="wev"
alias monitor_mouse_presses="wev -f wl_pointer:button"
alias monitor_windows="xprop"

## Notes & Text
alias note="notesh -f ~/notes/quick.json"

## Scripts
alias cgrid="python3 ~/.config/scripts/shell/color_grid.py"

## System Tools
alias code="code-insiders"
alias hyprland="Hyprland"
alias jless="fx"
alias mega="mega-cmd"
alias purge_script_logs='python3 ~/.config/scripts/shell/purge_script_logs.py'


## Video Download
alias sp_d="/home/rash/.local/bin/yt-dlp -f bestvideo+bestaudio/best -N 16 --no-abort-on-error --legacy-server-connect --add-metadata --no-check-certificates --impersonate Edge:Windows --cookies-from-browser firefox --username \$SP_USER --password \$SP_PASS"
alias yt_best="yt-dlp -f best"
alias yt_d="/home/rash/.local/bin/yt-dlp -f bestvideo+bestaudio/best --no-abort-on-error --add-metadata --external-downloader axel --external-downloader-args '-n 16'"
