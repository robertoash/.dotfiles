"""
Setup /etc/security/ configuration files.
"""

import subprocess
from pathlib import Path


def setup_security(dotfiles_dir):
    """Setup /etc/security/ configuration (Linux only)"""
    print("\n🔒 Step 6.2: Setting up /etc/security/ configuration...")

    # Check for both common and hostname-specific security configs
    security_source_paths = [
        dotfiles_dir / "common" / "etc" / "security",
        # Could add hostname-specific later if needed
    ]

    security_target_dir = Path("/etc/security")

    found_files = False
    for security_source_dir in security_source_paths:
        if not security_source_dir.exists():
            continue

        security_files = list(security_source_dir.glob("*"))

        if security_files:
            found_files = True
            for security_file in security_files:
                if security_file.name.startswith('.') or not security_file.is_file():
                    continue  # Skip hidden files and directories

                target_file = security_target_dir / security_file.name

                # Check if file already exists and is identical
                needs_update = True
                if target_file.exists():
                    source_content = security_file.read_text()
                    target_content = target_file.read_text()
                    if source_content == target_content:
                        needs_update = False
                        print(f"  ✅ {security_file.name} is already up to date")

                if needs_update:
                    print(f"  🔒 Installing {security_file.name} to /etc/security/ (requires sudo)...")

                    # Copy file to /etc/security/ with correct permissions (0644)
                    copy_result = subprocess.run(
                        ["sudo", "install", "-m", "0644", str(security_file), str(target_file)]
                    )

                    if copy_result.returncode == 0:
                        print(f"  ✅ Installed {security_file.name} to /etc/security/")
                    else:
                        print(f"  ⚠️  Failed to install {security_file.name}")

    if not found_files:
        print("  ℹ️  No security config files found")
