#!/usr/bin/env bash
# Claude Code status line - TokyoNight Deep themed
# Layout: [email left] [cwd / branch / model evenly spread] [bar right]

DATA=$(cat)

# TokyoNight Deep palette (matching starship config)
TEAL=$'\e[38;2;139;255;255m'    # accent   #8bffff  - cwd, personal email
PURPLE=$'\e[38;2;213;166;255m'  # color13  #d5a6ff  - branch, work email
YELLOW=$'\e[38;2;230;193;0m'    # color3   #e6c100  - context warning
PINK=$'\e[38;2;255;95;143m'     # color9   #ff5f8f  - context critical
BLUE=$'\e[38;2;130;170;255m'    # color12  #82aaff  - model
RESET=$'\e[0m'

BG_TEAL=$'\e[48;2;139;255;255m'
BG_YELLOW=$'\e[48;2;230;193;0m'
BG_PINK=$'\e[48;2;255;95;143m'
BG_EMPTY=$'\e[48;2;69;76;109m'
FG_DARK=$'\e[38;2;1;1;17m'
FG_LIGHT=$'\e[38;2;208;214;227m'

MODEL=$(echo "$DATA" | jq -r '.model.display_name // "?"')
CTX_PCT=$(echo "$DATA" | jq -r '(.context_window.used_percentage // 0) | floor')
RAW_CWD=$(echo "$DATA" | jq -r '.cwd // "."')
CWD="${RAW_CWD/#$HOME/~}"
BRANCH=$(git -C "$RAW_CWD" branch --show-current 2>/dev/null)
EMAIL=$(jq -r '.oauthAccount.emailAddress // ""' ~/.claude.json 2>/dev/null)

# Email color by domain
if [[ "$EMAIL" == *"@readly.com" ]]; then   EMAIL_COLOR="$PURPLE"
elif [[ "$EMAIL" == *"@gmail.com" ]]; then  EMAIL_COLOR="$TEAL"
else                                         EMAIL_COLOR="$RESET"
fi

# Get terminal width
WIDTH=$(python3 -c "
import fcntl, termios, struct
for fd in range(3):
    try:
        _, w = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, b'\0'*4))
        if w > 0:
            print(w + 2); exit()
    except: pass
print(${COLUMNS:-$(tput cols 2>/dev/null || echo 120)} + 2)
")

# Non-bar parts
NON_BAR_PLAIN=()
NON_BAR_COLOR=()
NON_BAR_PLAIN+=("$EMAIL");  NON_BAR_COLOR+=("${EMAIL_COLOR}${EMAIL}${RESET}")
NON_BAR_PLAIN+=("$CWD");    NON_BAR_COLOR+=("${TEAL}${CWD}${RESET}")
[[ -n "$BRANCH" ]] && { NON_BAR_PLAIN+=(" $BRANCH"); NON_BAR_COLOR+=("${PURPLE} ${BRANCH}${RESET}"); }
NON_BAR_PLAIN+=("$MODEL");  NON_BAR_COLOR+=("${BLUE}${MODEL}${RESET}")

# Compute non-bar total width
NON_BAR_W_STR=$(printf '%s\n' "${NON_BAR_PLAIN[@]}" | python3 -c "
import unicodedata, sys
def w(s):
    return sum(2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in s)
parts = sys.stdin.read().rstrip('\n').split('\n')
print(sum(w(p) for p in parts))
")
NON_BAR_W=$NON_BAR_W_STR

# N_GAPS = gaps between all elements including bar (N_PARTS - 1)
N_GAPS=$(( ${#NON_BAR_PLAIN[@]} ))  # non-bar parts count = N_GAPS since bar adds 1 more part

# Choose BAR_WIDTH so (WIDTH - NON_BAR_W - BAR_WIDTH) is exactly divisible by N_GAPS
BASE_BAR=12
AVAIL_BASE=$(( WIDTH - NON_BAR_W - BASE_BAR ))
EXTRA=$(( AVAIL_BASE % N_GAPS ))
TRIM=$(( (N_GAPS - EXTRA) % N_GAPS ))
BAR_WIDTH=$(( BASE_BAR - TRIM ))

# Build progress bar at final BAR_WIDTH
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

# Assemble all parts and compute equal gap
PARTS_COLOR=("${NON_BAR_COLOR[@]}" "$COLOR_BAR")
AVAIL=$(( WIDTH - NON_BAR_W - BAR_WIDTH ))
GAP=$(( AVAIL / N_GAPS ))

LINE=""
N=${#PARTS_COLOR[@]}
for ((i=0; i<N; i++)); do
    LINE+="${PARTS_COLOR[$i]}"
    (( i < N - 1 )) && printf -v gap '%*s' "$GAP" "" && LINE+="$gap"
done

printf "%s\n" "$LINE"
