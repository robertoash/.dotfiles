# Xtream Proxy Server

A filtering proxy for Xtream API that applies your channel filters and serves clean M3U playlists to Apple TV.

## How it works

1. **Apple TV** requests M3U from proxy server
2. **Proxy** fetches channels from real Xtream server via API
3. **Proxy** applies your filter rules (same as iptv_m3u_gen.py)
4. **Proxy** generates filtered M3U and serves to Apple TV
5. **Apple TV** plays streams → **Proxy** redirects to real server

## Setup

### 1. Configure Environment Variables

Edit `docker-compose.yml`:

```yaml
environment:
  # Your real Xtream server
  UPSTREAM_SERVER: "http://cf.hi-max.me"
  UPSTREAM_USERNAME: "48f07785de"
  UPSTREAM_PASSWORD: "f165bbc27a"

  # Optional: Different credentials for streaming (if you have EXTRA_ creds)
  STREAM_USERNAME: "your_extra_username"  # Leave blank to use UPSTREAM_USERNAME
  STREAM_PASSWORD: "your_extra_password"  # Leave blank to use UPSTREAM_PASSWORD

  # Credentials that Apple TV will use to connect to this proxy
  PROXY_USERNAME: "apple_tv_user"
  PROXY_PASSWORD: "apple_tv_pass"
```

### 2. Deploy to dockerlab

```bash
# Copy files to dockerlab
scp -r xtream_proxy/ dockerlab:~/

# SSH to dockerlab and deploy
ssh dockerlab
cd xtream_proxy/
docker-compose up -d
```

### 3. Configure Apple TV

Point your Apple TV IPTV app to:
- **Server**: `http://dockerlab_ip:8080`
- **Username**: `apple_tv_user` (or whatever you set as PROXY_USERNAME)
- **Password**: `apple_tv_pass` (or whatever you set as PROXY_PASSWORD)

## Endpoints

- `GET /get.php?username=user&password=pass&type=m3u_plus` - Filtered M3U playlist
- `GET /player_api.php?action=get_live_streams` - Filtered live streams API
- `GET /live/{user}/{pass}/{stream_id}.ts` - Live stream proxy
- `GET /xmltv.php?username=user&password=pass` - EPG proxy
- `GET /health` - Health check

## Filter Rules

Uses the same filter rules from your `iptv_m3u_gen.py`:
- Excludes religious/biblical content
- Includes: Swedish, US, UK, EU, Spanish, Italian, Australian channels
- Applies name tweaks (SWE|, USA|, etc.)
- Categorizes content (TV, Movies, Series, Spicy)

## Logs

```bash
# View logs
docker-compose logs -f xtream-proxy

# Check health
curl http://dockerlab_ip:8080/health
```