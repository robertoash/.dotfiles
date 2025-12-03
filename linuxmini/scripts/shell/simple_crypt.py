#!/usr/bin/env python3
import argparse
import os
import sys
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def derive_key(password, salt):
    """Derive encryption key from password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_file(filepath):
    """Encrypt a file with password."""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found")
        return False
    
    password = getpass.getpass("Enter password: ")
    salt = os.urandom(16)
    key = derive_key(password, salt)
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    
    # Write salt + encrypted data
    with open(f"{filepath}.enc", 'wb') as f:
        f.write(salt + encrypted_data)
    
    os.remove(filepath)
    print(f"🔒 Encrypted: {filepath} → {filepath}.enc")
    return True

def decrypt_file(filepath):
    """Decrypt a file with password."""
    if filepath.endswith('.enc'):
        encrypted_file = filepath
        output_file = filepath[:-4]  # Remove .enc
    else:
        encrypted_file = f"{filepath}.enc"
        output_file = filepath
    
    if not os.path.exists(encrypted_file):
        print(f"Error: Encrypted file {encrypted_file} not found")
        return False
    
    password = getpass.getpass("Enter password: ")
    
    with open(encrypted_file, 'rb') as f:
        salt = f.read(16)  # First 16 bytes are salt
        encrypted_data = f.read()
    
    key = derive_key(password, salt)
    fernet = Fernet(key)
    
    try:
        decrypted_data = fernet.decrypt(encrypted_data)
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
        print(f"🔓 Decrypted: {encrypted_file} → {output_file}")
        return True
    except Exception as e:
        print(f"Error: Decryption failed. Wrong password?")
        return False

def main():
    parser = argparse.ArgumentParser(description="Simple file encryption/decryption")
    parser.add_argument("-e", "--encrypt", help="Encrypt a file")
    parser.add_argument("-d", "--decrypt", help="Decrypt a file")
    
    args = parser.parse_args()
    
    if not (args.encrypt or args.decrypt):
        parser.print_help()
        sys.exit(1)
    
    if args.encrypt:
        if not encrypt_file(args.encrypt):
            sys.exit(1)
    
    if args.decrypt:
        if not decrypt_file(args.decrypt):
            sys.exit(1)

if __name__ == "__main__":
    main()