#! /bin/bash
# This script is used to listen for newly created workspaces using hyprctl
# and changing the layout to orientationtop if the workspace is on a vertical monitor

# Variable to store workspace information from the previous run
previous_run_workspaces=""

# Delay to give time for the workspaces to be created on boot
sleep 5

####################################################
############## Get a list of vertical monitors ################
####################################################

# Get a JSON of all monitors using hyprctl monitors -j
ALL_MONITORS=$(hyprctl monitors -j)
# Filter out only the monitors that have a transform property of 1
VERTICAL_MONITORS=$(echo $ALL_MONITORS | jq '.[] | select(.transform == 1)')
# Get the names of vertical monitors
VERTICAL_MONITOR_NAMES=$(echo $VERTICAL_MONITORS | jq -r '.name')

####################################################
### Apply the vertical layout to all workspaces on vertical monitors ###
####################################################

while true; do
    # Get the workspace JSON for the current run
    current_run_workspaces=$(hyprctl workspaces -j | jq -r '.[] | select(.name != "special") | "\(.monitor):\(.id)"')
    
    # Compare with the previous run to identify new workspaces
    new_workspaces=$(comm -13 <(echo "$previous_run_workspaces" | tr ' ' '\n' | sort) <(echo "$current_run_workspaces" | tr ' ' '\n' | sort))
    
    # Update the variable with current workspaces for the next run
    previous_run_workspaces="$current_run_workspaces"
    
    # Iterate through each vertical monitor
    for monitor in $VERTICAL_MONITOR_NAMES; do
        # Filter the new workspaces for the current monitor
        monitor_new_workspaces=$(echo "$new_workspaces" | grep "^$monitor:" | cut -d: -f2-)
        
        # Cycle through each workspace and set the layout to vertical if not processed
        while read -r workspace_id; do
            # Check if workspace_id is not empty
            if [ -n "$workspace_id" ]; then
                # Select the workspace
                hyprctl dispatch "workspace $workspace_id" > /dev/null  # Redirect "ok" to /dev/null
                # Set the layout to vertical
                hyprctl dispatch "layoutmsg orientationtop" > /dev/null  # Redirect "ok" to /dev/null
                #echo "Orientationtop set for workspace $workspace_id on monitor $monitor"
            fi
        done <<< "$monitor_new_workspaces"
    done
    sleep 3
done
