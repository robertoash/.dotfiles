# SGPT shell integration
_sgpt_zsh() {
if [[ -n "$BUFFER" ]]; then
    _sgpt_prev_cmd=$BUFFER
    BUFFER+="⌛"
    zle -I && zle redisplay
    BUFFER=$(sgpt --shell <<< "$_sgpt_prev_cmd" --no-interaction)
    zle end-of-line
fi
}
zle -N _sgpt_zsh

qs() {
  local input="$*"
  sgpt -s "$input"
}

qx() {
  local input="$*"
  sgpt -d "$input"
}

sgpt() {
    case "$1" in
        commit)
            shift # Remove 'commit' from the arguments

            local TEMP_FILE=$(mktemp)
            # Ensure the temp file is removed upon exit
            trap "rm -f '$TEMP_FILE'" EXIT

            # Generate the commit message and save it to TEMP_FILE
            git diff --cached | sgpt "Create a concise commit message. Just facts without embellishment" > "$TEMP_FILE"

            # Trim all leading and trailing newlines
            awk 'BEGIN {RS=""; FS="\n"} {gsub(/^\n+|\n+$/, ""); print}' "$TEMP_FILE" > "$TEMP_FILE.tmp" && mv "$TEMP_FILE.tmp" "$TEMP_FILE"

            # Open the editor
            ${EDITOR:-nano} "$TEMP_FILE"

            # After editing, prompt the user for confirmation
            echo "Do you want to proceed with the commit? [y/n]"
            read -r user_input

            case "$user_input" in
                y|Y)
                    if [ -s "$TEMP_FILE" ]; then  # Check if file is not empty
                        git commit -F "$TEMP_FILE"
                    else
                        echo "Commit message is empty. Aborting commit."
                    fi
                    ;;
                *)
                    echo "Commit aborted by user."
                    ;;
            esac
            ;;
        pr)
            case "$2" in
                create)
                    local DRAFT_FLAG=""
                    local TEMP_FILE=$(mktemp)
                    trap "rm -f '$TEMP_FILE'" EXIT

                    # Check for --draft argument
                    if [[ " $* " =~ " --draft " ]]; then
                        DRAFT_FLAG="--draft"
                    fi

                    # Generate diff against origin/main and save to a temp file.
                    git diff origin/main . > "$TEMP_FILE"

                    # Pass the diff to sgpt with an appropriate prompt.
                    sgpt "Create a PR title and description based on the following changes:" < "$TEMP_FILE" > "$TEMP_FILE.msg"

                    # Open the message in the editor for review and confirmation.
                    ${EDITOR:-nano} "$TEMP_FILE.msg"

                    # User confirmation before proceeding.
                    echo "Do you want to proceed with PR creation? [y/n]"
                    read -r user_input

                    if [[ "$user_input" =~ ^[Yy]$ ]]; then
                        # Extract title and body for the PR from the temp file.
                        # Assuming first line is title, rest is body.
                        local PR_TITLE=$(head -n 1 "$TEMP_FILE.msg")
                        local PR_BODY=$(tail -n +2 "$TEMP_FILE.msg")

                        # Create the PR and capture the URL.
                        local PR_URL=$(gh pr create --title "$PR_TITLE" --body "$PR_BODY" $DRAFT_FLAG --web)

                        echo "PR created and browser opened: $PR_URL"
                    else
                        echo "PR creation aborted."
                    fi
                    ;;

                review)
                    # Assuming the use of 'gh' to fetch the URL of the latest PR for the current branch.
                    local PR_URL=$(gh pr view --json url -q .url)

                    if [ -z "$PR_URL" ]; then
                        echo "No PR found for the current branch."
                        return
                    fi

                    # Fetching the diff of the latest PR and passing it to sgpt for review.
                    gh pr diff $(gh pr view --json number -q .number) | sgpt "Review the following PR changes:" > "$TEMP_FILE"

                    # Display the AI-enhanced review to stdout.
                    cat "$TEMP_FILE"
                    ;;

                *)
                    echo "Unsupported pr command: $2"
                    ;;
            esac
            ;;

        *)
            # Delegate all other commands to the original sgpt application
            command sgpt "$@"
            ;;
    esac
}
