#!/usr/bin/env python3

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
def execute_dcli(args, ignore_errors=False):
    try:
        # For password related commands, check auth first
        cmd_requires_auth = args[0] in ["password", "p", "note", "n", "otp", "o"]

        if cmd_requires_auth and not is_authenticated():
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


def handle_password(args, otp=False, silent=False):
    # Get original args but replace output format with json
    orig_args = args.copy()

    # Get field if specified
    field = "otp" if otp else "password"

    # Extract search terms (non-option arguments)
    search_terms = []
    for arg in orig_args:
        if not arg.startswith("-") and arg not in ["password", "p"]:
            search_terms.append(arg)

    # If no search terms, we can't proceed
    if not search_terms:
        if not silent:
            print("No search terms provided.")
        return False, None, None

    # Build the correct command in proper order
    search_args = ["password"]  # Always use 'password', not 'p'

    if otp:  # Add field parameter if we're looking for OTP
        search_args.extend(["-f", field])

    # Add search terms
    search_args.extend(search_terms)

    # Add json output format
    search_args.extend(["-o", "json"])

    # Execute command
    output = execute_dcli(search_args)

    # If we got an int (returncode) or empty string (interactive auth handled), exit early
    if isinstance(output, int) or output == "":
        return False, None, None

    try:
        credentials = json.loads(output)
    except json.JSONDecodeError:
        if not silent:
            print("Error: Failed to parse JSON output.")
        return False, None, None

    if not credentials:
        if not silent:
            print("No matching credentials found.")
        return False, None, None

    # Handle single result
    if len(credentials) == 1:
        credential = credentials[0]

        # Extract field value and OTP status
        value = credential.get(field, "")
        has_otp = "otpSecret" in credential or "otp" in credential
        search_term = search_terms[0]  # Use the search term for follow-up

        if value:
            subprocess.run(["wl-copy"], input=value, text=True)
            if not silent:
                emoji = "🔑" if field == "otp" else "🔓"
                print(
                    f"{emoji} {field.capitalize()} for "
                    f"\"{credential.get('title', 'Unknown')}\" copied to clipboard."
                )
            return True, search_term, has_otp
        else:
            if not silent:
                print(f"Field '{field}' not found in the credential.")
            return False, None, None
    else:
        # Create temporary file for fzf selection
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            for i, cred in enumerate(credentials):
                title = cred.get("title", "Unknown")
                login = cred.get("login", "") or cred.get("email", "")
                display = f"{title} - {login}" if login else title
                tmp.write(f"{i}: {display}\n")
            tmp_path = tmp.name

        try:
            # Use fzf for selection
            fzf_cmd = f'cat {tmp_path} | fzf --prompt="Select credential: " --height=10'
            fzf_result = subprocess.run(
                fzf_cmd, shell=True, capture_output=True, text=True
            )

            if fzf_result.returncode != 0:
                if not silent:
                    print("Selection cancelled.")
                return False, None, None

            selection = fzf_result.stdout.strip()
            if not selection:
                if not silent:
                    print("No selection made.")
                return False, None, None

            # Extract index from selection
            index = int(selection.split(":", 1)[0])
            credential = credentials[index]

            # Extract field value and OTP status
            value = credential.get(field, "")
            has_otp = "otpSecret" in credential or "otp" in credential
            search_term = credential.get(
                "title", search_terms[0]
            )  # Use title for follow-up

            if value:
                subprocess.run(["wl-copy"], input=value, text=True)
                if not silent:
                    emoji = "🔑" if field == "otp" else "🔓"
                    print(
                        f"{emoji} {field.capitalize()} for "
                        f"\"{credential.get('title', 'Unknown')}\" copied to clipboard."
                    )
                return True, search_term, has_otp
            else:
                if not silent:
                    print(f"Field '{field}' not found in the selected credential.")
                return False, None, None
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)


