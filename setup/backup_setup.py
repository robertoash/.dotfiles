"""
Backup and restore configs that get overwritten by applications.

For apps that break symlinks by writing new files (like sqlit), we:
1. Backup: Copy from home directory to dotfiles/machine/bkup with secrets masked
2. Restore: Copy from dotfiles/machine/bkup to home directory with secrets injected
"""

import json
import shutil
from pathlib import Path

from config import BACKUP_CONFIGS


def mask_secrets_in_json(data, masks):
    """
    Mask secrets in JSON data using json_path patterns.

    Args:
        data: Parsed JSON data
        masks: List of dicts with 'json_path' and 'placeholder'

    Returns:
        Modified data with secrets masked
    """
    for mask in masks:
        json_path = mask["json_path"]
        placeholder = mask["placeholder"]

        # Simple json_path parser for connections[*].field patterns
        if json_path.startswith("connections[*]."):
            field_path = json_path[len("connections[*]."):].split(".")
            if "connections" in data:
                for conn in data["connections"]:
                    obj = conn
                    for field in field_path[:-1]:
                        if field in obj:
                            obj = obj[field]
                    final_field = field_path[-1]
                    if final_field in obj and obj[final_field]:
                        obj[final_field] = placeholder

    return data


def is_sops_encrypted(file_path):
    """Check if a file is SOPS-encrypted"""
    try:
        with open(file_path, 'r') as f:
            content = f.read(1000)
            # JSON: ENC[AES256_GCM,...], YAML: sops: metadata
            return 'ENC[AES256_GCM,' in content or 'sops:' in content
    except:
        return False


def backup_configs(dotfiles_dir, hostname):
    """Backup configs from home directory to dotfiles with optional secrets masking"""
    print("\n💾 Backing up application configs...")

    machine_dir = dotfiles_dir / hostname

    for config_name, config in BACKUP_CONFIGS.items():
        source = config["source"]
        target = machine_dir / config["target"]
        secrets_mask = config.get("secrets_mask", {})

        if not source.exists():
            continue

        print(f"  📦 Backing up {config_name}...")

        # Create target directory
        target.mkdir(parents=True, exist_ok=True)

        # Copy directory contents
        if source.is_dir():
            for item in source.iterdir():
                source_file = item
                target_file = target / item.name

                # Check if file is already SOPS-encrypted
                if is_sops_encrypted(source_file):
                    # Already encrypted - just copy as-is
                    shutil.copy2(source_file, target_file)
                    print(f"    ✅ {item.name} (SOPS-encrypted)")
                # Check if this file needs secrets masking
                elif item.name in secrets_mask:
                    # JSON file with secrets to mask
                    with open(source_file) as f:
                        data = json.load(f)

                    data = mask_secrets_in_json(data, secrets_mask[item.name])

                    with open(target_file, 'w') as f:
                        json.dump(data, f, indent=2)

                    print(f"    ✅ {item.name} (secrets masked)")
                else:
                    # Regular file - just copy
                    shutil.copy2(source_file, target_file)
                    print(f"    ✅ {item.name}")


def restore_configs(dotfiles_dir, hostname, secrets):
    """
    Restore configs from dotfiles to home directory with secrets injected.

    Args:
        dotfiles_dir: Root dotfiles directory
        hostname: Machine hostname
        secrets: Dict mapping placeholders to actual values
    """
    print("\n📦 Restoring application configs...")

    machine_dir = dotfiles_dir / hostname

    for config_name, config in BACKUP_CONFIGS.items():
        source = machine_dir / config["target"]
        target = config["source"]
        secrets_mask = config.get("secrets_mask", {})

        if not source.exists():
            continue

        print(f"  📂 Restoring {config_name}...")

        # Create target directory
        target.mkdir(parents=True, exist_ok=True)

        # Copy directory contents
        if source.is_dir():
            for item in source.iterdir():
                source_file = item
                target_file = target / item.name

                # Check if this file has masked secrets
                if item.name in secrets_mask:
                    # JSON file with masked secrets - inject real values
                    with open(source_file) as f:
                        data = json.load(f)

                    # Replace placeholders with actual secrets
                    data_str = json.dumps(data)
                    for placeholder, value in secrets.items():
                        data_str = data_str.replace(placeholder, value)
                    data = json.loads(data_str)

                    with open(target_file, 'w') as f:
                        json.dump(data, f, indent=2)

                    print(f"    ✅ {item.name} (secrets injected)")
                else:
                    # Regular file - just copy
                    shutil.copy2(source_file, target_file)
                    print(f"    ✅ {item.name}")
