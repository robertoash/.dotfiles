#! /bin/bash
# Decrypt, source, and re-encrypt secrets files

# List of secret files
SECRETS_FILES=(
    '/home/rash/.secrets/.hass-cli_conf'
)
GPG_ID=j.roberto.ash@gmail.com

profile_source() {
    local file=$1
    # Check if file is not empty
    if [[ -s "$file" ]]; then
        source "$file"
    else
        echo "Error: $file is empty or missing."
        return 1
    fi
}

profile_decrypt() {
    local file=$1
    local encrypted_file="${file}.asc"
    if [[ -f "$encrypted_file" ]]; then
        gpg --quiet -d "$encrypted_file" > "$file" # Decrypt files
        if [ $? -eq 0 ]; then
            rm "$encrypted_file"
        else
            echo "Decryption failed for $encrypted_file"
            return 1
        fi
    fi
}

profile_encrypt() {
    local file=$1
    gpg --quiet -ea -r ${GPG_ID} "$file" # Encrypt files using ascii output
    if [ $? -eq 0 ]; then
        rm "$file"
    else
        echo "Encryption failed for $file"
        return 1
    fi
}

# Decrypt, source, and re-encrypt each file
for file in "${SECRETS_FILES[@]}"; do
    profile_decrypt "$file"
    if [ $? -eq 0 ]; then
        profile_source "$file"
        if [ $? -eq 0 ]; then
            profile_encrypt "$file"
            if [ $? -ne 0 ]; then
                echo "Failed to re-encrypt $file, leaving it decrypted."
            fi
        else
            echo "Failed to source $file. It will not be re-encrypted."
        fi
    else
        echo "Skipping $file due to decryption failure."
    fi
done
