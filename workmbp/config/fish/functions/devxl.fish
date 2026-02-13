function devxl --description 'Wrapper to use DEV_RA_WH warehouse with dbtf and snow'
    if test (count $argv) -lt 1
        echo "Usage: devxl <command> [args...]"
        echo "Supported commands: dbtf, snow"
        echo ""
        echo "Examples:"
        echo "  devxl dbtf run --select some_model"
        echo "  devxl snow sql -q 'SELECT 1'"
        return 1
    end

    set cmd $argv[1]
    set -e argv[1]

    switch $cmd
        case dbtf
            DBT_TARGET=devxl command $cmd $argv
        case snow
            set subcmd $argv[1]
            set -e argv[1]
            command $cmd $subcmd -c devxl $argv
        case '*'
            echo "Error: Unsupported command '$cmd'"
            echo "Supported commands: dbtf, snow"
            return 1
    end
end
