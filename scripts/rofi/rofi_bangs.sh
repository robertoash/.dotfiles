#!/usr/bin/env bash
# author: unknown
# sentby: MoreChannelNoise (https://www.youtube.com/user/MoreChannelNoise)
# editby: gotbletu (https://www.youtube.com/user/gotbletu)

# info: this is a script to launch other rofi scripts,
#       saves us the trouble of binding multiple hotkeys for each script,
#       when we can just use one hotkey for everything.

declare -A LABELS
declare -A COMMANDS

###
# List of defined 'bangs'

# launch apps
COMMANDS["apps"]="~/.config/scripts/rofi/rofi_drun.sh"
LABELS["apps"]=""

# search local files
COMMANDS["locate"]="~/.config/scripts/rofi/rofi_locate.sh"
LABELS["locate"]=""

# get keybinds
COMMANDS["keybinds"]="~/.config/scripts/rofi/rofi_hyprkeys.sh"
LABELS["keybinds"]=""

# get zsh aliases
COMMANDS["zsh_aliases"]="~/.config/scripts/rofi/rofi_zsh_aliases.sh"
LABELS["zsh_aliases"]=""

# get offline media size
COMMANDS["media_size"]="~/.config/scripts/rofi/rofi_media_size.sh"
LABELS["media_size"]=""

# mullvad
COMMANDS["mullvad"]="~/.config/scripts/rofi/rofi_mullvad.sh"
LABELS["mullvad"]=""

# calc
COMMANDS["calc"]="~/.config/scripts/rofi/rofi_calc.sh"
LABELS["calc"]=""

# shutdown
COMMANDS["shutdown"]="~/.config/scripts/rofi/rofi_shutdown.sh"
LABELS["shutdown"]=""

# show clipboard history
# source: https://bitbucket.org/pandozer/rofi-clipboard-manager/overview
# COMMANDS["clipboard"]='rofi -modi "clipboard:~/.bin/rofi-clipboard-manager/mclip.py menu" -show clipboard && ~/.bin/rofi-clipboard-manager/mclip.py paste'
# LABELS["clipboard"]=""

# references --------------------------
# COMMANDS[";sr2"]="chromium 'wikipedia.org/search-redirect.php?search=\" \${input}\""
# LABELS[";sr2"]=""

# COMMANDS[";piratebay"]="chromium --disk-cache-dir=/tmp/cache http://thepiratebay.org/search/\" \${input}\""
# LABELS[";piratebay"]=""

# COMMANDS[".bin"]="spacefm -r '/home/dka/bin'"
# LABELS[".bin"]=".bin"

################################################################################
# main script (don't touch below)
################################################################################

# Generate menu
function print_menu()
{
    for key in ${!LABELS[@]}
    do
        echo "$key"
        # echo "$key    ${LABELS[$key]}"
    done
}

# Show rofi
function start()
{
    # print_menu | rofi -dmenu -p "?=>"
    print_menu | sort | rofi show run -dmenu -i -p "launch rofi script: "
}

# Run it
value="$(start)"

# Split input.
choice=${value%%\ *} # grab upto first space.
input=${value:$((${#choice}+1))} # graph remainder, minus space.

# Cancelled? bail out
if test -z ${choice}
then
    exit
fi

# check if choice exists
if test ${COMMANDS[$choice]+isset}
then
    # Execute the choice
    eval echo "Executing: ${COMMANDS[$choice]}"
    eval ${COMMANDS[$choice]}
else
    eval  $choice | rofi
    # prefer my above so I can use this same script to also launch apps like geany or leafpad etc (DK)
    # echo "Unknown command: ${choice}" | rofi -dmenu -p "error"
fi
