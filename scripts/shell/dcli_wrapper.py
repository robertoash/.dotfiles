#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import tempfile
import termios
import tty
from shutil import which


# Get a single keypress from the user
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


# Check if required programs are installed
def check_dependencies():
    missing = []
    for dep in ["dcli", "wl-copy", "fzf"]:
        if which(dep) is None:
            missing.append(dep)

    if missing:
        print(f"Error: Missing dependencies: {', '.join(missing)}")
        print("Please install them before using this script.")
        sys.exit(1)


# Check if dcli is authenticated
def is_authenticated():
    try:
        # Try to run sync command with a short timeout
        cmd = ["dcli", "sync"]

        # Use a short timeout - if it takes longer than 1 second, it's likely
        # waiting for an OTP or password
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)

        # If authenticated, the output will contain "Successfully synced"
        return "Successfully synced" in result.stdout and result.returncode == 0
    except subprocess.TimeoutExpired:
        # If it times out, then it's probably waiting for authentication
        return False
    except Exception:
        return False


# Execute dcli command and get output
def execute_dcli(args, ignore_errors=False, headless=False):
    try:
        # For password related commands, check auth first
        cmd_requires_auth = args[0] in ["password", "p", "note", "n", "otp", "o"]

        if cmd_requires_auth and not is_authenticated():
            if headless:
                max_tries = 3
                tries = 0
                notified = False
                while not is_authenticated() and tries < max_tries:
                    if not notified:
                        subprocess.run(
                            ["dunstify", "Authentication required. Redirecting..."]
                        )
                        notified = True
                    print(
                        "You are not logged in. Launching a terminal for dcli login...",
                        file=sys.stderr,
                    )
                    subprocess.run(["kitty", "-e", "dcli", "sync"])
                    tries += 1
                    if not is_authenticated() and tries < max_tries:
                        print(
                            f"Authentication failed or not completed. Please try again. "
                            f"({tries}/{max_tries})",
                            file=sys.stderr,
                        )
                if not is_authenticated():
                    print(
                        f"Authentication failed after {max_tries} attempts. Exiting.",
                        file=sys.stderr,
                    )
                    subprocess.run(["dunstify", "dcli login failed after 3 attempts"])
                    sys.exit(1)
                print("Authentication successful. Continuing...", file=sys.stderr)
                subprocess.run(["dunstify", "dcli login successful"])
                # Now authenticated, proceed to run the original dcli command
                cmd = ["dcli"] + args
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0 and not ignore_errors:
                    print(f"Error executing dcli: {result.stderr}")
                    sys.exit(result.returncode)
                return result.stdout.strip()
            print("dcli is not authenticated. Switching to interactive mode...")
            # Run in interactive mode
            result = direct_execute_dcli(args)
            # If this was successful, return empty string to signal we handled it
            if (
                isinstance(result, subprocess.CompletedProcess)
                and result.returncode == 0
            ):
                return ""
            return (
                result.returncode
                if isinstance(result, subprocess.CompletedProcess)
                else result
            )

        # Regular execution with output capture
        cmd = ["dcli"] + args
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check if there was an error
        if result.returncode != 0 and not ignore_errors:
            print(f"Error executing dcli: {result.stderr}")
            sys.exit(result.returncode)

        return result.stdout.strip()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Headless mode for GUI integration",
        default=False,
    )
    # Parse known args so we don't interfere with dcli's own args
    args, unknown = parser.parse_known_args()
    return args, unknown


def select_and_copy(
    items,
    field,
    headless,
    single_msg_fn,
    multi_display_fn,
    clipboard_fn,
    not_found_msg,
    sys_exit_on_none=True,
    interactive_state=None,  # New: dict to hold state between steps
):
    if not items:
        print(not_found_msg)
        if sys_exit_on_none:
            sys.exit(1)
        return False
    if len(items) == 1:
        item = items[0]
        value = clipboard_fn(item)
        if value:
            subprocess.run(["wl-copy"], input=value, text=True)
            if not headless:
                print(single_msg_fn(item))
            return True
        else:
            print(f"Field '{field}' not found in the item.")
            return False
    else:
        if headless:
            for i, item in enumerate(items):
                print(f"{i}: {multi_display_fn(item)}")
            print("CHOOSE_INDEX")
            sys.stdout.flush()
            # Read index from stdin
            try:
                idx_line = sys.stdin.readline()
                idx = int(idx_line.strip())
                if idx < 0 or idx >= len(items):
                    print("Invalid index.")
                    if sys_exit_on_none:
                        sys.exit(1)
                    return False
                item = items[idx]
                value = clipboard_fn(item)
                if value:
                    subprocess.run(["wl-copy"], input=value, text=True)
                    if not headless:
                        print(single_msg_fn(item))
                    return True
                else:
                    print(f"Field '{field}' not found in the selected item.")
                    return False
            except Exception:
                print("Invalid input.")
                if sys_exit_on_none:
                    sys.exit(1)
                return False
        else:
            with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                for i, item in enumerate(items):
                    tmp.write(f"{i}: {multi_display_fn(item)}\n")
                tmp_path = tmp.name
            try:
                fzf_cmd = f'cat {tmp_path} | fzf --prompt="Select entry: " --height=10'
                fzf_result = subprocess.run(
                    fzf_cmd, shell=True, capture_output=True, text=True
                )
                if fzf_result.returncode != 0:
                    print("Selection cancelled.")
                    if sys_exit_on_none:
                        sys.exit(1)
                    return False
                selection = fzf_result.stdout.strip()
                if not selection:
                    print("No selection made.")
                    if sys_exit_on_none:
                        sys.exit(1)
                    return False
                index = int(selection.split(":", 1)[0])
                item = items[index]
                value = clipboard_fn(item)
                if value:
                    subprocess.run(["wl-copy"], input=value, text=True)
                    if not headless:
                        print(single_msg_fn(item))
                    return True
                else:
                    print(f"Field '{field}' not found in the selected item.")
                    return False
            finally:
                os.unlink(tmp_path)


