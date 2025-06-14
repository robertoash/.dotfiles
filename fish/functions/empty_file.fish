function empty_file
  if test -z "$argv[1]"
    echo "Usage: empty_file /path/to/file"
    return 1
  end

  if test -f $argv[1]
    : > $argv[1]
    echo "Emptied: $argv[1]"
  else
    echo "File does not exist: $argv[1]"
    return 1
  end
end
