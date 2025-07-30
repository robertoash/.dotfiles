function temp_check
    sudo smartctl -a $argv[1] | rg temp
end