# Utility to run dcli and parse JSON output
def run_dcli_json(args, silent=False, headless=False):
    output = execute_dcli(args, headless=headless)
    if isinstance(output, int) or output == "":
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        if not silent:
            print(f"Error: Failed to parse JSON output: {output}")
        return None


# Consolidated handler for all entry types (password, note, username, otp)
def handle_entry(
    dcli_args,
    field,
    headless,
    single_msg_fn,
    multi_display_fn,
    clipboard_fn,
    not_found_msg,
    sys_exit_on_none=True,
    otp_prompt_fn=None,  # Optional, for password/otp
    otp_action_fn=None,  # Optional, for password/otp
    otp_check_fn=None,  # Optional, for password/otp
    search_terms=None,  # Optional, for password/otp
    interactive_state=None,  # New: dict to hold state between steps
):
    items = run_dcli_json(dcli_args, headless=headless)
    if items is None:
        return False, None, None
    found = select_and_copy(
        items,
        field,
        headless,
        single_msg_fn,
        multi_display_fn,
        clipboard_fn,
        not_found_msg,
        sys_exit_on_none=sys_exit_on_none,
        interactive_state=interactive_state,
    )
    if (
        found
        and len(items) == 1
        and otp_prompt_fn
        and otp_action_fn
        and otp_check_fn
        and search_terms
    ):
        cred = items[0]
        if otp_check_fn(cred) and not headless:
            if otp_prompt_fn():
                otp_action_fn(search_terms[0])
        elif otp_check_fn(cred) and headless:
            otp_input = otp_prompt_fn(headless=True)
            if otp_input:
                otp_action_fn(search_terms[0])
    return found, items


def handle_password(args, otp=False, silent=False, headless=False):
    orig_args = args.copy()
    field = "otp" if otp else "password"
    search_terms = [
        arg
        for arg in orig_args
        if not arg.startswith("-") and arg not in ["password", "p"]
    ]
    if not search_terms:
        if not silent:
            print("No search terms provided.")
        return False, None, None
    search_args = ["password"]
    if otp:
        search_args.extend(["-f", field])
    search_args.extend(search_terms)
    search_args.extend(["-o", "json"])

    def single_msg(cred):
        emoji = "🔑" if field == "otp" else "🔓"
        return (
            f"{emoji} {field.capitalize()} for "
            f'"{cred.get('title', 'Unknown')}" copied to clipboard.'
        )

    def multi_display(cred):
        title = cred.get("title", "Unknown")
        login = cred.get("login", "") or cred.get("email", "")
        return f"{title} - {login}" if login else title

    def clipboard(cred):
        return cred.get(field, "")

    def otp_check(cred):
        return "otpSecret" in cred or "otp" in cred

    found, cred, items = handle_entry(
        search_args,
        field,
        headless,
        single_msg,
        multi_display,
        clipboard,
        "No matching credentials found.",
        sys_exit_on_none=True,
        otp_prompt_fn=prompt_for_otp,
        otp_action_fn=lambda search_term: get_otp_for_credential(
            search_term, headless=headless
        ),
        otp_check_fn=otp_check,
        search_terms=search_terms,
    )
    if found and cred:
        has_otp = "otpSecret" in cred or "otp" in cred
        search_term = search_terms[0]
        if headless:
            return True, search_term, False
        return True, search_term, has_otp
    return found, None, None