# Handle note command with fzf and wl-copy
def handle_note(args):
    # Get original args but replace output format with json
    orig_args = args.copy()

    # Remove -o/--output if present and add our own
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

    # Add json output format
    orig_args += ["-o", "json"]

    # Execute command
    output = execute_dcli(orig_args)

    # If we got an int (returncode) or empty string (interactive auth handled), exit early
    if isinstance(output, int) or output == "":
        return

    try:
        notes = json.loads(output)

        if not notes:
            print("No matching notes found.")
            sys.exit(1)

        # Handle single result
        if len(notes) == 1:
            note = notes[0]
            content = note.get("content", "")
            subprocess.run(["wl-copy"], input=content, text=True)
            print(f"📝 Note \"{note.get('title', 'Unknown')}\" copied to clipboard.")
        else:
            # Create temporary file for fzf selection
            with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                for i, note in enumerate(notes):
                    title = note.get("title", "Unknown")
                    tmp.write(f"{i}: {title}\n")
                tmp_path = tmp.name

            try:
                # Use fzf for selection
                fzf_cmd = f'cat {tmp_path} | fzf --prompt="Select note: " --height=10'
                fzf_result = subprocess.run(
                    fzf_cmd, shell=True, capture_output=True, text=True
                )

                if fzf_result.returncode != 0:
                    print("Selection cancelled.")
                    sys.exit(1)

                selection = fzf_result.stdout.strip()
                if not selection:
                    print("No selection made.")
                    sys.exit(1)

                # Extract index from selection
                index = int(selection.split(":", 1)[0])
                note = notes[index]

                content = note.get("content", "")
                subprocess.run(["wl-copy"], input=content, text=True)
                print(
                    f"📝 Note \"{note.get('title', 'Unknown')}\" copied to clipboard."
                )
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON output: {output}")
        sys.exit(1)


def prompt_for_otp():
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


# Handle direct OTP command
def handle_direct_otp(args):
    # First use JSON to determine number of matches and get credential info
    json_args = ["password", "-f", "otp"] + args + ["-o", "json"]
    json_output = execute_dcli(json_args)

    # If we got an int (returncode) or empty string (interactive auth handled), exit early
    if isinstance(json_output, int) or json_output == "":
        return

    try:
        credentials = json.loads(json_output)

        # No credentials found
        if not credentials:
            print("No matching OTP credentials found.")
            return

        # Single credential - get OTP directly
        if len(credentials) == 1:
            credential = credentials[0]
            search_term = credential.get("title", args[0] if args else "")

            # Get the actual OTP with console output
            otp_args = ["password", "-f", "otp", search_term, "-o", "console"]
            otp_output = execute_dcli(otp_args)

            # Check if we got a string result
            if isinstance(otp_output, int) or otp_output == "":
                return

            if otp_output and not otp_output.startswith("Error"):
                otp_code = otp_output.strip()
                subprocess.run(["wl-copy"], input=otp_code, text=True)
                print("🔑 OTP code copied to clipboard.")
            else:
                print("No OTP code found for this credential.")
        else:
            # Multiple credentials - use fzf for selection
            with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                for i, cred in enumerate(credentials):
                    title = cred.get("title", "Unknown")
                    login = cred.get("login", "") or cred.get("email", "")
                    display = f"{title} - {login}" if login else title
                    tmp.write(f"{i}: {display}\n")
                tmp_path = tmp.name

            try:
                # Use fzf for selection
                fzf_cmd = (
                    f'cat {tmp_path} | fzf --prompt="Select credential: " --height=10'
                )
                fzf_result = subprocess.run(
                    fzf_cmd, shell=True, capture_output=True, text=True
                )

                if fzf_result.returncode != 0:
                    print("Selection cancelled.")
                    return

                selection = fzf_result.stdout.strip()
                if not selection:
                    print("No selection made.")
                    return

                # Extract index from selection
                index = int(selection.split(":", 1)[0])
                credential = credentials[index]
                search_term = credential.get("title", "")

                # Get the actual OTP with console output
                otp_args = ["password", "-f", "otp", search_term, "-o", "console"]
                otp_output = execute_dcli(otp_args)

                # Check if we got a string result
                if isinstance(otp_output, int) or otp_output == "":
                    return

                if otp_output and not otp_output.startswith("Error"):
                    otp_code = otp_output.strip()
                    subprocess.run(["wl-copy"], input=otp_code, text=True)
                    print("🔑 OTP code copied to clipboard.")
                else:
                    print("No OTP code found for this credential.")
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
    except json.JSONDecodeError:
        print("Error parsing credential information.")
        # Fall back to handle_password with fzf
        handle_password(args, otp=True)


