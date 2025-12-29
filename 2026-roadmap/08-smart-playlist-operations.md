# Smart Playlist Operations Suite

**Category:** New Feature | DX Improvement
**Quarter:** Q3
**T-shirt Size:** M

## Why This Matters

Playlists are the core unit of music organization, yet esporifai currently has zero playlist functionality. Users can't list their playlists, analyze playlist composition, create new playlists programmatically, or manage existing ones.

For power users—DJs, playlist curators, music bloggers—playlist operations are their primary workflow. Adding intelligent playlist management with features Spotify doesn't offer (duplicate detection, coherence analysis, smart merging) creates compelling value.

## Current State

- **Playlist commands:** None
- **Playlist scopes:** Defined in `constants.py` but unused:
  - `playlist-read-private`
  - `playlist-read-collaborative`
- **Playlist creation:** Not implemented
- **Playlist analysis:** Not implemented

The scopes exist but aren't utilized:
```python
SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    # These are defined but no commands use them
]
```

## Proposed Future State

A comprehensive playlist management system:

**Playlist Operations:**
- List all playlists (owned, followed, collaborative)
- Get playlist details and track listing
- Create new playlists programmatically
- Add/remove tracks from playlists
- Reorder playlist tracks
- Update playlist metadata (name, description, image)
- Duplicate playlists (with modifications)

**Playlist Analysis:**
- Duplicate track detection
- Audio feature distribution analysis
- Playlist coherence scoring
- Genre/mood breakdown
- "Playlist personality" profile
- Tempo/energy flow visualization

**Smart Features:**
- Playlist deduplication (remove duplicates)
- Smart sorting (by tempo, energy, mood flow)
- Playlist merging with conflict resolution
- Auto-playlist from listening history
- "Continue this playlist" recommendations
- Playlist diffing (compare two playlists)

**Batch Operations:**
- Backup all playlists to JSON/CSV
- Restore playlists from backup
- Bulk add tracks from file
- Cross-playlist deduplication

## Key Deliverables

- [ ] Implement `esporifai playlists list` command
- [ ] Implement `esporifai playlists get <id>` command
- [ ] Implement `esporifai playlists create <name>` command
- [ ] Implement `esporifai playlists add <playlist_id> <track_ids>` command
- [ ] Implement `esporifai playlists remove <playlist_id> <track_ids>` command
- [ ] Add playlist modification scopes to auth (`playlist-modify-public`, `playlist-modify-private`)
- [ ] Implement duplicate track detection in playlists
- [ ] Create playlist coherence analyzer using audio features
- [ ] Implement smart sorting by tempo/energy/mood
- [ ] Add `esporifai playlists dedupe <id>` command
- [ ] Add `esporifai playlists analyze <id>` for full analysis
- [ ] Implement playlist backup/restore functionality
- [ ] Create playlist merging with smart conflict handling
- [ ] Add auto-playlist generation from recent listening
- [ ] Implement "continue playlist" recommendations
- [ ] Add `esporifai playlists diff <id1> <id2>` command
- [ ] Create playlist flow visualization (terminal-based)
- [ ] Implement batch track import from file

## Prerequisites

- Initiative 01 (Testing) for confident feature development
- Initiative 07 (AI Engine) for intelligent features (coherence, recommendations)
- Initiative 03 (Async) for efficient batch operations

## Risks & Open Questions

- Playlist modification is destructive—how to prevent accidents?
- Should we require `--force` for modifications?
- Coherence scoring algorithm—what makes a "coherent" playlist?
- Rate limits on playlist modifications—Spotify is stricter here
- How to handle collaborative playlists (different permissions)?
- Image upload for playlist covers—supported by API but complex

## Notes

New Spotify API endpoints to implement:
- `GET /v1/me/playlists` - User's playlists
- `GET /v1/playlists/{id}` - Playlist details
- `GET /v1/playlists/{id}/tracks` - Playlist tracks
- `POST /v1/users/{id}/playlists` - Create playlist
- `POST /v1/playlists/{id}/tracks` - Add tracks
- `DELETE /v1/playlists/{id}/tracks` - Remove tracks
- `PUT /v1/playlists/{id}/tracks` - Reorder tracks
- `PUT /v1/playlists/{id}` - Update details
- `PUT /v1/playlists/{id}/images` - Update cover image

New files:
```
esporifai/
├── api.py           # Add playlist endpoints
├── cli.py           # Add playlists command group
└── playlists/
    ├── operations.py  # CRUD operations
    ├── analysis.py    # Coherence, duplicates
    ├── smart.py       # Sorting, merging
    └── backup.py      # Backup/restore
```

Coherence metrics to consider:
- Tempo variance (lower = more coherent)
- Energy flow (should be smooth, not jarring)
- Genre concentration
- Year range
- Key compatibility (for DJs)
