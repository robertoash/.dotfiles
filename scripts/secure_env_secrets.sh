#! /bin/bash
# Decrypt, source, and re-encrypt secrets files

# List of secret files
SECRETS_FILES=(
    '/home/rash/.secrets/.hass-cli_conf'
)
GPG_ID=j.roberto.ash@gmail.com

profile_decrypt() {
    local file=$1
    local encrypted_file="${file}.asc"
    if [[ -f "$encrypted_file" ]]; then
        gpg --quiet -d "$encrypted_file" > "$file" # Decrypt files
        rm "$encrypted_file"
    fi
}

profile_encrypt() {
    local file=$1
    gpg --quiet -ea -r ${GPG_ID} "$file" # Encrypt files using ascii output
    rm "$file"
}

# Decrypt, source, and re-encrypt each file
for file in "${SECRETS_FILES[@]}"; do
    profile_decrypt "$file"
    source "$file"
    profile_encrypt "$file"
done
