# Print an optspec for argparse to handle cmd's options that are independent of any subcommand.
function __fish_trash_global_optspecs
	string join \n c/color= t/table= h/help V/version
end

function __fish_trash_needs_command
	# Figure out if the current invocation already has a command.
	set -l cmd (commandline -opc)
	set -e cmd[1]
	argparse -s (__fish_trash_global_optspecs) -- $cmd 2>/dev/null
	or return
	if set -q argv[1]
		# Also print the command, so this can be used to figure out what it is.
		echo $argv[1]
		return 1
	end
	return 0
end

function __fish_trash_using_subcommand
	set -l cmd (__fish_trash_needs_command)
	test -z "$cmd"
	and return 1
	contains -- $cmd[1] $argv
end

complete -c trash -n "__fish_trash_needs_command" -s c -l color -d 'When to use colors' -r -f -a "auto\t''
always\t''
never\t''"
complete -c trash -n "__fish_trash_needs_command" -s t -l table -d 'When to format as a table' -r -f -a "auto\t''
always\t''
never\t''"
complete -c trash -n "__fish_trash_needs_command" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c trash -n "__fish_trash_needs_command" -s V -l version -d 'Print version'
complete -c trash -n "__fish_trash_needs_command" -a "list" -d 'List files'
complete -c trash -n "__fish_trash_needs_command" -a "put" -d 'Put files'
complete -c trash -n "__fish_trash_needs_command" -a "empty" -d 'PERMANANTLY removes files'
complete -c trash -n "__fish_trash_needs_command" -a "restore" -d 'Restore files'
complete -c trash -n "__fish_trash_needs_command" -a "completions" -d 'Generates completion for a shell'
complete -c trash -n "__fish_trash_needs_command" -a "manpage" -d 'Generates manpages'
complete -c trash -n "__fish_trash_needs_command" -a "help" -d 'Print this message or the help of the given subcommand(s)'
complete -c trash -n "__fish_trash_using_subcommand list" -l before -l older-than -l older -d 'Filter by time (older than)' -r
complete -c trash -n "__fish_trash_using_subcommand list" -l within -l newer-than -l newer -d 'Filter by time' -r
complete -c trash -n "__fish_trash_using_subcommand list" -l regex -d 'Filter by regex' -r
complete -c trash -n "__fish_trash_using_subcommand list" -l glob -d 'Filter by glob' -r
complete -c trash -n "__fish_trash_using_subcommand list" -l substring -d 'Filter by substring' -r
complete -c trash -n "__fish_trash_using_subcommand list" -l exact -d 'Filter by exact match' -r
complete -c trash -n "__fish_trash_using_subcommand list" -s m -l match -d 'What type of pattern to use' -r -f -a "regex\t''
substring\t''
glob\t''
exact\t''"
complete -c trash -n "__fish_trash_using_subcommand list" -s d -l directory -l dir -d 'Filter by directory' -r -F
complete -c trash -n "__fish_trash_using_subcommand list" -s n -l max -d 'Show \'n\' maximum trash items' -r
complete -c trash -n "__fish_trash_using_subcommand list" -l rev -d 'Reverse the sorting of trash items'
complete -c trash -n "__fish_trash_using_subcommand list" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c trash -n "__fish_trash_using_subcommand put" -s h -l help -d 'Print help'
complete -c trash -n "__fish_trash_using_subcommand empty" -l before -l older-than -l older -d 'Filter by time (older than)' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -l within -l newer-than -l newer -d 'Filter by time' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -l regex -d 'Filter by regex' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -l glob -d 'Filter by glob' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -l substring -d 'Filter by substring' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -l exact -d 'Filter by exact match' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -s m -l match -d 'What type of pattern to use' -r -f -a "regex\t''
substring\t''
glob\t''
exact\t''"
complete -c trash -n "__fish_trash_using_subcommand empty" -s d -l directory -l dir -d 'Filter by directory' -r -F
complete -c trash -n "__fish_trash_using_subcommand empty" -s n -l max -d 'Show \'n\' maximum trash items' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -s r -l ranges -d 'Filter by ranges' -r
complete -c trash -n "__fish_trash_using_subcommand empty" -l rev -d 'Reverse the sorting of trash items'
complete -c trash -n "__fish_trash_using_subcommand empty" -l all -d 'Empty all files'
complete -c trash -n "__fish_trash_using_subcommand empty" -s f -l force -d 'Skip confirmation'
complete -c trash -n "__fish_trash_using_subcommand empty" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c trash -n "__fish_trash_using_subcommand restore" -l before -l older-than -l older -d 'Filter by time (older than)' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -l within -l newer-than -l newer -d 'Filter by time' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -l regex -d 'Filter by regex' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -l glob -d 'Filter by glob' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -l substring -d 'Filter by substring' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -l exact -d 'Filter by exact match' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -s m -l match -d 'What type of pattern to use' -r -f -a "regex\t''
substring\t''
glob\t''
exact\t''"
complete -c trash -n "__fish_trash_using_subcommand restore" -s d -l directory -l dir -d 'Filter by directory' -r -F
complete -c trash -n "__fish_trash_using_subcommand restore" -s n -l max -d 'Show \'n\' maximum trash items' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -s r -l ranges -d 'Filter by ranges' -r
complete -c trash -n "__fish_trash_using_subcommand restore" -l rev -d 'Reverse the sorting of trash items'
complete -c trash -n "__fish_trash_using_subcommand restore" -s f -l force -d 'Skip confirmation'
complete -c trash -n "__fish_trash_using_subcommand restore" -s h -l help -d 'Print help (see more with \'--help\')'
complete -c trash -n "__fish_trash_using_subcommand completions" -s h -l help -d 'Print help'
complete -c trash -n "__fish_trash_using_subcommand manpage" -s h -l help -d 'Print help'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "list" -d 'List files'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "put" -d 'Put files'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "empty" -d 'PERMANANTLY removes files'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "restore" -d 'Restore files'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "completions" -d 'Generates completion for a shell'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "manpage" -d 'Generates manpages'
complete -c trash -n "__fish_trash_using_subcommand help; and not __fish_seen_subcommand_from list put empty restore completions manpage help" -f -a "help" -d 'Print this message or the help of the given subcommand(s)'
