#!/usr/bin/env python3
import subprocess
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


@userscript
def run_with_paste(request):
    # Parse arguments using qutescript's parser
    args = parser.parse_args()

    # Print debug info
    print(f"Running script: {args.script}")
    print(f"With args: {args.args}")
    print(f"Using paste delay: {args.paste_delay}ms")

    try:
        # Run the script with output capture
        subprocess.run(
            [args.script] + args.args,
            check=True,
            text=True,
            capture_output=True,
        )

        # Send paste command
        return f"cmd-later {args.paste_delay} fake-key <Ctrl-v>"

    except Exception as e:
        request.send_text(f"Error: {e}")


if __name__ == "__main__":
    run_with_paste()
