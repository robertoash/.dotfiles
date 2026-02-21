#!/usr/bin/env bash
# Claude Code status line - TokyoNight Deep themed
# Layout: @domain  ~/path  branch  model  [bar]

DATA=$(cat)

# TokyoNight Deep palette (matching starship config)
TEAL=$'\e[38;2;139;255;255m'    # accent   #8bffff  - cwd, personal email
PURPLE=$'\e[38;2;213;166;255m'  # color13  #d5a6ff  - branch, work email
YELLOW=$'\e[38;2;230;193;0m'    # color3   #e6c100  - context warning
PINK=$'\e[38;2;255;95;143m'     # color9   #ff5f8f  - context critical
BLUE=$'\e[38;2;130;170;255m'    # color12  #82aaff  - model
DIM=$'\e[38;2;86;95;137m'
RESET=$'\e[0m'

BG_TEAL=$'\e[48;2;139;255;255m'
BG_YELLOW=$'\e[48;2;230;193;0m'
BG_PINK=$'\e[48;2;255;95;143m'
BG_EMPTY=$'\e[48;2;69;76;109m'
FG_DARK=$'\e[38;2;1;1;17m'
FG_LIGHT=$'\e[38;2;208;214;227m'

MODEL=$(echo "$DATA" | jq -r '.model.display_name // "?"' | tr '[:upper:] ' '[:lower:]-' | tr -s '-')
CTX_PCT=$(echo "$DATA" | jq -r '(.context_window.used_percentage // 0) | floor')
RAW_CWD=$(echo "$DATA" | jq -r '.cwd // "."')
EMAIL=$(jq -r '.oauthAccount.emailAddress // ""' ~/.claude.json 2>/dev/null)
BRANCH=$(git -C "$RAW_CWD" branch --show-current 2>/dev/null)

# @domain only (guard against empty email)
[[ -n "$EMAIL" ]] && EMAIL_DISPLAY="@${EMAIL#*@}" || EMAIL_DISPLAY=""

# Email color by domain
if [[ "$EMAIL" == *"@readly.com" ]]; then   EMAIL_COLOR="$PURPLE"
elif [[ "$EMAIL" == *"@gmail.com" ]]; then  EMAIL_COLOR="$TEAL"
else                                         EMAIL_COLOR="$RESET"
fi

# Collapse home, then cap at 3 levels: ~/a/b/c/d -> ~/.../d
if [[ "$RAW_CWD" == "$HOME"* ]]; then
    CWD="~${RAW_CWD#$HOME}"
else
    CWD="$RAW_CWD"
fi
IFS='/' read -ra _PARTS <<< "$CWD"
if (( ${#_PARTS[@]} > 4 )); then
    CWD="${_PARTS[0]}/.../${_PARTS[-1]}"
fi

# Progress bar (fixed width)
BAR_WIDTH=10
FILLED=$(( CTX_PCT * BAR_WIDTH / 100 ))

if (( CTX_PCT >= 90 )); then   BG_FILLED="$BG_PINK"
elif (( CTX_PCT >= 70 )); then BG_FILLED="$BG_YELLOW"
else                           BG_FILLED="$BG_TEAL"
fi

PCT_TEXT="${CTX_PCT}%"
PCT_LEN=${#PCT_TEXT}
LEFT_PAD=$(( (BAR_WIDTH - PCT_LEN) / 2 ))
RIGHT_PAD=$(( BAR_WIDTH - PCT_LEN - LEFT_PAD ))
BAR_CHARS="$(printf '%*s' "$LEFT_PAD" "")${PCT_TEXT}$(printf '%*s' "$RIGHT_PAD" "")"

COLOR_BAR=""
for ((i=0; i<BAR_WIDTH; i++)); do
    char="${BAR_CHARS:$i:1}"
    if (( i < FILLED )); then COLOR_BAR+="${BG_FILLED}${FG_DARK}${char}"
    else                       COLOR_BAR+="${BG_EMPTY}${FG_LIGHT}${char}"
    fi
done
COLOR_BAR+="${RESET}"

SEP="${DIM}::${RESET}"

LINE="${EMAIL_COLOR}${EMAIL_DISPLAY}${RESET}"
LINE+="${SEP}${TEAL}${CWD}${RESET}"
[[ -n "$BRANCH" ]] && LINE+="${SEP}${PURPLE} ${BRANCH}${RESET}"
LINE+="${SEP}${BLUE}${MODEL}${RESET}"
LINE+="${SEP}${COLOR_BAR}"

printf "%s\n" "$LINE"
