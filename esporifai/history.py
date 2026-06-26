from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

Json = dict[str, Any]


class HistoryInputKind(str, Enum):
    recently_played = "recently-played"
    export = "export"

    def __str__(self):
        return self.value


@dataclass
class NormalizedHistory:
    events: dict[tuple[str, str], Json] = field(default_factory=dict)
    tracks: dict[str, Json] = field(default_factory=dict)
    albums: dict[str, Json] = field(default_factory=dict)
    artists: dict[str, Json] = field(default_factory=dict)
    skipped_rows: int = 0

    def add_event(self, played_at: str, track_id: str, source: str) -> None:
        event = self.events.setdefault(
            (played_at, track_id),
            {
                "played_at": played_at,
                "track_id": track_id,
                "sources": [],
            },
        )
        event["sources"] = sorted(set(event["sources"]) | {source})

    def event_records(self) -> list[Json]:
        return [self.events[key] for key in sorted(self.events)]

    def track_records(self) -> list[Json]:
        return [self.tracks[key] for key in sorted(self.tracks)]

    def album_records(self) -> list[Json]:
        return [self.albums[key] for key in sorted(self.albums)]

    def artist_records(self) -> list[Json]:
        return [self.artists[key] for key in sorted(self.artists)]

    def as_summary(self) -> Json:
        event_records = self.event_records()
        return {
            "events": len(event_records),
            "tracks": len(self.tracks),
            "albums": len(self.albums),
            "artists": len(self.artists),
            "skipped_rows": self.skipped_rows,
            "earliest": event_records[0]["played_at"] if event_records else None,
            "latest": event_records[-1]["played_at"] if event_records else None,
        }


def load_json(path: Path) -> Any:
    with open(path) as handle:
        return json.load(handle)


def first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def spotify_items(payload: Any) -> list[Json]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("items") or []
        return [item for item in items if isinstance(item, dict)]
    return []


def artist_id_list(raw_artists: Any) -> list[str]:
    if not isinstance(raw_artists, list):
        return []

    ids = []
    for artist in raw_artists:
        if isinstance(artist, dict) and artist.get("id"):
            ids.append(artist["id"])
        elif isinstance(artist, str):
            ids.append(artist)
    return ids


def normalize_artist(artist: Json, source: str) -> Json | None:
    artist_id = artist.get("id")
    if not artist_id:
        return None
    return {
        "id": artist_id,
        "name": artist.get("name"),
        "uri": artist.get("uri"),
        "href": artist.get("href"),
        "external_urls": artist.get("external_urls"),
        "type": artist.get("type"),
        "sources": [source],
    }


def normalize_album(album: Json, source: str) -> Json | None:
    album_id = album.get("id")
    if not album_id:
        return None
    return {
        "id": album_id,
        "name": album.get("name"),
        "album_type": album.get("album_type"),
        "artist_ids": artist_id_list(album.get("artists")),
        "release_date": album.get("release_date"),
        "release_date_precision": album.get("release_date_precision"),
        "total_tracks": album.get("total_tracks"),
        "uri": album.get("uri"),
        "href": album.get("href"),
        "external_urls": album.get("external_urls"),
        "images": album.get("images"),
        "type": album.get("type"),
        "sources": [source],
    }


def normalize_track(track: Json, source: str) -> Json | None:
    track_id = track.get("id")
    if not track_id:
        return None

    album = track.get("album") if isinstance(track.get("album"), dict) else {}
    artist_ids = artist_id_list(track.get("artists"))
    album_id = first_present(track.get("album_id"), album.get("id"))

    return {
        "id": track_id,
        "name": track.get("name"),
        "artist_ids": first_present(track.get("artist_ids"), artist_ids, []),
        "album_id": album_id,
        "duration_ms": track.get("duration_ms"),
        "explicit": track.get("explicit"),
        "popularity": track.get("popularity"),
        "preview_url": track.get("preview_url"),
        "track_number": track.get("track_number"),
        "disc_number": track.get("disc_number"),
        "is_local": track.get("is_local"),
        "uri": track.get("uri"),
        "href": track.get("href"),
        "external_ids": track.get("external_ids"),
        "external_urls": track.get("external_urls"),
        "type": track.get("type"),
        "metadata_status": "complete",
        "sources": [source],
    }


