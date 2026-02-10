# Coding Conventions

**Analysis Date:** 2026-02-10

## Naming Patterns

**Files:**
- Python: `snake_case.py` (e.g., `symlink_setup.py`, `env_distribution.py`, `merge_setup.py`)
- Bash: `kebab-case.sh` (e.g., `decrypt-secrets.sh`)
- Setup modules use descriptive suffixes: `*_setup.py` for setup-related modules, `*_utils.py` for utility modules

**Functions:**
- Python functions use `snake_case` (e.g., `get_machine_config()`, `setup_ssh()`, `create_symlink()`)
- Private functions prefixed with underscore: `_create_or_replace_symlink()`, `_handle_special_cases()`
- Functions named descriptively with action verb first: `setup_*`, `merge_*`, `distribute_*`, `backup_*`, `create_*`, `generate_*`

**Variables:**
- Snake_case for all variables: `dotfiles_dir`, `hostname`, `machine_config`, `symlink_warnings`
- Boolean flags prefixed or suffixed descriptively: `is_linux`, `is_macos`, `needs_update`, `found_files`
- Collections use plural names: `symlink_paths`, `gitignore_entries`, `plist_files`, `hosts_entries`
- Type hints included in function signatures where clarity is needed

**Types/Classes:**
- Dictionary-based configuration objects: `MACHINES` (constants), `MERGE_DIRS` (config), `machine_config` (instances)
- No class definitions; project uses functional design with dictionaries for configuration

## Code Style

**Formatting:**
- Standard PEP 8: 4-space indentation, line length ~120 characters
- No explicit formatter (no black/autopep8 config found)
- Consistent spacing around operators and parameters

**Linting:**
- Pyright type checker configured in `pyrightconfig.json`
- Config includes `setup` directory in extra paths for import resolution
- No ESLint, flake8, or mypy config found

**Docstrings:**
- Module-level docstrings present in all `.py` files: Triple-quoted summary at top
- Module docstrings explain the module's purpose and any key context
- Function docstrings use triple quotes with description, Args, Returns (when needed)
- Example from `symlink_setup.py`:
  ```python
  """Symlink configuration files to ~/.config and handle special cases."""

  def symlink_configs(dotfiles_dir, hostname, home, machine_config):
      """Symlink all configs based on MERGE_DIRS configuration"""
  ```

## Import Organization

**Order:**
1. Standard library imports (`subprocess`, `json`, `shutil`, `pathlib`, `socket`, `platform`)
2. Third-party imports (`yaml`)
3. Local imports (relative imports from setup modules)

**Path Aliases:**
- Local module imports use relative names: `from config import MERGE_DIRS`, `from symlink_utils import create_symlink`
- No path aliases or complex import schemes used

**Example structure** (`setup/env_distribution.py`):
```python
#!/usr/bin/env python3
"""Module docstring."""

import socket
import subprocess
from pathlib import Path
from typing import Dict, Any
import yaml
```

## Error Handling

**Patterns:**
- Try/except blocks catch specific exceptions: `PermissionError`, `FileNotFoundError`, `subprocess.CalledProcessError`
- Non-critical failures return gracefully with warnings (print to stdout with emoji prefix)
- Critical failures exit with messages:
  ```python
  if not config_file.exists():
      raise FileNotFoundError(f"Environment config not found: {config_file}")
  ```

**Subprocess handling:**
- Common pattern with error checking:
  ```python
  result = subprocess.run(["chmod", "600", str(source)], check=True)
  # or
  result = subprocess.run(["cmd"], capture_output=True, text=True)
  if result.returncode != 0:
      print(f"⚠️  Failed: {result.stderr}")
  ```

**Graceful degradation:**
- Non-essential operations wrapped in try/except, errors logged but don't stop setup
- Example (`env_distribution.py`):
  ```python
  except (subprocess.CalledProcessError, FileNotFoundError) as e:
      if verbose:
          print(f"  ⚠️  Could not import into systemd: {e}")
      return False
  ```

## Logging

**Framework:** No dedicated logging library; uses `print()` with emoji prefixes and status indicators

**Patterns:**
- Informational: `print(f"ℹ️  Message")`
- Success: `print(f"✅ Success message")`
- Warning: `print(f"⚠️  Warning message")`
- Error: `print(f"❌ Error message")` (rarely used, exceptions preferred)
- Section headers: `print(f"\n🔗 Step 2: Symlinking configs...")`
- Progress updates: `print(f"\r🔀 Merging... ({current}/{total})", end='', flush=True)`

