"""
Claude Code configuration setup with sops-encrypted secrets.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def decrypt_secrets(secrets_file):
    """Decrypt sops secrets file and return as dict"""
    try:
        # Set age key file path to speed up decryption
        env = os.environ.copy()
        age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"
        if age_key_file.exists():
            env["SOPS_AGE_KEY_FILE"] = str(age_key_file)

        result = subprocess.run(
            ["sops", "-d", str(secrets_file)],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        # Parse YAML output - simple parser to avoid PyYAML dependency
        secrets = {}
        for line in result.stdout.split('\n'):
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                secrets[key.strip()] = value.strip()
        return secrets
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error decrypting secrets: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  Error parsing secrets: {e}", file=sys.stderr)
        return None


def substitute_secrets(template_str, secrets):
    """Replace {{PLACEHOLDER}} with actual secret values"""
    replacements = {
        "{{CLAUDE_GITHUB_TOKEN}}": secrets.get("github-token", ""),
        "{{CLAUDE_HA_TOKEN_GLOBAL}}": secrets.get("ha-token-global", ""),
        "{{OBSIDIAN_API_KEY}}": secrets.get("obsidian-api-key", ""),
        "{{JIRA_URL}}": secrets.get("jira-url", ""),
        "{{JIRA_USERNAME}}": secrets.get("jira-username", ""),
        "{{JIRA_API_TOKEN}}": secrets.get("jira-api-token", ""),
    }

    for placeholder, value in replacements.items():
        template_str = template_str.replace(placeholder, value)

    return template_str


def setup_claude_config(dotfiles_dir, hostname=None):
    """Setup Claude Code MCP servers with encrypted secrets"""
    dotfiles_dir = Path(dotfiles_dir)

    if hostname is None:
        import socket
        hostname = socket.gethostname()

    # Paths
    common_secrets_file = dotfiles_dir / "common" / "secrets" / "common.yaml"
    machine_secrets_file = dotfiles_dir / hostname / "secrets" / f"{hostname}.yaml"
    common_template_file = dotfiles_dir / "common" / ".claude" / "mcp-servers-template.json"
    machine_template_file = dotfiles_dir / hostname / ".claude" / "mcp-servers-template.json"
    claude_json_path = Path.home() / ".claude.json"

    print("\n🔐 Setting up Claude Code configuration...")

    # Try to set up MCP servers (but continue even if it fails)
    mcp_setup_success = False
    try:
        # Set up environment with age key path for faster sops operations
        env = os.environ.copy()
        age_key_file = Path.home() / ".config" / "sops" / "age" / "keys.txt"
        if age_key_file.exists():
            env["SOPS_AGE_KEY_FILE"] = str(age_key_file)

        # Check if sops is installed
        subprocess.run(["sops", "--version"], capture_output=True, check=True, env=env)

        # Check if at least common template exists
        if common_secrets_file.exists() and common_template_file.exists():
            # Decrypt common secrets
            secrets = decrypt_secrets(common_secrets_file)

            # Load and merge machine-specific secrets if they exist
            if machine_secrets_file.exists():
                machine_secrets = decrypt_secrets(machine_secrets_file)
                if machine_secrets:
                    secrets.update(machine_secrets)
                    print(f"  🔑 Merged secrets from {hostname}/secrets/{hostname}.yaml")

            if secrets:
                # Load common template
                with open(common_template_file) as f:
                    common_template_str = f.read()

                # Substitute secrets in common template
                common_mcp_str = substitute_secrets(common_template_str, secrets)
                mcp_servers = json.loads(common_mcp_str)

                # Load and merge machine-specific template if it exists
                if machine_template_file.exists():
                    with open(machine_template_file) as f:
                        machine_template_str = f.read()

                    # Substitute secrets in machine-specific template
                    machine_mcp_str = substitute_secrets(machine_template_str, secrets)
                    machine_mcp_servers = json.loads(machine_mcp_str)

                    # Merge machine-specific servers (they override common ones)
                    mcp_servers.update(machine_mcp_servers)
                    print(f"  📦 Merged {len(machine_mcp_servers)} machine-specific MCP server(s) from {hostname}")

                # Load existing .claude.json or create new one
                if claude_json_path.exists():
                    with open(claude_json_path) as f:
                        claude_config = json.load(f)
                else:
                    claude_config = {}

                # Sync mcpServers section - remove servers not in template, add/update from template
                if "mcpServers" not in claude_config:
                    claude_config["mcpServers"] = {}

                # Remove servers that aren't in the template
                servers_to_remove = [
                    server for server in claude_config["mcpServers"]
                    if server not in mcp_servers
                ]
                for server in servers_to_remove:
                    del claude_config["mcpServers"][server]
                    print(f"  🗑️  Removed obsolete MCP server: {server}")

                # Add/update servers from template
                claude_config["mcpServers"].update(mcp_servers)

                # Write back
                with open(claude_json_path, "w") as f:
                    json.dump(claude_config, f, indent=2)

                print(f"✅ Updated {claude_json_path} with MCP server configurations")
                mcp_setup_success = True
            else:
                print("⚠️  Failed to decrypt secrets. Skipping MCP servers setup.")
        else:
            if not common_secrets_file.exists():
                print(f"⚠️  Secrets file not found: {common_secrets_file}")
            if not common_template_file.exists():
                print(f"⚠️  Common template not found: {common_template_file}")
            print("⚠️  Skipping MCP servers setup.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  sops not found. Skipping MCP servers setup.")
    except Exception as e:
        print(f"⚠️  Error setting up MCP servers: {e}")

    # Symlink CLAUDE.md from common to ~/.claude/
    claude_md_source = dotfiles_dir / "common" / ".claude" / "CLAUDE.md"
    claude_md_target = Path.home() / ".claude" / "CLAUDE.md"

    if claude_md_source.exists():
        # Create ~/.claude directory if it doesn't exist
        claude_md_target.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing symlink or file
        if claude_md_target.exists() or claude_md_target.is_symlink():
            claude_md_target.unlink()

        # Create symlink
        claude_md_target.symlink_to(claude_md_source.resolve())
        print(f"✅ Symlinked {claude_md_target} -> {claude_md_source}")
    else:
        print(f"⚠️  CLAUDE.md not found at {claude_md_source}")

    return True