def handle_note(args, headless=False):
    orig_args = args.copy()
    if "-o" in orig_args:
        idx = orig_args.index("-o")
        if idx + 1 < len(orig_args):
            orig_args.pop(idx + 1)
        orig_args.pop(idx)
    elif "--output" in orig_args:
        idx = orig_args.index("--output")
        if idx + 1 < len(orig_args):
            orig_args.pop(idx + 1)
        orig_args.pop(idx)
    orig_args += ["-o", "json"]

    def single_msg(note):
        return f"📝 Note \"{note.get('title', 'Unknown')}\" copied to clipboard."

    def multi_display(note):
        return note.get("title", "Unknown")

    def clipboard(note):
        return note.get("content", "")

    handle_entry(
        orig_args,
        "content",
        headless,
        single_msg,
        multi_display,
        clipboard,
        "No matching notes found.",
        sys_exit_on_none=True,
    )


def handle_username(args, headless=False):
    orig_args = args.copy()
    search_terms = [
        arg
        for arg in orig_args
        if not arg.startswith("-") and arg not in ["username", "u"]
    ]
    if not search_terms:
        print("No search terms provided.")
        return
    search_args = ["password"] + search_terms + ["-o", "json"]

    def single_msg(cred):
        return (
            f"👤 Username for \"{cred.get('title', 'Unknown')}\" copied to clipboard."
        )

    def multi_display(cred):
        title = cred.get("title", "Unknown")
        login = cred.get("login", "") or cred.get("email", "")
        return f"{title} - {login}" if login else title

    def clipboard(cred):
        return cred.get("login", "") or cred.get("email", "")

    handle_entry(
        search_args,
        "login",
        headless,
        single_msg,
        multi_display,
        clipboard,
        "No matching credentials found.",
        sys_exit_on_none=True,
    )


def handle_direct_otp(args, headless=False):
    json_args = ["password", "-f", "otp"] + args + ["-o", "json"]

    def single_msg(cred):
        return "🔑 OTP code copied to clipboard."

    def multi_display(cred):
        title = cred.get("title", "Unknown")
        login = cred.get("login", "") or cred.get("email", "")
        return f"{title} - {login}" if login else title

    def clipboard(cred):
        otp_args = ["password", "-f", "otp", cred.get("title", ""), "-o", "console"]
        otp_output = execute_dcli(otp_args, headless=headless)
        if isinstance(otp_output, int) or otp_output == "":
            return ""
        if otp_output and not otp_output.startswith("Error"):
            return otp_output.strip()
        return ""

    handle_entry(
        json_args,
        "otp",
        headless,
        single_msg,
        multi_display,
        clipboard,
        "No matching OTP credentials found.",
        sys_exit_on_none=False,
        otp_prompt_fn=prompt_for_otp,
        otp_action_fn=lambda search_term: get_otp_for_credential(
            search_term, headless=headless
        ),
        otp_check_fn=None,
        search_terms=None,
    )


def prompt_for_otp(headless=False):
    if headless:
        print("PROMPT: Enter OTP code:")
        sys.stdout.flush()
        otp_input = sys.stdin.readline().strip()
        if otp_input:
            print("Copying OTP code...")
            return otp_input  # Return the entered OTP or signal to proceed
        else:
            print("Exiting without copying OTP.")
            return None
    print("🔑 OTP available for this credential.")
    print("ENTER to copy OTP to clipboard, ESC to exit.")
    sys.stdout.flush()

    while True:
        key = getch()
        if key == "\r" or key == "\n":  # Enter key
            print("Copying OTP code...")
            return True
        elif key == "\x1b":  # Esc key
            print("Exiting without copying OTP.")
            return False
        # Ignore other keys


# Handle OTP retrieval after password
def get_otp_for_credential(search_term, headless=False):
    # Get the OTP code with console output
    otp_args = ["password", "-f", "otp", search_term, "-o", "console"]
    otp_output = execute_dcli(otp_args, headless=headless)

    # Check if we got a string result
    if isinstance(otp_output, int) or otp_output == "":
        return False

    # Parse the output - if it's a single line, it's the OTP code
    if otp_output and not otp_output.startswith("Error"):
        # Strip any whitespace and newlines
        otp_code = otp_output.strip()

        # Copy to clipboard
        subprocess.run(["wl-copy"], input=otp_code, text=True)
        if not headless:
            print("🔑 OTP code copied to clipboard.")
        return True
    else:
        print("No OTP code found in the credential.")
        return False


# Directly execute dcli with passthrough for interactive I/O
def direct_execute_dcli(args):
    cmd = ["dcli"] + args
    # Use subprocess.run without capturing output to allow interactive I/O
    result = subprocess.run(cmd)
    # If this is a password command and we had to authenticate, return empty string
    # to signal that we should not proceed with credential handling
    if args[0] in ["p", "password", "n", "note", "o", "otp"] and result.returncode == 0:
        return ""
    return result