**When to log:**
- Print status at the start of each major step/function
- Print results/counts of operations performed
- Print warnings for non-critical issues
- Print success confirmations when setup completes

## Comments

**When to Comment:**
- Avoid comments explaining obvious code; code should be self-documenting
- Comments clarify WHY, not WHAT:
  ```python
  # Comments on context:
  """Skip hidden files and directories"""

  # Explain purpose in complex logic:
  """
  Merge existing auto-generated entries with new ones
  (preserves old entries while adding new ones)
  """

  # NOT for simple operations:
  # ❌ Don't do: "Loop through items" above a for loop
  ```

**Docstring/TSDoc:**
- Module docstrings (required): One-line summary + optional detail
- Function docstrings: Present for public functions; describe purpose, args if complex, return type
- Example (`merge_common_into_machine`):
  ```python
  def merge_common_into_machine(common_dir, machine_dir, config_root, dotfiles_dir, level=0, symlink_paths=None, progress_info=None):
      """
      Populate machine_dir with symlinks to files from common_dir.
      Only creates symlinks for items that don't already exist in machine_dir.
      Recursively merges subdirectories.
      Collects all symlink paths relative to config_root for .gitignore.
      """
  ```

## Function Design

**Size:**
- Functions typically 20-50 lines; longer functions break into private helpers with `_` prefix
- Example: `symlink_setup.py` has `symlink_configs()` as public interface, `_create_or_replace_symlink()` and `_handle_special_cases()` as private helpers

**Parameters:**
- Prefer explicit parameters over global state
- Common pattern: `(dotfiles_dir, hostname, home, machine_config)` passed through call chain
- Optional parameters with `None` defaults: `symlink_paths=None`, `progress_info=None`, `verbose=True`
- Type hints for function signatures where useful (seen in `env_distribution.py`)

**Return Values:**
- Functions return relevant data: counts (`int`), content (`str`), success flags (`bool`), or collected data (`list`, `dict`)
- Many setup functions return `None` and print status directly
- Helper functions return data needed by callers: `merge_common_into_machine()` returns `symlink_paths`

## Module Design

**Exports:**
- Setup modules export single main function: `setup_ssh()`, `setup_crontab()`, `setup_hosts()`, etc.
- Utility modules export helper functions: `create_symlink()`, `merge_common_into_machine()` from `symlink_utils.py`
- Configuration module (`config.py`) exports constants: `MERGE_DIRS`, `BACKUP_CONFIGS`
- Orchestrator (`setup.py`) imports and calls all setup functions in sequence

**Barrel Files:**
- Not used; imports are explicit and specific
- Each setup module self-contained with clear dependencies

## Type Hints

**Usage:**
- Type hints present in function signatures for clarity (not enforced everywhere)
- Common types: `Path`, `str`, `int`, `Dict[str, Any]`, `List[str]`, `bool`
- Example from `env_distribution.py`:
  ```python
  def load_env_config(dotfiles_dir: Path) -> Dict[str, Any]:
  def expand_home(val: str, home_dir: str) -> str:
  def generate_systemd_env_file(config: Dict[str, Any], machine: str) -> str:
  ```

## Conditionals and Checks

**Pattern:**
- Early returns to reduce nesting
- Guard clauses check prerequisites:
  ```python
  if not source_dir.exists():
      continue  # Skip if not present
  if hostname is None:
      hostname = socket.gethostname()  # Default value
  ```

- Config-driven conditionals: `if machine_config["is_linux"]:`, `if machine_config["is_macos"]:`

## File Operations

**Pathlib preference:**
- All file operations use `Path` from `pathlib`, never `os.path`
- Path methods: `.exists()`, `.is_symlink()`, `.is_dir()`, `.read_text()`, `.write_text()`, `.glob()`, `.iterdir()`
- Permissions set via `subprocess.run(["chmod", ...])` for sensitive files

**Special considerations:**
- SSH config files get `chmod 600`: `subprocess.run(["chmod", "600", str(ssh_config_source)], check=True)`
- Directories created with `mkdir(parents=True, exist_ok=True)`
- Symlinks always use `.resolve()` to get absolute paths

---

*Convention analysis: 2026-02-10*
