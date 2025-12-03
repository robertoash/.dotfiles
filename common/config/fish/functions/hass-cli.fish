function hass-cli
    if not set -q __hass_cli_completions_loaded
        eval (env _HASS_CLI_COMPLETE=fish_source hass-cli)
        set -g __hass_cli_completions_loaded 1
    end
    command hass-cli $argv
end