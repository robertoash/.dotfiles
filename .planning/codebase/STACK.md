# Technology Stack

**Analysis Date:** 2026-02-10

## Languages

**Primary:**
- Python 3.10+ - Core language for all setup scripts, utilities, and automation
- Python 3.12 - Used for MQTT and other system services
- Python 3.14.2 - Runtime environment (current system)
- Bash - Shell scripts for service launching and system commands
- Fish - Shell configuration and scripting language

**Secondary:**
- YAML - Configuration files, secrets management, data formats
- JSON - Application configurations, service files
- TOML - Python project configurations, tool configuration

## Runtime

**Environment:**
- Linux (Arch-based systems for linuxmini, oldmbp)
- macOS (workmbp)
- Python 3.10+ required as primary runtime

**Package Manager:**
- pip/setuptools - Python package distribution
- uv - Fast Python package installer/resolver (mise.toml configured)
- setuptools - Build backend for Python projects
- hatchling - Build backend for some projects

**Lockfile:**
- uv.lock - Present for MQTT and idle-management projects

## Frameworks

**Core:**
- Flask 3.0.0 - Web framework for Xtream API proxy server (`/home/rash/.dotfiles/linuxmini/scripts/iptv/xtream_proxy/`)
- paho-mqtt 2.1.0 - MQTT client library for pub/sub messaging
- pyyaml 6.0+ - YAML parsing for configuration files
- pyrage 1.1.0+ - Cookie management utility

**System Integration:**
- subprocess - Process execution for system commands
- pathlib - Modern file path handling
- os/sys - Standard library system operations

**CLI/Utilities:**
- Rofi - Menu/dmenu for interactive scripts
- yt-dlp - YouTube content downloading and querying
- jellyfin-apiclient-python - Jellyfin media server API client

**Data Processing:**
- numpy - Numerical computing (idle-management, face detection)
- opencv-python (cv2) - Computer vision (face detection for idle management)
- watchdog 6.0.0+ - File system event monitoring

## Key Dependencies

**Critical:**
- paho-mqtt 2.1.0 - MQTT broker communication for Home Assistant integration
- PyYAML 6.0+ - SOPS secrets configuration and YAML parsing
- Flask 3.0.0 - Web proxy for Xtream API filtering
- requests 2.31.0 - HTTP client for external API calls (Jellyfin, Xtream)
- gunicorn 21.2.0 - WSGI HTTP server for production deployment

**Infrastructure:**
- watchdog 6.0.0+ - File system monitoring for service triggers
- numpy 2.3.2+ - Numerical operations for idle detection algorithms
- opencv-python 4.11.0.86+ - Face detection and vision processing

**Environment & Config:**
- pyyaml - Encrypted secrets via SOPS integration
- pyrage - Age encryption support for secrets

## Configuration

**Environment:**
- SOPS + Age encryption for secrets management (`.sops.yaml`)
- Environment variables for service configuration:
  - `MQTT_BROKER` (10.20.10.100:1883)
  - `JELLYFIN_URL`, `JELLYFIN_API_KEY` - Media server access
  - `HASS_SERVER`, `HASS_TOKEN` - Home Assistant integration
  - `UPSTREAM_SERVER`, `UPSTREAM_USERNAME`, `UPSTREAM_PASSWORD` - Xtream upstream
  - `PROXY_USER*_USERNAME/PASSWORD/STREAM_USER/STREAM_PASS` - Multi-user proxy auth
  - `XDG_RUNTIME_DIR` - Runtime directory for service files

**Build:**
- `setup.py` - Main installation orchestrator
- `pyrightconfig.json` - Pyright type checker configuration
- `mise.toml` - Tool version management (Python 3.12.9)
- `pyproject.toml` - Standard project metadata and dependencies
- `uv.lock` - Dependency lockfile for reproducible installs

## Platform Requirements

**Development:**
- Python 3.10+ installed
- SOPS with Age encryption keys configured
- systemd (Linux only)
- Bash/Fish shell
- Git for dotfiles management

**Production:**
- Linux (Arch-based) or macOS
- systemd user services for background tasks
- MQTT broker reachable (Home Assistant typically provides this)
- Home Assistant with hass-cli for device control
- Optional: Jellyfin media server for rofi_jellyfin integration

## Special Configuration

**Multi-Machine Support:**
- Hostname-based detection in `machines.py` (workmbp, linuxmini, oldmbp)
- Machine-specific secrets in `.sops.yaml` with Age key groups
- Separate directories for platform-specific configs (Darwin vs Linux)

**Secrets Management:**
- SOPS with Age encryption
- Keys defined in `.sops.yaml` with per-machine Age public keys
- Encrypted files in `{hostname}/secrets/`, `common/secrets/`, etc.
- Runtime decryption via sops-secrets systemd service

**Development Tools:**
- Pyright for type checking
- Black for code formatting (line-length: 88)
- Linting via various tools configured in projects

---

*Stack analysis: 2026-02-10*
