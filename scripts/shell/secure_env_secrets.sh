#! /bin/bash
# Decrypt, source, and re-encrypt secrets files

# Lock file location
# This file is used by flock to manage script execution access.
LOCK_FILE="/tmp/secrets_script.lock"

# List of secret files
SECRETS_FILES=(
    '/home/rash/.secrets/.hass-cli_conf'
    '/home/rash/.secrets/.shell-gpt_conf'
)
GPG_ID=j.roberto.ash@gmail.com

conf_source() {
    local file=$1
    if [[ -s "$file" ]]; then
        source "$file"
        if [ $? -eq 0 ]; then
            #echo "Sourced $file successfully."
            :
        else
            echo "Error: Sourcing $file failed."
            return 1
        fi
    else
        echo "Error: $file is empty or missing."
        return 1
    fi
}

conf_encrypt() {
    local file=$1
    gpg --yes --quiet -ea -r ${GPG_ID} "$file" # Encrypt files using ascii output
    if [ $? -eq 0 ]; then
        # echo "Encryption successful for $file."
        rm "$file" # Remove source file if encryption is successful
    else
        echo "Encryption failed for $file."
        return 1
    fi
}

conf_decrypt() {
    local file=$1
    local encrypted_file="${file}.asc"
    if [[ -f "$encrypted_file" ]]; then
        decrypted_content=$(gpg --quiet -d "$encrypted_file")
        decrypt_status=$?
        if [ $decrypt_status -eq 0 ]; then
            # echo "Decryption successful for $encrypted_file."
            echo "$decrypted_content" > "$file"
            if [[ -s "$file" ]]; then
                conf_source "$file"
                conf_encrypt "$file"
            else
                echo "Error: Decrypted file $file is empty."
                return 1
            fi
        else
            echo "Error: Decryption failed for $encrypted_file with status $decrypt_status."
            return 1
        fi
    else
        echo "Error: Encrypted file $encrypted_file not found."
        return 1
    fi
}

{
    # The flock command acquires an exclusive lock on file descriptor 200, linked to the LOCK_FILE.
    # If the lock is not available (meaning another instance of the script has it), this command waits until the lock can be acquired.
    # Once the script execution completes, the lock is automatically released, allowing the next waiting script instance to proceed.
    flock -x 200

    # Process each file
    for file in "${SECRETS_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            # If _conf file exists, encrypt it and delete original
            conf_encrypt "$file"
        elif [[ -f "${file}.asc" ]]; then
            # If only .asc file exists, decrypt it, source it, and re-encrypt
            conf_decrypt "$file"
        else
            echo "Error: Neither $file nor ${file}.asc exists."
        fi
    done

 } 200>"${LOCK_FILE}"
