function dbt --description 'dbt Cloud CLI wrapper with custom dag subcommand'
    # Check for help flag first to prepend our documentation
    if test (count $argv) -ge 1; and test "$argv[1]" = "--help" -o "$argv[1]" = "-h"
        echo "🚀 dbt Cloud CLI - Full platform features with cloud infrastructure"
        echo "📡 Connection: Uses dbt_cloud.yml (ignores profiles.yml)"
        echo "🗄️  Target Schema: 'rash' in READLY_DEV database"
        echo "⚡ Custom Command: 'dbt dag <model>' - Generate DAG visualization"
        echo "🔧 Override: Set different --environment or DBT_CLOUD_CONFIG_PATH"
        echo ""
        command dbt $argv
    # Check if first argument is "dag"
    else if test (count $argv) -ge 1; and test "$argv[1]" = "dag"
        # Remove "dag" from arguments and pass the rest to the script
        set -e argv[1]
        ~/.dotfiles/workmbp/scripts/dbt_dag_viz.py $argv
    else
        # dbt Cloud CLI uses dbt_cloud.yml directly, no profile needed
        command dbt $argv
    end
end
