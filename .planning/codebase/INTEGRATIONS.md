# External Integrations

**Analysis Date:** 2026-02-10

## APIs & External Services

**Home Assistant:**
- Home Assistant MQTT Broker - Central hub for device automation
  - SDK/Client: paho-mqtt 2.1.0
  - Connection: MQTT broker at `10.20.10.100:1883`
  - Auth: Username/password via environment
  - Usage: Idle management, office detection, device control (lights, switches)

**Media Services:**
- Jellyfin - Self-hosted media server
  - SDK/Client: jellyfin-apiclient-python
  - Auth: API key (`JELLYFIN_API_KEY` env var)
  - Endpoint: `JELLYFIN_URL` env var
  - Usage: Media browsing, playback control via rofi menu
  - Cache: Disk-based pickle cache at `~/.config/scripts/_cache/rofi_jellyfin/`

**Streaming/IPTV:**
- Xtream Codes API - IPTV/streaming service proxy
  - SDK/Client: Custom Flask-based proxy implementation
  - Auth: Multi-user proxy with upstream credentials
  - Endpoint: Xtream upstream server (configurable via `UPSTREAM_SERVER` env var)
  - Usage: Stream filtering, multi-user authentication, port 8080 (full) & 7070 (mini)
  - Implementation: `linuxmini/scripts/iptv/xtream_proxy/`

**YouTube:**
- YouTube (via yt-dlp)
  - SDK/Client: yt-dlp CLI tool
  - Auth: Cookie extraction from Brave browser
  - Usage: Search, watch-later playlist access, video playback via mpv
  - Implementation: `linuxmini/scripts/rofi/rofi_yt_search.py`, `rofi_yt_watchlater.py`

**Calendar:**
- Google Calendar integration
  - Usage: Knivsta/Uppsala school calendar generation and notifications
  - Implementation: `linuxmini/scripts/gcal/`
  - Auth: Environment-based (calendar URLs or API keys)

## Data Storage

**Local Filesystems:**
- Primary: Local filesystem only (no centralized database)
- Cache: Disk-based caches at `~/.config/scripts/_cache/`
  - Jellyfin media cache (pickle format)
  - Rofi script caches
- Temporary Storage: `/tmp/mqtt/` for MQTT status files
  - `in_office_status` - Office presence state
  - `linux_mini_status` - System status
  - `linux_webcam_status` - Webcam state
  - `idle_detection_status` - Idle state
  - `manual_override_status` - Manual override flags

**Secrets Storage:**
- SOPS encrypted YAML files at:
  - `common/secrets/claude.yaml`
  - `{hostname}/secrets/*.yaml`
  - Files encrypted with Age per machine
  - Runtime secrets available via `XDG_RUNTIME_DIR/secrets/` (sops-secrets service)

**Bookmark/URL Storage:**
- Buku (bookmark manager)
  - Encrypted database support (`~/.config/buku/` or swappable DBs)
  - Scripts for database switching with encryption

**File Management:**
- Fre - Frecent file access tracker
  - Database at ~/.local/share/frecent/
  - Cleanup via `linuxmini/scripts/shell/frecent_cleanup.py`

## Authentication & Identity

**Auth Providers:**
- Custom/Multi-service approach
- Home Assistant token-based (`HASS_TOKEN` env var)
- Jellyfin API key authentication
- Xtream Codes multi-user proxy credentials
- Age encryption keys for SOPS secrets (per-machine)

**Implementation:**
- Environment variables for service credentials
- SOPS-managed encrypted secrets with Age encryption
- Machine-specific secrets in `.sops.yaml` with key groups
- Runtime secret injection via sops-secrets systemd service

## Monitoring & Observability

**Error Tracking:**
- None detected - error handling via subprocess exit codes and exception logging

**Logs:**
- File-based logging to `~/.local/share/logs/` or `~/.config/logs/`
- Log structure: `LOGGING_CONFIG` from `config.py` modules
- Systemd journal integration via systemd services
- Service status checks via `systemctl --user status [service]`

**System Monitoring:**
- MQTT status reporting for system metrics
- File-based status tracking in `/tmp/mqtt/`
- systemd service status monitoring

## CI/CD & Deployment

**Hosting:**
- Local machines only (linuxmini, workmbp, oldmbp)
- systemd user services for background tasks
- systemd timers for scheduled operations (cron-like)

**Package Distribution:**
- Python packages installed via pip/uv to machine-specific locations
- Git-based dotfiles synchronization across machines
- No external CI/CD pipeline detected

## Environment Configuration

**Required env vars:**
- `MQTT_BROKER` - MQTT broker host (default: 10.20.10.100)
- `JELLYFIN_URL` - Jellyfin server URL
- `JELLYFIN_API_KEY` - Jellyfin API authentication
- `HASS_SERVER` - Home Assistant server URL
- `HASS_TOKEN` - Home Assistant authentication token
- `UPSTREAM_SERVER` - Xtream upstream server address
- `UPSTREAM_USERNAME`, `UPSTREAM_PASSWORD` - Xtream upstream credentials
- `PROXY_USER{N}_USERNAME/PASSWORD/STREAM_USER/STREAM_PASS` - Multi-user proxy auth (1-N)
- `XDG_RUNTIME_DIR` - Runtime directory for secrets (systemd)
- `XDG_CONFIG_HOME` - Config directory (defaults to ~/.config)
- `XDG_CACHE_HOME` - Cache directory

**Secrets location:**
- SOPS encrypted YAML files: `.sops.yaml` configuration with Age keys
- Runtime decryption: sops-secrets.service provides decrypted files in `$XDG_RUNTIME_DIR/secrets/`
- Per-machine encrypted files in `{hostname}/secrets/`

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- MQTT publish: System status updates to Home Assistant topics
- Xtream API calls: Stream filtering and media queries
- Jellyfin API calls: Media server queries and playback control
- Home Assistant service calls: Device control (switch.turn_off, etc.)

## System Integration

**IPC & Process Communication:**
- systemd services for background task management
- MQTT pub/sub for Home Assistant communication
- File-based status communication in `/tmp/mqtt/`
- subprocess-based CLI tool invocation (hass-cli, yt-dlp, mpv, rofi)

**Voice & Input:**
- hyprwhspr - Wayland speech-to-text integration
- Espanso - Text expansion and abbreviation engine
- Kanata - Keyboard remapping daemon
- Ydotool - Keyboard/mouse automation

**Desktop Environment Integration:**
- Hyprland - Tiling window manager
- Waybar - Status bar
- Dunst - Notification daemon
- Rofi - Application launcher and menu system

## Third-Party Tools (Non-SDK)

**Media:**
- mpv - Video player
- yt-dlp - YouTube/video downloader and tools
- Jellyfin client via apiclient-python

**System:**
- hyprctl - Hyprland control
- systemctl - systemd service management
- hass-cli - Home Assistant CLI for service calls

**Utilities:**
- Rofi - Interactive menu system
- SOPS - Secrets encryption management
- Age - Modern encryption tool

---

*Integration audit: 2026-02-10*