def normalize_export_track(row: Json, source: str, track_id: str) -> Json:
    name = first_present(
        row.get("name"),
        row.get("track_name"),
        row.get("master_metadata_track_name"),
    )
    artist_name = first_present(
        row.get("artist_name"),
        row.get("master_metadata_album_artist_name"),
    )
    album_name = first_present(
        row.get("album_name"),
        row.get("master_metadata_album_album_name"),
    )
    status = "partial" if first_present(name, artist_name, album_name) else "missing"
    record = {
        "id": track_id,
        "name": name,
        "artist_names": [artist_name] if artist_name else [],
        "album_name": album_name,
        "uri": row.get("spotify_track_uri"),
        "metadata_status": status,
        "sources": [source],
    }
    return {key: value for key, value in record.items() if value not in (None, [], {})}


def merge_record(records: dict[str, Json], record: Json | None) -> None:
    if not record:
        return

    existing = records.get(record["id"])
    if existing is None:
        clean = {
            key: value
            for key, value in record.items()
            if value not in (None, [], {})
        }
        clean["sources"] = sorted(set(record.get("sources", [])))
        records[record["id"]] = clean
        return

    status_rank = {"missing": 0, "partial": 1, "complete": 2}
    for key, value in record.items():
        if key == "sources":
            existing["sources"] = sorted(set(existing.get("sources", [])) | set(value))
        elif key == "metadata_status":
            current = status_rank.get(existing.get("metadata_status"), -1)
            incoming = status_rank.get(value, -1)
            if incoming > current:
                existing[key] = value
        elif value not in (None, [], {}) and existing.get(key) in (None, [], {}, ""):
            existing[key] = value


def normalize_recently_played_item(
    item: Json, source: str, history: NormalizedHistory
) -> None:
    played_at = item.get("played_at")
    track = item.get("track") if isinstance(item.get("track"), dict) else {}
    track_id = track.get("id")
    if not played_at or not track_id:
        history.skipped_rows += 1
        return

    history.add_event(played_at, track_id, source)
    merge_record(history.tracks, normalize_track(track, source))

    album = track.get("album") if isinstance(track.get("album"), dict) else None
    merge_record(history.albums, normalize_album(album, source) if album else None)
    if album:
        for artist in album.get("artists", []):
            if isinstance(artist, dict):
                merge_record(history.artists, normalize_artist(artist, source))
    for artist in track.get("artists", []):
        if isinstance(artist, dict):
            merge_record(history.artists, normalize_artist(artist, source))


def track_id_from_export_row(row: Json) -> str | None:
    uri = row.get("spotify_track_uri") or ""
    return first_present(
        row.get("id"),
        row.get("track_id"),
        (
            uri.removeprefix("spotify:track:")
            if uri.startswith("spotify:track:")
            else None
        ),
    )


def normalize_export_row(row: Json, source: str, history: NormalizedHistory) -> None:
    played_at = first_present(row.get("played_at"), row.get("ts"))
    track_id = track_id_from_export_row(row)
    if not played_at or not track_id:
        history.skipped_rows += 1
        return

    history.add_event(played_at, track_id, source)
    merge_record(history.tracks, normalize_export_track(row, source, track_id))


def normalize_history_payload(
    payload: Any,
    kind: HistoryInputKind,
    source: str,
) -> NormalizedHistory:
    history = NormalizedHistory()
    if kind == HistoryInputKind.recently_played:
        for item in spotify_items(payload):
            normalize_recently_played_item(item, source, history)
        return history

    if kind == HistoryInputKind.export:
        rows = payload if isinstance(payload, list) else []
        for row in rows:
            if isinstance(row, dict):
                normalize_export_row(row, source, history)
            else:
                history.skipped_rows += 1
        return history

    raise ValueError(f"Unsupported history kind: {kind}")


def sorted_jsonl(records: list[Json]) -> str:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def write_jsonl(path: Path, records: list[Json]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sorted_jsonl(records))
