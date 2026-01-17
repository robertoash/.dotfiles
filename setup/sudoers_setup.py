"""
Setup sudoers.d configuration.
"""

import subprocess
from pathlib import Path


def setup_sudoers(dotfiles_dir):
    """Setup sudoers.d configuration (Linux only)"""
    print("\n🔒 Step 6.1: Setting up sudoers.d configuration...")
    sudoers_source_dir = dotfiles_dir / "system" / "sudoers.d"
    sudoers_target_dir = Path("/etc/sudoers.d")

    if sudoers_source_dir.exists():
        sudoers_files = list(sudoers_source_dir.glob("*"))

        if sudoers_files:
            for sudoers_file in sudoers_files:
                if sudoers_file.name.startswith('.'):
                    continue  # Skip hidden files

                target_file = sudoers_target_dir / sudoers_file.name

                # Check if file already exists and is identical
                needs_update = True
                if target_file.exists():
                    source_content = sudoers_file.read_text()
                    target_content = target_file.read_text()
                    if source_content == target_content:
                        needs_update = False
                        print(f"  ✅ {sudoers_file.name} is already up to date")

                if needs_update:
                    print(f"  🔒 Installing {sudoers_file.name} (requires sudo)...")
                    print(f"     Validating syntax with visudo...")

                    # Validate syntax first using visudo
                    validate_result = subprocess.run(
                        ["sudo", "visudo", "-cf", str(sudoers_file)]
                    )

                    if validate_result.returncode == 0:
                        print(f"     Installing to /etc/sudoers.d/...")
                        # Copy file to /etc/sudoers.d/ with correct permissions (0440)
                        copy_result = subprocess.run(
                            ["sudo", "install", "-m", "0440", str(sudoers_file), str(target_file)]
                        )

                        if copy_result.returncode == 0:
                            print(f"  ✅ Installed {sudoers_file.name} to /etc/sudoers.d/")
                        else:
                            print(f"  ⚠️  Failed to install {sudoers_file.name}")
                    else:
                        print(f"  ❌ Syntax error in {sudoers_file.name}")
                        print(f"  ⚠️  Skipping installation to prevent system misconfiguration")
        else:
            print("  ℹ️  No sudoers files found in system/sudoers.d/")
    else:
        print("  ℹ️  system/sudoers.d/ directory not found")
