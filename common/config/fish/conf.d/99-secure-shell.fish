# Secure shell configuration - only active when SECURE_SHELL env var is set
# This file is safe to track in git and symlink to ~/.config because it only
# activates when launched via secure_shell.sh script (which exports SECURE_SHELL=1)
#
# IMPORTANT: This file should NEVER set SECURE_SHELL=1 itself - that must come
# from the parent process (secure_shell.sh). This prevents the leak where
# SECURE_SHELL persists into regular shells.

if set -q SECURE_SHELL
    # Generate unique session ID for ephemeral history
    # This runs every time fish starts (including after rr reload) to create
    # a fresh ephemeral history session
    set SESSION_ID "secure_shell_"(date +%s)"_"(random)
    set -gx fish_history $SESSION_ID
end
