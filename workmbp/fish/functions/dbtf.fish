function dbtf --description 'dbt Fusion wrapper that automatically uses local_dev profile'
    # Check for help flag first to prepend our documentation
    if test (count $argv) -ge 1; and begin; test "$argv[1]" = "--help"; or test "$argv[1]" = "-h"; end
        echo "⚡ dbt Fusion - Local development with 4.5x faster performance"
        echo "🔗 Connection: Direct to Snowflake using ~/.dbt/profiles.yml"
        echo "🗄️  Target Schema: 'dbt_rash_fusion' in READLY_DEV database"
        echo "🔑 Auth: JWT key-pair via PRIVATE_KEY_PASSPHRASE (sops secret)"
        echo "📝 Default Profile: 'default' → local_dev configuration"
        echo "🔧 Override: Use --profile <profile_name> to change"
        echo ""
        command dbtf $argv
    else
        # Check if --profile is already specified
        set has_profile false
        for arg in $argv
            if string match -q '*profile*' -- $arg
                set has_profile true
                break
            end
        end
        
        # Add --profile local_dev if not specified
        if not $has_profile
            command dbtf --profile local_dev $argv
        else
            command dbtf $argv
        end
    end
end