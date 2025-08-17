#!/usr/bin/env python3
import subprocess
import json
import time
import os
from qutescript import userscript
from qutescript.cli import parser

# Add your arguments to qutescript's parser
parser.add_argument("--script", help="The script to run", required=True)
parser.add_argument(
    "--paste-delay",
    type=int,
    help="The delay in milliseconds to wait before pasting",
    default=500,
)
parser.add_argument("args", nargs="*", help="Arguments for the script")


def get_focused_window_id():
    """Get the currently focused window ID in Hyprland"""
    try:
        result = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            window_info = json.loads(result.stdout)
            return window_info.get("address")
    except Exception as e:
        print(f"Warning: Could not get focused window: {e}")
    return None


def focus_window(window_id):
    """Focus a specific window in Hyprland by its ID"""
    if not window_id:
        return False
    try:
        result = subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"address:{window_id}"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Warning: Could not focus window: {e}")
        return False


def is_authenticated():
    """Check if dcli is authenticated"""
    try:
        result = subprocess.run(
            ["dcli", "sync"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return "Successfully synced" in result.stdout and result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


@userscript
def run_with_paste(request):
    # Parse arguments using qutescript's parser
    args = parser.parse_args()

    # Print debug info
    print(f"Running script: {args.script}")
    print(f"With args: {args.args}")
    print(f"Using paste delay: {args.paste_delay}ms")

    # Capture the current window ID before running the script
    original_window = get_focused_window_id()
    print(f"Original window ID: {original_window}")

    # Check if we need authentication first
    if not is_authenticated():
        print("Not authenticated, triggering login...")
        # Launch terminal for authentication
        subprocess.run(["wezterm", "start", "--", "dcli", "sync"])
        
        # Wait a bit for user to complete authentication
        time.sleep(1)
        
        # Check if authentication succeeded
        if not is_authenticated():
            request.send_text("Authentication required. Please authenticate and try again.")
            return

    # Now run the actual password retrieval
    try:
        # Run the script with output capture
        result = subprocess.run(
            [args.script] + args.args,
            check=False,
            text=True,
            capture_output=True,
        )

        # Check for any errors
        if result.returncode != 0:
            # Check if it was an auth error (shouldn't happen now but just in case)
            if result.returncode == 42:
                request.send_text("Authentication failed. Please try again.")
                return
            else:
                # Some other error
                request.send_text(f"Error running script: {result.stderr}")
                return

        # Success! Now handle the paste
        print("Script executed successfully")

        # Refocus the original window before pasting
        if original_window:
            print(f"Refocusing original window: {original_window}")
            focus_window(original_window)
            # Small delay to ensure window is focused
            time.sleep(0.1)

        # Send paste command
        return f"cmd-later {args.paste_delay} fake-key <Ctrl-v>"

    except Exception as e:
        request.send_text(f"Error: {e}")
        return


if __name__ == "__main__":
    run_with_paste()
