# Multi-Platform Music Service SDK

**Category:** New Feature | Integration
**Quarter:** Q2-Q3
**T-shirt Size:** XL

## Why This Matters

Spotify isn't the only music streaming service. Apple Music has 88+ million subscribers. YouTube Music is the default on Android. Amazon Music, Deezer, Tidal—the market is fragmented. Users often have libraries across multiple services, or switch services over time.

By abstracting music data access across platforms, esporifai becomes the universal music data tool—not just a Spotify CLI. This is a massive expansion of the addressable user base and creates unique value: cross-platform listening analytics that no single service provides.

Think: "How does my Apple Music discovery compare to my Spotify recommendations?" or "Transfer my complete listening history from Spotify to Apple Music."

## Current State

- **Platforms supported:** Spotify only
- **Architecture:** Spotify-specific (`api.py` directly calls Spotify endpoints)
- **Data model:** Spotify JSON schemas hardcoded
- **Authentication:** Spotify OAuth only
- **CLI commands:** Spotify-specific terminology

Current architecture is tightly coupled:
```python
def get_track(access_token: str, track_id: str):
    # Hardcoded Spotify endpoint
    response = httpx.get(
        f"https://api.spotify.com/v1/tracks/{track_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
```

## Proposed Future State

A unified music data SDK supporting multiple platforms:

**Supported Platforms:**
- Spotify (current, enhanced)
- Apple Music
- YouTube Music
- Last.fm
- Deezer
- Tidal
- Amazon Music (where API available)

**Unified Data Model:**
- Common `Track`, `Artist`, `Album`, `Playlist` objects
- Platform-specific fields preserved as metadata
- Bidirectional ID mapping between services
- Normalized audio features where available

**Cross-Platform Features:**
- Universal search across all connected services
- Playlist sync/transfer between platforms
- Combined listening history from all sources
- Cross-platform artist/track matching
- Unified recommendations aggregation

**Architecture:**
- Provider abstraction layer
- Plugin system for new platforms
- Credential manager for multiple accounts
- Rate limit coordination across services

## Key Deliverables

- [ ] Design unified music data model (Track, Artist, Album, Playlist, ListeningEvent)
- [ ] Create provider abstraction interface (`BaseProvider` class)
- [ ] Refactor Spotify as first provider implementation
- [ ] Implement Apple Music provider using MusicKit
- [ ] Implement YouTube Music provider using `ytmusicapi`
- [ ] Implement Last.fm provider for scrobble data
- [ ] Implement Deezer provider using their API
- [ ] Create cross-platform ID matching using ISRC/UPC
- [ ] Add MusicBrainz integration for canonical IDs
- [ ] Implement credential manager for multiple services
- [ ] Create `esporifai providers list` command
- [ ] Create `esporifai providers auth <provider>` command
- [ ] Add `--provider` flag to all data commands
- [ ] Implement playlist transfer between services
- [ ] Create unified search across all providers
- [ ] Add cross-platform listening merge
- [ ] Implement provider plugin system for community extensions
- [ ] Document provider development guide

## Prerequisites

- Initiative 03 (Async Architecture) for efficient multi-provider calls
- Initiative 04 (Data Export Hub) for unified data handling
- Initiative 02 (Auth Security) for multi-account credential management

## Risks & Open Questions

- Apple Music's API has significant limitations—what's actually feasible?
- YouTube Music has no official API—is `ytmusicapi` stable enough?
- Cross-platform track matching accuracy—how to handle mismatches?
- Should this be a breaking change (esporifai 1.0) or additive?
- How to handle rate limits across multiple providers simultaneously?
- Privacy: aggregating data across services creates richer user profile
- Licensing implications of moving playlists between services?

## Notes

Platform API availability:
- **Spotify:** Excellent API, full access
- **Apple Music:** MusicKit API, requires developer account, limited personal data
- **YouTube Music:** No official API, `ytmusicapi` is reverse-engineered
- **Last.fm:** Good API, excellent for scrobble history
- **Deezer:** Decent API with OAuth
- **Tidal:** Limited API access
- **Amazon Music:** No public API

ID matching strategies:
- ISRC codes (International Standard Recording Code) for tracks
- UPC/EAN for albums
- MusicBrainz IDs as canonical reference
- Fuzzy matching on artist name + track title as fallback

New project structure:
```
esporifai/
├── providers/
│   ├── base.py          # Abstract provider
│   ├── spotify.py       # Current api.py refactored
│   ├── apple_music.py
│   ├── youtube_music.py
│   ├── lastfm.py
│   └── deezer.py
├── models/
│   ├── track.py
│   ├── artist.py
│   ├── album.py
│   └── playlist.py
└── matching/
    ├── isrc.py
    └── fuzzy.py
```
