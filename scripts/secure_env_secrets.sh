#! /bin/bash
# Decrypt, source, and re-encrypt secrets files

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
    else
        echo "Error: $file is empty or missing."
        return 1
    fi
}

conf_encrypt() {
    local file=$1
    gpg --yes --quiet -ea -r ${GPG_ID} "$file" # Encrypt files using ascii output
    if [ $? -eq 0 ]; then
        rm "$file" # Remove source file if encryption is successful
    else
        echo "Encryption failed for $file"
        return 1
    fi
}

conf_decrypt() {
    local file=$1
    local encrypted_file="${file}.asc"
    if [[ -f "$encrypted_file" ]]; then
        gpg --quiet -d "$encrypted_file" > "$file" # Decrypt files
        if [ $? -eq 0 ]; then
            conf_source "$file"
            conf_encrypt "$file"
        else
            echo "Decryption failed for $encrypted_file"
            return 1
        fi
    else
        echo "Encrypted file $encrypted_file not found."
        return 1
    fi
}

# Process each file
for file in "${SECRETS_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        # If _conf file exists, encrypt it
        conf_encrypt "$file"
    fi
    # Process the .asc file regardless
    conf_decrypt "$file"
done
