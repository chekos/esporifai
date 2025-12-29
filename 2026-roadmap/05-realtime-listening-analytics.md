# Real-Time Listening Analytics

**Category:** New Feature | Architecture
**Quarter:** Q2
**T-shirt Size:** L

## Why This Matters

Spotify's "recently played" endpoint only returns the last 50 tracks, with no historical data beyond that window. For any meaningful listening analytics—understanding listening patterns, tracking discovery, measuring mood over time—users need continuous data collection.

Real-time listening analytics transforms esporifai from a point-in-time data fetcher into a persistent listening companion that builds comprehensive listening history over days, weeks, and months.

This is a unique differentiator: no existing open-source tool provides this capability well. It positions esporifai as essential infrastructure for music data researchers and enthusiasts.

## Current State

- **Data collection:** On-demand only, no persistence
- **Recently played:** Limited to last 50 tracks per API call
- **Historical data:** None—each query is independent
- **Monitoring:** No background processes or scheduling
- **Listening patterns:** Impossible to analyze without external tools

Current limitation example:
```bash
esporifai get-recently-played  # Gets last 50 tracks
# Run again later: overlapping data, no continuity
# No way to build complete listening history
```

## Proposed Future State

A comprehensive real-time listening monitoring system:

**Core Capabilities:**
- Background daemon continuously polling recently-played
- Intelligent deduplication and gap detection
- Persistent storage of complete listening history
- Real-time event streaming (websockets/SSE)
- Configurable polling intervals with rate limit respect

**Analytics Features:**
- Listening session detection (gaps = new session)
- Daily/weekly/monthly listening summaries
- Genre and mood pattern analysis
- Discovery tracking (new artists/tracks)
- Listening time calculations
- Peak listening hour identification

**Integrations:**
- Webhook notifications on song change
- Discord/Slack rich presence integration
- Last.fm scrobble export
- IFTTT/Zapier triggers

**Visualization:**
- Terminal-based live dashboard
- Listening calendar heatmap
- Top artists/tracks over custom periods

## Key Deliverables

- [ ] Create background daemon using `schedule` or `apscheduler`
- [ ] Implement SQLite-based listening history storage
- [ ] Add deduplication logic based on played_at timestamp
- [ ] Create `esporifai listen start` to begin monitoring
- [ ] Create `esporifai listen stop` to halt daemon
- [ ] Create `esporifai listen status` for daemon health
- [ ] Implement gap detection and notification
- [ ] Add listening session segmentation algorithm
- [ ] Create daily/weekly summary generation
- [ ] Implement genre pattern analysis using audio features
- [ ] Add `esporifai stats` command for listening summaries
- [ ] Create webhook notification system
- [ ] Implement Discord Rich Presence integration
- [ ] Add Last.fm scrobble export format
- [ ] Create terminal dashboard using Rich Live Display
- [ ] Implement listening calendar visualization
- [ ] Add custom date range queries (`--from`, `--to`)
- [ ] Create data export for collected history
- [ ] Add systemd/launchd service configuration

## Prerequisites

- Initiative 03 (Async Architecture) for efficient polling
- Initiative 04 (Data Export Hub) for storage and export
- Initiative 02 (Auth Security) for long-running token management

## Risks & Open Questions

- Spotify API rate limits for continuous polling—what's the sustainable interval?
- Background daemon approach: Python process vs. system service vs. container?
- How to handle token refresh for long-running processes?
- Cross-platform daemon management (systemd vs. launchd vs. Windows service)?
- Privacy implications of storing complete listening history?
- Storage growth over time—compression? Archival strategy?
- Should we support multiple Spotify accounts simultaneously?

## Notes

Spotify recently-played constraints:
- Maximum 50 tracks per request
- `before` and `after` cursors for pagination
- No webhook/push notification support (polling required)

Recommended polling strategy:
- Poll every 1-5 minutes
- Use `after` cursor pointing to last known played_at
- Exponential backoff on rate limits
- Consider circadian polling (more frequent during active hours)

Technical components needed:
- `esporifai/daemon.py` - Background service
- `esporifai/storage.py` - SQLite persistence layer
- `esporifai/analytics.py` - Pattern analysis
- `esporifai/notifications.py` - Webhook/integration handlers

Process management options:
- `python-daemon` - Unix daemon support
- `schedule` - Simple scheduling
- `apscheduler` - Advanced scheduling
- `supervisor` - Process management
