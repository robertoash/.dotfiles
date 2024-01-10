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
COMMANDS["apps"]="~/.config/rofi/scripts/rofi_drun.sh"
LABELS["apps"]=""

# search local files
COMMANDS["locate"]="~/.config/rofi/scripts/rofi_locate.sh"
LABELS["locate"]=""

# get keybinds
COMMANDS["keybinds"]="~/.config/rofi/scripts/rofi_hyprkeys.sh"
LABELS["keybinds"]=""

# get offline media size
COMMANDS["media_size"]="~/.config/rofi/scripts/rofi_media_size.sh"
LABELS["media_size"]=""

# mullvad
COMMANDS["mullvad"]="~/.config/rofi/scripts/rofi_mullvad.sh"
LABELS["mullvad"]=""

# calc
COMMANDS["calc"]="~/.config/rofi/scripts/rofi_calc.sh"
LABELS["calc"]=""

# open custom web searches
# COMMANDS["websearch"]="~/.scripts/rofi-surfraw-websearch.sh"
# LABELS["websearch"]=""

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

# COMMANDS["#screenshot"]='/home/dka/bin/screenshot-scripts/myscreenshot.sh'
# LABELS["#screenshot"]="screenshot"

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
    print_menu | sort | rofi show run -dmenu -mesg ">>> launch rofi scripts" -i -p "select: "
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
