#!/usr/bin/env python3
import argparse
import fcntl
import logging
import os
import shlex
import subprocess
import sys

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# Lock file location
lock_file = "/tmp/secrets_script.lock"

# List of secret files
secrets_files = [
    "/home/rash/.secrets/.hass-cli_conf",
    "/home/rash/.secrets/.tibber_token",
    "/home/rash/.secrets/.sp_secrets",
    "/home/rash/.secrets/.cjar_secrets",
    "/home/rash/.secrets/.openai_api_key",
    "/home/rash/.secrets/.linkding_envs",
    "/home/rash/.secrets/.anthropic_api_key",
    "/home/rash/.secrets/.github_access_token",
    "/home/rash/.secrets/.rash_gmail_pass",
]
gpg_id = "j.roberto.ash@gmail.com"


def detect_shell():
    """Detect the current shell being used."""
    # Check parent process name
    try:
        ppid = os.getppid()
        with open(f"/proc/{ppid}/comm", "r") as f:
            parent_name = f.read().strip()
        if parent_name in ["fish"]:
            return "fish"
        elif parent_name in ["bash", "zsh", "sh"]:
            return "posix"
    except (OSError, FileNotFoundError):
        pass

    # Fallback to SHELL environment variable
    shell = os.environ.get("SHELL", "")
    if "fish" in shell:
        return "fish"
    else:
        return "posix"  # Default to POSIX (bash/zsh) syntax


def configure_logging(args):
    # Configure logging in quiet mode
    logging_utils.configure_logging(quiet=True)
    logger = logging.getLogger()

    # Override the console handler to use stderr instead of stdout
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.stream = sys.stderr

    # Set log level based on debug flag
    logger.setLevel(logging.DEBUG if args.debug else logging.ERROR)


def conf_source(file, shell_type=None):
    if shell_type is None:
        shell_type = detect_shell()

    if os.path.getsize(file) > 0:
        try:
            if shell_type == "fish":
                # For Fish, we need to output in a format that works with eval
                commands = []
                with open(file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Strip 'export ' prefix if present to make files shell-agnostic
                            if line.startswith("export "):
                                line = line[7:]  # Remove 'export ' prefix

                            # Ensure we have a key=value pair, handle empty values
                            if "=" not in line:
                                continue  # Skip malformed lines

                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            # Remove quotes if they exist
                            if (value.startswith('"') and value.endswith('"')) or (
                                value.startswith("'") and value.endswith("'")
                            ):
                                value = value[1:-1]

                            # Fish needs proper escaping
                            escaped_value = value.replace("'", "\\'")
                            commands.append(f"set -gx {key} '{escaped_value}'")

                # Output commands separated by newlines for Fish
                for cmd in commands:
                    print(cmd)
            else:
                # Original logic for bash/zsh
                with open(file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Strip 'export ' prefix if present
                            if line.startswith("export "):
                                line = line[7:]

                            # Ensure we have a key=value pair
                            if "=" not in line:
                                continue

                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            # Remove quotes if they exist
                            if (value.startswith('"') and value.endswith('"')) or (
                                value.startswith("'") and value.endswith("'")
                            ):
                                value = value[1:-1]

                            print(f'export {key}="{value}"')

        except Exception as e:
            logging.error(f"Error: Sourcing {file} failed. {e}")
            return False
    else:
        logging.error(f"Error: {file} is empty or missing.")
        return False
    return True


def conf_encrypt(file):
    encrypt_cmd = f"gpg --yes --quiet -ea -r {gpg_id} {file}"
    try:
        subprocess.check_call(encrypt_cmd, shell=True)
        # After successful encryption, delete the unencrypted file
        os.remove(file)  # This line deletes the original file after encryption
    except subprocess.CalledProcessError as e:
        logging.error(f"Encryption failed for {file} with status {e.returncode}")
        return False
    return True


def conf_decrypt(file):
    encrypted_file = f"{file}.asc"
    if os.path.isfile(encrypted_file):
        try:
            decrypted_content = subprocess.check_output(
                f"gpg --quiet -d {encrypted_file}", shell=True
            ).decode()

            # Normalize the content to shell-agnostic format
            # Supports: KEY=VALUE, export KEY=VALUE, set [-flags] KEY "quoted value"
            normalized_lines = []
            for line in decrypted_content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Strip 'export ' prefix if present to standardize format
                    if line.startswith("export "):
                        line = line[7:]  # Remove 'export ' prefix
                        # Handle fish shell syntax: set [-gx|-g|-x] KEY VALUE
                    elif line.startswith("set "):
                        try:
                            # Parse fish set command with proper quote handling
                            parts = shlex.split(line)
                            if len(parts) >= 3:
                                # Handle flags like -gx, -g, -x
                                key_index = 1
                                if parts[1].startswith("-"):
                                    key_index = 2

                                if len(parts) > key_index:
                                    key = parts[key_index]
                                    # Join remaining parts as value, handling spaces
                                    value = " ".join(parts[key_index + 1 :])
                                    line = f"{key}={value}"
                                else:
                                    # Malformed fish command, skip
                                    continue
                            else:
                                # Malformed fish command, skip
                                continue
                        except ValueError:
                            # shlex.split failed (unmatched quotes, etc.), skip line
                            continue
                    normalized_lines.append(line)
                else:
                    # Keep comments and empty lines as-is
                    normalized_lines.append(line)

            # Write the normalized content back to file
            with open(file, "w") as f:
                f.write("\n".join(normalized_lines))
                if normalized_lines and not decrypted_content.endswith("\n"):
                    f.write("\n")  # Ensure file ends with newline

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Error: Decryption failed for {encrypted_file} "
                f"with status {e.returncode}."
            )
            return False
    else:
        logging.error(f"Error: Encrypted file {encrypted_file} not found.")
        return False
    return True


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Retrieve environment secrets.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--decrypt", help="Decrypt a file")
    parser.add_argument("--edit", help="Edit a file")
    parser.add_argument(
        "--shell",
        choices=["fish", "posix"],
        help="Override shell detection (fish or posix)",
    )
    args = parser.parse_args()

    configure_logging(args)

    if args.decrypt:
        file = args.decrypt.removesuffix(".asc")
        if conf_decrypt(file):
            print(f"✅ Decrypted to: {file}")
        else:
            sys.exit(1)
        return

    if args.edit:
        file = args.edit.removesuffix(".asc")
        if not conf_decrypt(file):
            sys.exit(1)
        editor = os.environ.get("EDITOR", "nvim")
        subprocess.run([editor, file])
        if not conf_encrypt(file):
            sys.exit(1)
        print(f"🔒 Re-encrypted: {file} → {file}.asc")
        return

    shell_type = args.shell if args.shell else detect_shell()

    with open(lock_file, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        for file in secrets_files:
            if os.path.isfile(file):
                conf_encrypt(file)
            if os.path.isfile(f"{file}.asc"):
                conf_decrypt(file)
                conf_source(file, shell_type)
                conf_encrypt(file)
            else:
                logging.error(f"Error: Neither {file} nor {file}.asc exists.")


if __name__ == "__main__":
    main()