def main():
    check_dependencies()
    parsed, unknown = parse_args()
    headless = parsed.headless
    sys.argv = [sys.argv[0]] + unknown
    if len(sys.argv) < 2:
        direct_execute_dcli(["--help"])
        sys.exit(0)
    command = sys.argv[1]
    args = sys.argv[1:]

    command_map = {
        "p": "password",
        "password": "password",
        "n": "note",
        "note": "note",
        "o": "otp",
        "otp": "otp",
        "u": "username",
        "username": "username",
    }

    if command_map.get(command) == "password":
        orig_args = args.copy()
        search_terms = [
            arg
            for arg in orig_args
            if not arg.startswith("-") and arg not in ["password", "p"]
        ]
        if not search_terms:
            print("No search terms provided.")
            sys.exit(1)
        search_args = ["password"] + search_terms + ["-o", "json"]

        def single_msg(cred):
            return f"🔓 Password for \"{cred.get('title', 'Unknown')}\" copied to clipboard."

        def multi_display(cred):
            title = cred.get("title", "Unknown")
            login = cred.get("login", "") or cred.get("email", "")
            return f"{title} - {login}" if login else title

        def clipboard(cred):
            return cred.get("password", "")

        def otp_check(cred):
            return "otpSecret" in cred or "otp" in cred

        handle_entry(
            search_args,
            "password",
            headless,
            single_msg,
            multi_display,
            clipboard,
            "No matching credentials found.",
            sys_exit_on_none=True,
            otp_prompt_fn=prompt_for_otp,
            otp_action_fn=lambda search_term: get_otp_for_credential(
                search_term, headless=headless
            ),
            otp_check_fn=otp_check,
            search_terms=search_terms,
        )
    elif command_map.get(command) == "note":
        orig_args = args.copy()
        if "-o" in orig_args:
            idx = orig_args.index("-o")
            if idx + 1 < len(orig_args):
                orig_args.pop(idx + 1)
            orig_args.pop(idx)
        elif "--output" in orig_args:
            idx = orig_args.index("--output")
            if idx + 1 < len(orig_args):
                orig_args.pop(idx + 1)
            orig_args.pop(idx)
        orig_args += ["-o", "json"]

        def single_msg(note):
            return f"📝 Note \"{note.get('title', 'Unknown')}\" copied to clipboard."

        def multi_display(note):
            return note.get("title", "Unknown")

        def clipboard(note):
            return note.get("content", "")

        handle_entry(
            orig_args,
            "content",
            headless,
            single_msg,
            multi_display,
            clipboard,
            "No matching notes found.",
            sys_exit_on_none=True,
        )
    elif command_map.get(command) == "otp":
        json_args = ["password", "-f", "otp"] + args[1:] + ["-o", "json"]

        def single_msg(cred):
            return "🔑 OTP code copied to clipboard."

        def multi_display(cred):
            title = cred.get("title", "Unknown")
            login = cred.get("login", "") or cred.get("email", "")
            return f"{title} - {login}" if login else title

        def clipboard(cred):
            otp_args = ["password", "-f", "otp", cred.get("title", ""), "-o", "console"]
            otp_output = execute_dcli(otp_args, headless=headless)
            if isinstance(otp_output, int) or otp_output == "":
                return ""
            if otp_output and not otp_output.startswith("Error"):
                return otp_output.strip()
            return ""

        handle_entry(
            json_args,
            "otp",
            headless,
            single_msg,
            multi_display,
            clipboard,
            "No matching OTP credentials found.",
            sys_exit_on_none=False,
            otp_prompt_fn=prompt_for_otp,
            otp_action_fn=lambda search_term: get_otp_for_credential(
                search_term, headless=headless
            ),
            otp_check_fn=None,
            search_terms=None,
        )
    elif command_map.get(command) == "username":
        orig_args = args.copy()
        search_terms = [
            arg
            for arg in orig_args
            if not arg.startswith("-") and arg not in ["username", "u"]
        ]
        if not search_terms:
            print("No search terms provided.")
            sys.exit(1)
        search_args = ["password"] + search_terms + ["-o", "json"]

        def single_msg(cred):
            return f"👤 Username for \"{cred.get('title', 'Unknown')}\" copied to clipboard."

        def multi_display(cred):
            title = cred.get("title", "Unknown")
            login = cred.get("login", "") or cred.get("email", "")
            return f"{title} - {login}" if login else title

        def clipboard(cred):
            return cred.get("login", "") or cred.get("email", "")

        handle_entry(
            search_args,
            "login",
            headless,
            single_msg,
            multi_display,
            clipboard,
            "No matching credentials found.",
            sys_exit_on_none=True,
        )
    else:
        result = direct_execute_dcli(args)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
