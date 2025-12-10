"""
Claude Code configuration setup with sops-encrypted secrets.
"""

import json
import subprocess
import sys
from pathlib import Path


def decrypt_secrets(secrets_file):
    """Decrypt sops secrets file and return as dict"""
    try:
        result = subprocess.run(
            ["sops", "-d", str(secrets_file)],
            capture_output=True,
            text=True,
            check=True
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
        "{{CLAUDE_GITHUB_TOKEN}}": secrets.get("claude-github-token", ""),
        "{{CLAUDE_HA_TOKEN_CONFIG}}": secrets.get("claude-ha-token-config", ""),
        "{{CLAUDE_HA_TOKEN_GLOBAL}}": secrets.get("claude-ha-token-global", ""),
        "{{OBSIDIAN_API_KEY}}": secrets.get("obsidian-api-key", ""),
    }
    
    for placeholder, value in replacements.items():
        template_str = template_str.replace(placeholder, value)
    
    return template_str


def setup_claude_config(dotfiles_dir):
    """Setup Claude Code MCP servers with encrypted secrets"""
    dotfiles_dir = Path(dotfiles_dir)
    
    # Paths
    secrets_file = dotfiles_dir / "common" / "secrets" / "claude.yaml"
    template_file = dotfiles_dir / "common" / ".claude" / "mcp-servers-template.json"
    claude_json_path = Path.home() / ".claude.json"
    
    print("\n🔐 Setting up Claude Code configuration...")
    
    # Check if sops is installed
    try:
        subprocess.run(["sops", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  sops not found. Skipping Claude config setup.")
        return False
    
    # Check if secrets file exists
    if not secrets_file.exists():
        print(f"⚠️  Secrets file not found: {secrets_file}")
        return False
    
    # Check if template exists
    if not template_file.exists():
        print(f"⚠️  Template not found: {template_file}")
        return False
    
    # Decrypt secrets
    secrets = decrypt_secrets(secrets_file)
    if not secrets:
        print("⚠️  Failed to decrypt secrets.")
        return False
    
    # Load template
    with open(template_file) as f:
        template_str = f.read()
    
    # Substitute secrets
    mcp_servers_str = substitute_secrets(template_str, secrets)
    mcp_servers = json.loads(mcp_servers_str)
    
    # Load existing .claude.json or create new one
    if claude_json_path.exists():
        with open(claude_json_path) as f:
            claude_config = json.load(f)
    else:
        claude_config = {}
    
    # Update mcpServers section
    if "mcpServers" not in claude_config:
        claude_config["mcpServers"] = {}
    
    claude_config["mcpServers"].update(mcp_servers)
    
    # Write back
    with open(claude_json_path, "w") as f:
        json.dump(claude_config, f, indent=2)
    
    print(f"✅ Updated {claude_json_path} with MCP server configurations")
    return True
