function hass-cli
    if not set -q __hass_cli_completions_loaded
        eval (env HASS_CLI_COMPLETE=source_fish hass-cli)
        set -g __hass_cli_completions_loaded 1
    end
    command hass-cli $argv
end