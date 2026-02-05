function nup
    set -l temp_file (mktemp)
    cat > $temp_file
    nu -c "open --raw '$temp_file' | $argv[1]"
    command rm $temp_file
end
