# Lazy Google Cloud SDK setup
function gcloud
    if not set -q __gcloud_setup_done
        echo "🌩️ Setting up Google Cloud SDK..." >&2
        if test -f '/home/rash/builds/google-cloud-sdk/path.fish.inc'
            source '/home/rash/builds/google-cloud-sdk/path.fish.inc'
        end
        set -g __gcloud_setup_done 1
    end
    command gcloud $argv
end

# Add wrappers for other common gcloud tools if you use them
function gsutil
    __ensure_gcloud_setup
    command gsutil $argv
end

function bq
    __ensure_gcloud_setup
    command bq $argv
end

# Helper function
function __ensure_gcloud_setup
    if not set -q __gcloud_setup_done
        if test -f '/home/rash/builds/google-cloud-sdk/path.fish.inc'
            source '/home/rash/builds/google-cloud-sdk/path.fish.inc'
        end
        set -g __gcloud_setup_done 1
    end
end

# Load Google Cloud SDK completion
if test -f '/home/rash/builds/google-cloud-sdk/completion.fish.inc'
    source '/home/rash/builds/google-cloud-sdk/completion.fish.inc'
end