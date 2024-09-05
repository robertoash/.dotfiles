#!/usr/bin/env python3

import fcntl
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class BukuDBSwitcher:
    def __init__(self):
        self.db_dir = Path.home() / ".local" / "share" / "buku"
        self.backup_dir = self.db_dir / "bkups"
        self.current_db_file = self.db_dir / "current_db.txt"
        self.is_switch_startup = True
        self.original_browser = os.environ.get("BROWSER", "zen-browser")
        os.environ["ORIGINAL_BROWSER"] = self.original_browser
        # Create a temporary lock file path
        self.lock_file_path = Path(tempfile.gettempdir()) / "switch_buku.lock"
        self.lock_file = None

    def acquire_lock(self):
        self.lock_file = open(self.lock_file_path, "w")
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # Print error if launched manually and not via .zshrc
            if not self.is_switch_startup:
                print("Another instance is running. Exiting.")
            sys.exit(1)

    def release_lock(self):
        if self.lock_file:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()

    def set_browser_mode(self):
        os.environ["BROWSER"] = str(
            Path.home() / ".config" / "scripts" / "shell" / "buku_browser_wrapper.py"
        )

    def monitor_bookmarks_db(self, target_db):
        while True:
            if list(self.db_dir.glob("bookmarks.db*")):
                self.current_db_file.write_text(target_db)
                self.set_browser_mode()
                break

    def get_suffix(self, file):
        return file.suffix[3:] if file.suffix.startswith(".db") else ""

    def get_current_db_path(self):
        current_db = self.get_current_db()
        real_location = next(
            self.db_dir.glob("bookmarks.db*"),
            "nonexistent and waiting for its creation",
        )
        substituted_location = self.db_dir / f"{current_db}{real_location.suffix}"
        print(f"Real location: {real_location}")
        print(f"Substituted location: {substituted_location}")

    def create_or_update_backup(self, file):
        from datetime import datetime

        # Get todays date
        today = datetime.now().strftime("%Y%m%d")

        file_path = Path(file)  # Convert to Path object
        base_name = file_path.stem  # Get the base name without extension
        extension = file_path.suffix  # Get the file extension
        backup = ""

        # Remove .db suffix if present
        base_name = base_name.rstrip(".db")

        if extension == ".gpg":
            backup = self.backup_dir / f"{base_name}_{today}.backup.gpg"
        else:
            backup = self.backup_dir / f"{base_name}_{today}.backup"

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup.unlink(missing_ok=True)  # Remove existing backup if it exists
        shutil.copy(file, backup)  # Copy the original file to the backup location

    def switch_db(self, target_db, encrypt_flag=False):
        target_db = Path(target_db).with_suffix(".db")
        current_db = self.get_current_db()

        if self.check_startup_scenario(target_db, current_db):
            return

        if target_db.name == "bookmarks.db":
            print("Error: target_db cannot be bookmarks.db")
            return

        current_suffix = self.get_current_suffix()
        target_suffix = self.get_target_suffix(target_db)

        if not self.rename_current_db(current_db, current_suffix):
            return

        self.encrypt_current_db_if_needed(current_db, current_suffix, encrypt_flag)

        if not self.handle_target_db(target_db, target_suffix):
            self.rollback_changes(
                True, False, current_db, current_suffix, target_db, target_suffix
            )
            return

        self.simulate_rashp_error(target_db)

        self.finalize_switch(target_db)

    def check_startup_scenario(self, target_db, current_db):
        return (
            (self.db_dir / "bookmarks.db").exists()
            and not (self.db_dir / target_db).exists()
            and target_db == current_db
        )

    def simulate_rashp_error(self, target_db):
        if target_db.name == "rashp.db":
            print("Database 'rashp.db' is corrupted and cannot be loaded.")

    def get_current_suffix(self):
        for file in self.db_dir.glob("bookmarks.db*"):
            return self.get_suffix(file)
        return ""

    def get_target_suffix(self, target_db):
        for file in self.db_dir.glob(f"{target_db.stem}*"):
            return self.get_suffix(file)
        return ""

    def rename_current_db(self, current_db, current_suffix):
        current_file = self.db_dir / f"bookmarks.db{current_suffix}"
        if current_file.exists():
            new_file = self.db_dir / f"{current_db}{current_suffix}"
            if new_file.exists():
                print(
                    f"Error: Cannot rename current db. File {new_file} already exists."
                )
                return False
            try:
                current_file.rename(new_file)
            except OSError:
                print("Error: Failed to rename current database.")
                return False
        return True

    def encrypt_current_db_if_needed(self, current_db, current_suffix, encrypt_flag):
        if current_db == "rashp.db" or encrypt_flag:
            file = self.db_dir / f"{current_db}{current_suffix}"
            subprocess.run(
                ["gpg", "-c", "--cipher-algo", "AES256", str(file)], check=True
            )
            file.unlink()
            print(f"Current database encrypted: {file}.gpg")

    def handle_target_db(self, target_db, target_suffix):
        target_file = self.db_dir / f"{target_db}{target_suffix}"
        gpg_file = self.db_dir / f"{target_db}.gpg"

        if (
            not target_file.exists()
            and not gpg_file.exists()
            and self.is_switch_startup
        ):
            target_file.touch()
            print(f"Created empty database: {target_file}")

        if target_file.exists() or gpg_file.exists():
            return self.handle_existing_target_db(target_db, target_suffix)
        else:
            print(f"Error: Target database {target_db} not found.")
            return False

    def handle_existing_target_db(self, target_db, target_suffix):
        gpg_file = self.db_dir / f"{target_db}.gpg"
        if gpg_file.exists():
            self.create_or_update_backup(gpg_file)
            try:
                subprocess.run(
                    [
                        "gpg",
                        "--decrypt",
                        "--output",
                        str(self.db_dir / target_db),
                        str(gpg_file),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                print("Decryption failed. Aborting database switch.")
                return False
        else:
            self.create_or_update_backup(self.db_dir / f"{target_db}{target_suffix}")

        if (self.db_dir / f"{target_db}.gpg").exists():
            subprocess.run(
                ["gpg", "-d", str(self.db_dir / f"{target_db}.gpg")],
                stdout=open(str(self.db_dir / target_db), "wb"),
                check=True,
            )
            (self.db_dir / f"{target_db}.gpg").unlink()
            target_suffix = ""

        new_file = self.db_dir / f"bookmarks.db{target_suffix}"
        if new_file.exists():
            print(
                f"Error: Cannot rename target database. File {new_file} already exists."
            )
            return False
        try:
            (self.db_dir / f"{target_db}{target_suffix}").rename(new_file)
        except OSError:
            print("Error: Failed to rename target database.")
            return False

        if not self.is_switch_startup and target_db != "rashp.db":
            pass  # Commented out: print(f"Database '{target_db}' loaded successfully.")
        return True

    def finalize_switch(self, target_db):
        self.current_db_file.write_text(str(target_db))
        self.set_browser_mode()

    def rollback_changes(
        self,
        renamed_current,
        renamed_target,
        current_db,
        current_suffix,
        target_db,
        target_suffix,
    ):
        if renamed_current:
            (self.db_dir / f"{current_db}{current_suffix}").rename(
                self.db_dir / f"bookmarks.db{current_suffix}"
            )
        if renamed_target:
            (self.db_dir / f"bookmarks.db{target_suffix}").rename(
                self.db_dir / f"{target_db}{target_suffix}"
            )
        print("Changes rolled back due to an error.")

    def get_current_db(self):
        return (
            self.current_db_file.read_text().strip()
            if self.current_db_file.exists()
            else "rash.db"
        )

    def run(self, target_db=None, encrypt_flag=False, is_switch_startup=True):
        self.acquire_lock()
        try:
            if not self.current_db_file.exists():
                self.current_db_file.write_text("rash.db")

            current_db = self.get_current_db()

            if current_db == "rashp.db":
                encrypt_flag = True

            # Set the startup state
            self.is_switch_startup = is_switch_startup

            if target_db == "current":
                self.get_current_db_path()
            else:
                self.switch_db(target_db, encrypt_flag)

            self.is_switch_startup = False
        finally:
            self.release_lock()


if __name__ == "__main__":
    import sys

    switcher = BukuDBSwitcher()
    encrypt_flag = "--enc" in sys.argv
    target_db = next(
        (arg for arg in sys.argv[1:] if arg != "--enc" and arg != "--startup"), "rash"
    )
    is_switch_startup = "--startup" in sys.argv
    switcher.run(target_db, encrypt_flag, is_switch_startup)