# Handle OTP retrieval after password
def get_otp_for_credential(search_term):
    # Get the OTP code with console output
    otp_args = ["password", "-f", "otp", search_term, "-o", "console"]
    otp_output = execute_dcli(otp_args)

    # Check if we got a string result
    if isinstance(otp_output, int) or otp_output == "":
        return False

    # Parse the output - if it's a single line, it's the OTP code
    if otp_output and not otp_output.startswith("Error"):
        # Strip any whitespace and newlines
        otp_code = otp_output.strip()

        # Copy to clipboard
        subprocess.run(["wl-copy"], input=otp_code, text=True)
        print("🔑 OTP code copied to clipboard.")
        return True
    else:
        print("No OTP code found in the credential.")
        return False


# Handle username extraction and copying
def handle_username(args):
    # Get original args but replace output format with json
    orig_args = args.copy()

    # Extract search terms (non-option arguments)
    search_terms = []
    for arg in orig_args:
        if not arg.startswith("-") and arg not in ["username", "u"]:
            search_terms.append(arg)

    # If no search terms, we can't proceed
    if not search_terms:
        print("No search terms provided.")
        return

    # Build the command to get password entry in JSON format
    search_args = ["password"] + search_terms + ["-o", "json"]

    # Execute command
    output = execute_dcli(search_args)

    # If we got an int (returncode) or empty string (interactive auth handled), exit early
    if isinstance(output, int) or output == "":
        return

    try:
        credentials = json.loads(output)

        if not credentials:
            print("No matching credentials found.")
            return

        # Handle single result
        if len(credentials) == 1:
            credential = credentials[0]

            # Try to get username or fall back to email if username not present
            username = credential.get("login", "")
            if not username:
                username = credential.get("email", "")

            if username:
                subprocess.run(["wl-copy"], input=username, text=True)
                print(
                    f"👤 Username for \"{credential.get('title', 'Unknown')}\" copied to clipboard."
                )
            else:
                print("No username or email found in the credential.")
        else:
            # Create temporary file for fzf selection
            with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                for i, cred in enumerate(credentials):
                    title = cred.get("title", "Unknown")
                    login = cred.get("login", "") or cred.get("email", "")
                    display = f"{title} - {login}" if login else title
                    tmp.write(f"{i}: {display}\n")
                tmp_path = tmp.name

            try:
                # Use fzf for selection
                fzf_cmd = (
                    f'cat {tmp_path} | fzf --prompt="Select credential: " --height=10'
                )
                fzf_result = subprocess.run(
                    fzf_cmd, shell=True, capture_output=True, text=True
                )

                if fzf_result.returncode != 0:
                    print("Selection cancelled.")
                    return

                selection = fzf_result.stdout.strip()
                if not selection:
                    print("No selection made.")
                    return

                # Extract index from selection
                index = int(selection.split(":", 1)[0])
                credential = credentials[index]

                # Try to get username or fall back to email if username not present
                username = credential.get("login", "")
                if not username:
                    username = credential.get("email", "")

                if username:
                    subprocess.run(["wl-copy"], input=username, text=True)
                    print(
                        f"👤 Username for \"{credential.get('title', 'Unknown')}\" copied to clipboard."
                    )
                else:
                    print("No username or email found in the credential.")
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
    except json.JSONDecodeError:
        print("Error parsing credential information.")


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
    # Check dependencies first
    check_dependencies()

    # If no arguments provided, show help
    if len(sys.argv) < 2:
        direct_execute_dcli(["--help"])
        sys.exit(0)

    # First argument is the command
    command = sys.argv[1]
    args = sys.argv[1:]  # Include the command itself

    # Handle specific commands
    if command in ["p", "password"]:
        success, search_term, has_otp = handle_password(args)

        # If password retrieval was successful and credential has OTP
        if success and has_otp:
            if prompt_for_otp():
                get_otp_for_credential(search_term)

    elif command in ["n", "note"]:
        handle_note(args)
    elif command in ["o", "otp"]:
        handle_direct_otp(args[1:])  # Skip the 'otp' command
    elif command in ["u", "username"]:
        handle_username(args)
    else:
        # For other commands, directly execute dcli with interactive I/O
        result = direct_execute_dcli(args)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
