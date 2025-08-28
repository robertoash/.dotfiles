#!/usr/bin/env python3

import getpass
import json
import os
import subprocess
import sys
from pathlib import Path


class BukuDBSwitcher:
    def __init__(self):
        self.db_dir = Path.home() / ".local" / "share" / "buku"
        self.backup_dir = self.db_dir / "bkups"
        self.current_db_file = self.db_dir / "current_db.txt"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def get_current_db(self):
        if self.current_db_file.exists():
            return self.current_db_file.read_text().strip()
        return "rash"

    def switch_db(self, target_db):
        target_db = target_db.replace(".db", "")
        
        if target_db == "bookmarks":
            print("Error: target_db cannot be bookmarks")
            return False
        
        current_db = self.get_current_db()
        
        # Handle encrypted database (rashp)
        if target_db == "rashp":
            gpg_file = self.db_dir / "rashp.db.gpg"
            if gpg_file.exists():
                # Decrypt rashp.db
                try:
                    subprocess.run(
                        ["gpg", "--decrypt", "--output", str(self.db_dir / "rashp.db"), str(gpg_file)],
                        check=True
                    )
                    gpg_file.unlink()
                except subprocess.CalledProcessError:
                    print("Decryption failed. Aborting database switch.")
                    return False
        
        # Check if current database should be encrypted (has bookmark #1 with title "Pass")
        if current_db != "bookmarks" and (self.db_dir / f"{current_db}.db").exists():
            # Check if bookmark #1 has title "Pass"
            password = None
            try:
                # Get bookmark #1 as JSON with minimal fields
                result = subprocess.run(
                    ["buku", "--db", str(self.db_dir / f"{current_db}.db"), "-f", "40", "-j", "-p", "1"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    bookmark = json.loads(result.stdout)
                    if bookmark.get("title") == "Pass":
                        password = bookmark.get("uri", "")
            except:
                pass
            
            if password:
                # Use extracted password to encrypt
                subprocess.run(
                    ["gpg", "-c", "--batch", "--yes", "--passphrase", password, 
                     "--cipher-algo", "AES256", str(self.db_dir / f"{current_db}.db")],
                    capture_output=True
                )
                (self.db_dir / f"{current_db}.db").unlink()
            # If no "Pass" entry found, leave unencrypted
        
        # Create target database file if it doesn't exist
        target_file = self.db_dir / f"{target_db}.db"
        if not target_file.exists() and not (self.db_dir / f"{target_db}.db.gpg").exists():
            target_file.touch()
            print(f"Created empty database: {target_file}")
        
        # Update symlink
        symlink = self.db_dir / "bookmarks.db"
        symlink.unlink(missing_ok=True)
        symlink.symlink_to(target_file.name)
        
        # Save current database name
        self.current_db_file.write_text(target_db)
        
        # Set BROWSER environment variable for buku integration
        os.environ["BROWSER"] = str(Path.home() / ".config" / "scripts" / "shell" / "buku_browser_wrapper.py")
        
        return True

    def get_current_db_info(self):
        current_db = self.get_current_db()
        symlink = self.db_dir / "bookmarks.db"
        
        if symlink.exists() and symlink.is_symlink():
            real_target = symlink.resolve()
            print(f"Current database: {current_db}")
            print(f"Symlink points to: {real_target}")
        else:
            print(f"Current database (from file): {current_db}")
            print("Warning: bookmarks.db symlink does not exist")


def main():
    switcher = BukuDBSwitcher()
    
    if len(sys.argv) < 2:
        target_db = "rash"
    else:
        target_db = sys.argv[1]
    
    if target_db in ["--help", "-h", "help"]:
        print("""bk_swap - Switch between buku bookmark databases

Usage:
    bk_swap [database_name]    Switch to database
    bk_swap current            Show current database info
    bk_swap --help             Show this help

Examples:
    bk_swap rash              Switch to rash database
    bk_swap rashp             Switch to encrypted rashp database
    bk_swap work              Switch to work database (creates if missing)
    
Notes:
- Databases with bookmark #1 titled "Pass" are auto-encrypted
- Password stored in the URL field of the "Pass" bookmark
- Exit handlers automatically encrypt on shell exit""")
        return
    
    if target_db == "current":
        switcher.get_current_db_info()
        return
    
    # Check if database exists
    target_db = target_db.replace(".db", "")
    db_file = switcher.db_dir / f"{target_db}.db"
    gpg_file = switcher.db_dir / f"{target_db}.db.gpg"
    
    if not db_file.exists() and not gpg_file.exists() and target_db != "rash":
        # Database doesn't exist, offer to create encrypted version
        response = input(f"Database '{target_db}' doesn't exist. Create new encrypted database? (y/N): ")
        if response.lower() == 'y':
            # Switch to new empty database
            switcher.switch_db(target_db)
            
            # Prompt for password and add as bookmark #1
            password = getpass.getpass(f"Enter encryption password for {target_db}: ")
            subprocess.run([
                "buku", "--db", str(db_file),
                "-a", password, 
                "--title", "Pass"
            ], capture_output=True)
            
            # Switch back to rash (this will encrypt the new db)
            switcher.switch_db("rash")
            print(f"Created encrypted database: {target_db}.db.gpg")
        return
    
    if switcher.switch_db(target_db):
        if target_db != "rashp":
            print(f"Switched to database: {target_db}")


if __name__ == "__main__":
    main()