#!/bin/bash

# Direct Vivaldi launcher script - for use with Hyprland startup
# Created to work around PATH issues on login

# Log execution
echo "$(date): vivaldi_direct called with args: $@" >> /tmp/vivaldi_direct.log

# Parse arguments
PROFILE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [ -z "$PROFILE" ]; then
  echo "Error: --profile is required" >> /tmp/vivaldi_direct.log
  exit 1
fi

# Execute appropriate Vivaldi command based on profile
case "$PROFILE" in
  rash|jobhunt)
    /usr/bin/vivaldi --new-window --new-instance --ozone-platform=wayland --enable-features=UseOzonePlatform --profile-directory="$PROFILE" > /dev/null 2>&1 &
    ;;
  chatgpt)
    /usr/bin/vivaldi --new-window --new-instance --ozone-platform=wayland --enable-features=UseOzonePlatform --profile-directory=app_profile --app=https://chat.openai.com > /dev/null 2>&1 &
    ;;
  perplexity)
    /usr/bin/vivaldi --new-window --new-instance --ozone-platform=wayland --enable-features=UseOzonePlatform --profile-directory=app_profile --app=https://perplexity.ai > /dev/null 2>&1 &
    ;;
  *)
    echo "Error: Unknown profile $PROFILE" >> /tmp/vivaldi_direct.log
    exit 1
    ;;
esac

# Log completion
echo "$(date): vivaldi_direct launched Vivaldi with profile $PROFILE" >> /tmp/vivaldi_direct.log

exit 0