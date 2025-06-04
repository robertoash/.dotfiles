# SGPT shell integration
function _sgpt_zsh
    if test -n "$BUFFER"
        set _sgpt_prev_cmd $BUFFER
        set BUFFER "$BUFFER⌛"
        # Note: zle commands don't exist in fish, this would need different implementation
        set BUFFER (echo "$_sgpt_prev_cmd" | sgpt --shell --no-interaction)
    end
end

function qs
  set -l input $argv
  sgpt -s $input
end

function qx
  set -l input $argv
  sgpt -d $input
end

function sgpt
    switch $argv[1]
        case commit
            set -e argv[1] # Remove 'commit' from the arguments

            set -l TEMP_FILE (mktemp)
            # Ensure the temp file is removed upon exit
            trap "rm -f '$TEMP_FILE'" EXIT

            # Generate the commit message and save it to TEMP_FILE
            git diff --cached | sgpt "Create a concise commit message. Just facts without embellishment" > $TEMP_FILE

            # Trim all leading and trailing newlines
            awk 'BEGIN {RS=""; FS="\n"} {gsub(/^\n+|\n+$/, ""); print}' $TEMP_FILE > $TEMP_FILE.tmp && mv $TEMP_FILE.tmp $TEMP_FILE

            # Open the editor
            eval $EDITOR $TEMP_FILE

            # After editing, prompt the user for confirmation
            echo "Do you want to proceed with the commit? (y/n)"
            read -l user_input

            switch $user_input
                case y Y
                    if test -s $TEMP_FILE   # Check if file is not empty
                        git commit -F $TEMP_FILE
                    else
                        echo "Commit message is empty. Aborting commit."
                    end
                case '*'
                    echo "Commit aborted by user."
            end

        case pr
            switch $argv[2]
                case create
                    set -l DRAFT_FLAG ""
                    set -l TEMP_FILE (mktemp)
                    trap "rm -f '$TEMP_FILE'" EXIT

                    # Check for --draft argument
                    if string match -q "*--draft*" $argv
                        set DRAFT_FLAG "--draft"
                    end

                    # Generate diff against origin/main and save to a temp file.
                    git diff origin/main . > $TEMP_FILE

                    # Pass the diff to sgpt with an appropriate prompt.
                    sgpt "Create a PR title and description based on the following changes:" < $TEMP_FILE > $TEMP_FILE.msg

                    # Open the message in the editor for review and confirmation.
                    eval $EDITOR $TEMP_FILE.msg

                    # User confirmation before proceeding.
                    echo "Do you want to proceed with PR creation? (y/n)"
                    read -l user_input

                    if string match -q -r "^[Yy]" $user_input
                        # Extract title and body for the PR from the temp file.
                        # Assuming first line is title, rest is body.
                        set -l PR_TITLE (head -n 1 $TEMP_FILE.msg)
                        set -l PR_BODY (tail -n +2 $TEMP_FILE.msg)

                        # Create the PR and capture the URL.
                        set -l PR_URL (gh pr create --title $PR_TITLE --body $PR_BODY $DRAFT_FLAG --web)

                        echo "PR created and browser opened: $PR_URL"
                    else
                        echo "PR creation aborted."
                    end

                case review
                    # Assuming the use of 'gh' to fetch the URL of the latest PR for the current branch.
                    set -l PR_URL (gh pr view --json url -q .url)

                    if test -z "$PR_URL"
                        echo "No PR found for the current branch."
                        return
                    end

                    # Fetching the diff of the latest PR and passing it to sgpt for review.
                    gh pr diff (gh pr view --json number -q .number) | sgpt "Review the following PR changes:" > $TEMP_FILE

                    # Display the AI-enhanced review to stdout.
                    cat $TEMP_FILE

                case '*'
                    echo "Unsupported pr command: $argv[2]"
            end

        case '*'
            # Delegate all other commands to the original sgpt application
            command sgpt $argv
    end
end
