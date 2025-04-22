#!/usr/bin/env python3
import argparse
import fcntl
import logging
import os
import subprocess
import sys

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Retrieve environment secrets.")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Configure logging in quiet mode
logging_utils.configure_logging(quiet=True)
logger = logging.getLogger()

# Override the console handler to use stderr instead of stdout
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        handler.stream = sys.stderr

# Set log level based on debug flag
logger.setLevel(logging.DEBUG if args.debug else logging.ERROR)

# Lock file location
lock_file = "/tmp/secrets_script.lock"

# List of secret files
secrets_files = [
    "/home/rash/.secrets/.hass-cli_conf",
    "/home/rash/.secrets/.tibber_token",
    "/home/rash/.secrets/.sp_secrets",
    "/home/rash/.secrets/.cjar_secrets",
    "/home/rash/.secrets/.openai_api_key",
]
gpg_id = "j.roberto.ash@gmail.com"


def conf_source(file):
    if os.path.getsize(file) > 0:
        try:
            with open(file) as f:
                for line in f:
                    if line.strip() and not line.strip().startswith("#"):
                        key, value = line.strip().split("=", 1)
                        print(f'export {key}="{value.strip()}"')
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
            # Write the decrypted content back to a file
            with open(file, "w") as f:
                f.write(decrypted_content)
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
    with open(lock_file, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        for file in secrets_files:
            if os.path.isfile(file):
                conf_encrypt(file)
            if os.path.isfile(f"{file}.asc"):
                conf_decrypt(file)
                conf_source(file)
                conf_encrypt(file)
            else:
                logging.error(f"Error: Neither {file} nor {file}.asc exists.")


if __name__ == "__main__":
    main()
