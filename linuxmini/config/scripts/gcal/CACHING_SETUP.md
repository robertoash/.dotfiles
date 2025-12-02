# Google Calendar Notifications - Caching Setup

This system now uses caching to reduce API calls and improve efficiency.

## How It Works

- **Cache Refresh**: Fetches events from Google Calendar API and stores them locally
- **Cache Query**: Checks cached events for notifications (no API calls)
- **Smart Fallback**: The `--cron` mode automatically refreshes cache if stale

## Cron Job Setup

### Recommended Efficient Setup

Add these two lines to your crontab (`crontab -e`):

```bash
# Refresh cache every 30 minutes (API call)
*/30 * * * * /home/rash/.config/scripts/gcal/gcal_refresh_wrapper.sh

# Check cache every minute for notifications (no API call)
*/1 * * * * /home/rash/.config/scripts/gcal/gcal_cron_wrapper.sh
```

### Alternative Single Cron Job (Backward Compatible)

If you prefer a single cron job with smart caching:

```bash
# Smart caching - refreshes only when needed
*/1 * * * * /home/rash/.config/scripts/gcal/gcal_cron_wrapper.sh
```

Change the wrapper to use `--cron` instead of `--query` for this approach.

## Benefits

- **Reduced API Calls**: From 1440 calls/day to 48 calls/day (97% reduction)
- **Lower Costs**: Significant reduction in Google Calendar API usage
- **Better Performance**: Cache queries are nearly instantaneous
- **Reliability**: Notifications still arrive on time

## Cache Configuration

- **Cache Duration**: 1 hour (configurable in `CACHE_DURATION_HOURS`)
- **Cache Location**: `~/.config/gcal-notifications/events_cache.json`
- **Cache Scope**: 24 hours of upcoming events

## Manual Commands

```bash
# Refresh cache manually
python3 gcal_notify.py --refresh --verbose

# Query cache manually
python3 gcal_notify.py --query --verbose

# Check cache status
ls -la ~/.config/gcal-notifications/events_cache.json
```

## Logs

- Query operations: `~/.config/gcal-notifications/cron.log`
- Refresh operations: `~/.config/gcal-notifications/refresh.log`