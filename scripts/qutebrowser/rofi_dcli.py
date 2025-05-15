#!/usr/bin/env python3

import os
import subprocess
import sys
from shutil import which

ROFI_CMD_ARGS = [
    "rofi",
    "-theme",
    "/home/rash/.config/rofi/current_theme_single_column.rasi",
    "-dmenu",
    "-i",
    "-p",
]


def check_dependencies():
    missing = []
    for dep in ["rofi", "wl-copy", "wl-paste", "dcli"]:
        if which(dep) is None:
            missing.append(dep)

    if missing:
        rofi_error(f"Missing dependencies: {', '.join(missing)}")
        sys.exit(1)


def rofi_input(prompt):
    rofi_cmd = ROFI_CMD_ARGS + [prompt]
    result = subprocess.run(
        rofi_cmd, input="", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        sys.exit(0)
    return result.stdout.strip()


def rofi_error(message):
    subprocess.run(["rofi", "-e", message])


def rofi_select(prompt, options):
    rofi_cmd = ROFI_CMD_ARGS + [prompt]
    input_str = "\n".join(options)
    result = subprocess.run(
        rofi_cmd,
        input=input_str,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        sys.exit(0)
    return result.stdout.strip()


def run_dcli_wrapper(args):
    wrapper_path = os.path.expanduser("~/.config/scripts/shell/dcli_wrapper.py")
    if not os.path.isfile(wrapper_path):
        rofi_error(f"dcli_wrapper script not found at {wrapper_path}")
        sys.exit(1)
    cmd = [wrapper_path, "--headless"] + args
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def main():
    check_dependencies()
    if len(sys.argv) < 2:
        rofi_error("Usage: rofi_dcli.py [password|username|otp|note]")
        sys.exit(1)
    credential_type = sys.argv[1]
    valid_types = ["password", "username", "otp", "note"]
    if credential_type not in valid_types:
        rofi_error(f"Invalid credential type. Choose from: {', '.join(valid_types)}")
        sys.exit(1)
    # Initial input from user
    search_term = rofi_input(f"Search {credential_type}")
    args = [credential_type, search_term]
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "../shell/dcli_wrapper.py"),
        "--headless",
    ] + args
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        while True:
            # Read lines until we get a prompt or EOF
            output_lines = []
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.rstrip("\n")
                if line == "CHOOSE_INDEX":
                    # Show options in output_lines
                    choice = rofi_select("Select entry", output_lines)
                    if not choice:
                        proc.terminate()
                        sys.exit(0)
                    idx = choice.split(":", 1)[0].strip()
                    proc.stdin.write(f"{idx}\n")
                    proc.stdin.flush()
                    output_lines = []
                    continue
                elif line.startswith("PROMPT:"):
                    prompt = line[len("PROMPT:") :].strip()
                    user_input = rofi_input(prompt)
                    if not user_input:
                        proc.terminate()
                        sys.exit(0)
                    proc.stdin.write(f"{user_input}\n")
                    proc.stdin.flush()
                    output_lines = []
                    continue
                else:
                    output_lines.append(line)
            # If process exited, print any remaining output as message
            if output_lines:
                rofi_error("\n".join(output_lines))
            proc.wait()
            break
    finally:
        if proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    main()
