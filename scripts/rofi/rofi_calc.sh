#!/bin/bash

# Temporary file to store the calculation
temp_calc_file="/tmp/calc_input"

# File to store the history of calculations
calc_history_file="/tmp/calc_history"

# File to store the last result
last_result_file="/tmp/calc_output"

# Ensure the history file and last result file exist
touch "$calc_history_file"
touch "$last_result_file"

# Cleanup function to remove temporary files
cleanup() {
    rm -f "$temp_calc_file"
    rm -f "$calc_history_file"
    rm -f "$last_result_file"
}

# Trap EXIT signal to perform cleanup on script exit
trap cleanup EXIT

# Function to trim spaces
trim() {
    local var="$*"
    # Remove leading and trailing whitespace
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo -n "$var"
}

# Function to replace solitary periods with the last result
replace_solitary_period() {
    local input=$1
    local last_result=$(<"$last_result_file")
    local replaced=""

    # Loop through each character of the input
    local prev_char=""
    for (( i=0; i<${#input}; i++ )); do
        local char="${input:$i:1}"

        if [[ "$char" == "." ]]; then
            # Check for solitary period
            if [[ "$prev_char" != "" && "$prev_char" =~ [0-9] ]]; then
                replaced+="."
            elif [[ $((i+1)) -lt ${#input} && "${input:$((i+1)):1}" =~ [0-9] ]]; then
                replaced+="."
            else
                replaced+="$last_result"
            fi
        else
            replaced+="$char"
        fi

        prev_char="$char"
    done

    echo "$replaced"
}

# Function to process selected history item
process_selected_history() {
    local selection=$1

    # Strip 'Calculation: ' or 'Result: ' from the selection
    local stripped_selection=${selection#*: }

    # Copy stripped selection to clipboard
    echo -n "$stripped_selection" | wl-copy

    # Update last_result_file only if it's a result
    if [[ $selection == Result:* ]]; then
        echo "$stripped_selection" > "$last_result_file"
    fi
}

# Function to process calculation and update history
process_calculation() {
    local original_input=$1
    local processed_input=$1

    # Replace only solitary periods with the last result
    processed_input=$(replace_solitary_period "$processed_input")

    # Write the processed input to the temporary file
    echo "$processed_input" > "$temp_calc_file"

    # Calculate the result
    result=$(calc -f "$temp_calc_file")

    # Trim the result and write to the last result file
    trimmed_result=$(trim "$result")
    echo "$trimmed_result" > "$last_result_file"

    # Update the history file with the original input and result
    echo -e "Calculation: $original_input\nResult: $trimmed_result\n\n$(cat "$calc_history_file")" > "$calc_history_file"
}

# Rofi loop
while true; do
    # Display the history and capture new input from Rofi
    input=$(cat "$calc_history_file" | rofi -dmenu -p "Enter calculation:")

    # Exit if Rofi is closed
    [[ $? -ne 0 ]] && exit

    # Check if input is a selection from history
    if [[ $input == Calculation:* ]] || [[ $input == Result:* ]]; then
        process_selected_history "$input"
    else
        # Process the new input and update history
        process_calculation "$input"
    fi
done
