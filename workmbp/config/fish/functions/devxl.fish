function devxl --description 'Wrapper to use devxl connection/profile with dbt, dbtf, and snow'
    if test (count $argv) -lt 1
        echo "Usage: devxl <command> [args...]"
        echo "Supported commands: dbtf, dbt, snow"
        echo ""
        echo "Examples:"
        echo "  devxl dbtf run --select some_model"
        echo "  devxl snow sql -q 'SELECT 1'"
        echo "  devxl dbt build --select +my_model+"
        return 1
    end

    set cmd $argv[1]
    set -e argv[1]

    switch $cmd
        case dbtf dbt
            command $cmd --profile devxl $argv
        case snow
            command $cmd --connection devxl $argv
        case '*'
            echo "Error: Unsupported command '$cmd'"
            echo "Supported commands: dbtf, dbt, snow"
            return 1
    end
end
