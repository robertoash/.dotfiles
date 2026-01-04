function hypr-keybinds --description 'Display Hyprland keybinds in fzf and execute selected command'
    # Get keybinds from hyprctl
    set -l binds_json (hyprctl binds -j 2>/dev/null)
    
    if test $status -ne 0
        echo "Error: Could not get keybinds from hyprctl"
        return 1
    end
    
    # Format keybinds as "[combo] description | dispatcher arg"
    # We only show binds with descriptions
    set -l formatted_binds (echo $binds_json | jq -r '
        .[] | 
        select(.has_description == true) |
        . as $bind |
        
        # Convert modmask to readable format
        (
            if ($bind.modmask | floor) == 0 then ""
            else
                (
                    [
                        (if ($bind.modmask | floor) % 2 == 1 then "SHIFT" else empty end),
                        (if (($bind.modmask | floor) / 4 | floor) % 2 == 1 then "CTRL" else empty end),
                        (if (($bind.modmask | floor) / 8 | floor) % 2 == 1 then "ALT" else empty end),
                        (if (($bind.modmask | floor) / 64 | floor) % 2 == 1 then "SUPER" else empty end),
                        (if (($bind.modmask | floor) / 128 | floor) % 2 == 1 then "ALTGR" else empty end)
                    ]
                ) as $mod_array |
                # Check if all four modifiers are present (Hyper)
                if ($mod_array | length) == 4 then "HYPER"
                else ($mod_array | join("+"))
                end
            end
        ) as $mods |
        
        # Handle mouse keys
        (
            if ($bind.key | startswith("mouse:")) then
                ($bind.key | split(":")[1]) as $code |
                if $code == "272" then "m:L"
                elif $code == "273" then "m:R"
                elif $code == "274" then "m:M"
                else "m:\($code)"
                end
            else
                $bind.key
            end
        ) as $key |
        
        # Build combo string
        (if $mods != "" then "\($mods)+\($key)" else $key end) as $combo |
        
        # Format: [combo] description (dispatcher arg) TAB dispatcher TAB arg
        "[\($combo)] \($bind.description) (\($bind.dispatcher) \($bind.arg | rtrimstr(" ")))\t\($bind.dispatcher)\t\($bind.arg)"
    ')
    
    if test -z "$formatted_binds"
        echo "No keybinds with descriptions found"
        return 1
    end
    
    # Show in fzf (display description with command in parenthesis)
    set -l selection (printf '%s\n' $formatted_binds | fzf \
        --prompt="Hyprland Keybinds> " \
        --delimiter='\t' \
        --with-nth=1 \
        --preview='echo {}' \
        --preview-window=hidden \
        --height=50% \
        --reverse \
        --bind='ctrl-/:toggle-preview')
    
    if test -z "$selection"
        return 0
    end
    
    # Extract dispatcher and arg from selection (fields 3 and 4)
    set -l parts (string split \t -- $selection)
    set -l dispatcher $parts[3]
    set -l arg $parts[4]
    
    # Execute the dispatcher
    if test -n "$dispatcher"
        echo "Executing: hyprctl dispatch $dispatcher $arg"
        hyprctl dispatch $dispatcher $arg
    end
end
