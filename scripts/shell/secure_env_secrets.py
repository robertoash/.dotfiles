#!/usr/bin/env python3
import fcntl
import os
import subprocess
import sys

# Lock file location
lock_file = "/tmp/secrets_script.lock"

# List of secret files
secrets_files = [
    "/home/rash/.secrets/.hass-cli_conf",
    "/home/rash/.secrets/.tibber_token",
    "/home/rash/.secrets/.sp_secrets"
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
            print(f"Error: Sourcing {file} failed. {e}", file=sys.stderr)
            return False
    else:
        print(f"Error: {file} is empty or missing.", file=sys.stderr)
        return False
    return True


def conf_encrypt(file):
    encrypt_cmd = f"gpg --yes --quiet -ea -r {gpg_id} {file}"
    try:
        subprocess.check_call(encrypt_cmd, shell=True)
        # After successful encryption, delete the unencrypted file
        os.remove(file)  # This line deletes the original file after encryption
    except subprocess.CalledProcessError as e:
        print(
            f"Encryption failed for {file} with status {e.returncode}", file=sys.stderr
        )
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
            print(
                f"Error: Decryption failed for {encrypted_file} "
                f"with status {e.returncode}.",
                file=sys.stderr,
            )
            return False
    else:
        print(
            f"Error: Encrypted file {encrypted_file} not found.",
            file=sys.stderr,
        )
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
                print(f"Error: Neither {file} nor {file}.asc exists.", file=sys.stderr)


if __name__ == "__main__":
    main()
