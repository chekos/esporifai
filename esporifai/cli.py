from __future__ import annotations

from pathlib import Path
from datetime import datetime as dt
import json
from typing import List, Optional
from zoneinfo import ZoneInfo

import typer
from rich import print

from .config import get_authorize_url_inputs, get_settings
from .api import (
    get_track_audio_analysis,
    get_user_top_items,
    get_user_recently_played,
    get_artist,
    get_several_artists,
    get_track,
    get_several_tracks,
    get_track_audio_features,
    get_several_tracks_audio_features,
)
from .constants import (
    APP_DIR,
    GetTopItems,
    GetTopTimeRanges,
    GetRecentlyPlayedDirections,
    __version__,
    __app_name__,
)
from .utils import (
    auth_check,
    build_auth_code_url,
    build_auth_payload,
    get_auth_status,
    handle_authorization,
    handle_id_file,
    handle_response,
    handle_data,
    request_token,
    write_json,
)
from .constants import AUTH_FILE


token_info = None


def init():
    if not APP_DIR.exists():
        APP_DIR.mkdir(parents=True)


cli = typer.Typer(callback=init, help=f"""{__app_name__} version {__version__}""")


def ensure_token_info(force: bool = False):
    global token_info
    if force or token_info is None:
        token_info = handle_authorization(
            save_files=True,
            force=force,
            settings=get_settings(),
        )
    return token_info


@cli.command()
def auth(
    force: bool = typer.Option(False, "--force", help="Force authorization flow"),
    check: bool = typer.Option(
        False, "--check", help="Check if auth credentials are saved."
    ),
    status: bool = typer.Option(
        False, "--status", help="Show the current auth artifact and token status."
    ),
    url: bool = typer.Option(
        False, "--url", help="Print the Spotify authorization URL for manual login."
    ),
    code: Optional[str] = typer.Option(
        None,
        "--code",
        help="Exchange a Spotify authorization code without browser automation.",
    ),
):
    if check:
        print(auth_check())
        return None

    if status:
        print(json.dumps(get_auth_status(), indent=2, default=str))
        return None

    if url:
        client_id, redirect_uri = get_authorize_url_inputs()
        print(build_auth_code_url(client_id=client_id, redirect_uri=redirect_uri))
        return None

    if code:
        settings = get_settings()
        write_json(AUTH_FILE, build_auth_payload(code, settings=settings))
        token = request_token(code, write=True, settings=settings)
        global token_info
        token_info = token
        print(json.dumps(get_auth_status(settings=settings), indent=2, default=str))
        return None

    ensure_token_info(force=force)


@cli.command()
def get_top(
    item_type: GetTopItems = typer.Argument(
        GetTopItems.artists, case_sensitive=False, help="The type of entity to return."
    ),
    limit: int = typer.Option(
        20, help="The maximum number of items to return.", min=0, max=50
    ),
    offset: int = typer.Option(
        0,
        help="The index of the first item to return. Default: 0 (the first item). Use with limit to get the next set of items.",
    ),
    time_range: GetTopTimeRanges = typer.Option(
        GetTopTimeRanges.medium_term,
        help="""Over what time frame the affinities are computed. Valid values:
        'long' (calculated from several years of data and including all new data as it becomes available),
        'medium' (approximately last 6 months), 'short' (approximately last 4 weeks).""",
    ),
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
    trim: bool = typer.Option(False, "--trim/--full"),
):
    token_info = ensure_token_info()
    response = handle_response(
        get_user_top_items(
            access_token=token_info["access_token"],
            item_type=item_type.value,
            limit=limit,
            offset=offset,
            time_range=f"{time_range.value}_term",
        )
    )

    data = handle_data(response, output, trim)

    if output == Path("-"):
        print(json.dumps(data, default=str))


@cli.command()
def get_recently_played(
    direction: GetRecentlyPlayedDirections = typer.Argument(
        GetRecentlyPlayedDirections.before,
        case_sensitive=False,
        help="Whether to get items 'before' or 'after' `timestamp`.",
    ),
    timestamp: dt = typer.Argument(
        "2022-08-10", help="Time to start getting items from."
    ),
    limit: int = typer.Option(
        20, help="The maximum number of items to return.", min=1, max=50
    ),
    time_zone: str = typer.Option("America/Tijuana", help="Timezone"),
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
    trim: bool = typer.Option(False, "--trim/--full"),
):
    token_info = ensure_token_info()
    # transform date from timestamp to unix timestamp in milliseconds
    timestamp = timestamp.replace(tzinfo=ZoneInfo(time_zone))
    timestamp = int(timestamp.timestamp()) * 1_000

    response = handle_response(
        get_user_recently_played(
            access_token=token_info["access_token"],
            timestamp=timestamp,
            direction=direction,
            limit=limit,
        )
    )

    data = handle_data(response, output, trim)

    if output == Path("-"):
        print(json.dumps(data, default=str))


@cli.command()
def analyze_track(
    track_id: str = typer.Argument(
        ..., help="Spotify track ID. Use '-' if providing a file with IDs."
    ),
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
    file: Path = typer.Option(
        "",
        "--file",
        "-f",
        help="A newline-delimited file with a list of track IDs. One per line.",
    ),
):
    token_info = ensure_token_info()
    if track_id != "-":
        response = handle_response(
            get_track_audio_analysis(
                access_token=token_info["access_token"],
                track_id=track_id,
            )
        )

        data = handle_data(response, output)

        if output == Path("-"):
            typer.echo(
                json.dumps(
                    data,
                    default=str,
                )
            )
    else:
        if (file.suffix == ".txt") | (file.suffix == ".csv"):
            ids = handle_id_file(file)
            for _id in ids:
                response = handle_response(
                    get_track_audio_analysis(
                        access_token=token_info["access_token"],
                        track_id=_id,
                    )
                )
                if output == Path("-"):
                    data = handle_data(response, output)
                    typer.echo(
                        json.dumps(
                            data,
                            default=str,
                        )
                    )
                else:
                    if output.is_dir():
                        data = handle_data(response, output.joinpath(f"{_id}.json"))
                    else:
                        data = handle_data(response, Path(f"{_id}.json"))
        else:
            print("Provide a .txt or .csv file with one ID per line.")


@cli.command()
def get_artists(
    artists_ids: List[str] = typer.Option(
        ...,
        "--id",
    ),
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
):
    token_info = ensure_token_info()
    if len(artists_ids) == 1:
        response = handle_response(
            get_artist(
                access_token=token_info["access_token"],
                artist_id=artists_ids[0],
            )
        )
    else:
        response = handle_response(
            get_several_artists(
                access_token=token_info["access_token"],
                artist_ids=artists_ids,
            )
        )

    data = handle_data(response, output)

    if output == Path("-"):
        typer.echo(
            json.dumps(
                data,
                default=str,
            )
        )


@cli.command()
def get_tracks(
    track_ids: List[str] = typer.Option(
        ...,
        "--id",
    ),
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
):
    token_info = ensure_token_info()
    if len(track_ids) == 1:
        response = handle_response(
            get_track(
                access_token=token_info["access_token"],
                track_id=track_ids[0],
            )
        )
    else:
        response = handle_response(
            get_several_tracks(
                access_token=token_info["access_token"],
                track_ids=track_ids,
            )
        )

    data = handle_data(response, output)

    if output == Path("-"):
        typer.echo(
            json.dumps(
                data,
                default=str,
            )
        )


# Command for getting audio features of one or more tracks
@cli.command()
def get_audio_features(
    track_ids: List[str] = typer.Option(
        ...,
        "--id",
        help="Spotify track ID(s). Use '-' if providing a file with IDs.",
    ),
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
    file: Path = typer.Option(
        "",
        "--file",
        "-f",
        help="A newline-delimited file with a list of track IDs. One per line.",
    ),
):
    token_info = ensure_token_info()
    if track_ids[0] != "-":
        if len(track_ids) == 1:
            response = handle_response(
                get_track_audio_features(
                    access_token=token_info["access_token"],
                    track_id=track_ids[0],
                )
            )
        else:
            response = handle_response(
                get_several_tracks_audio_features(
                    access_token=token_info["access_token"],
                    track_ids=track_ids,
                )
            )

        data = handle_data(response, output)

        if output == Path("-"):
            typer.echo(
                json.dumps(
                    data,
                    default=str,
                )
            )
    else:
        if (file.suffix == ".txt") | (file.suffix == ".csv"):
            ids = handle_id_file(file)
            for _id in ids:
                response = handle_response(
                    get_track_audio_features(
                        access_token=token_info["access_token"],
                        track_id=_id,
                    )
                )
                if output == Path("-"):
                    data = handle_data(response, output)
                    typer.echo(
                        json.dumps(
                            data,
                            default=str,
                        )
                    )
                else:
                    if output.is_dir():
                        data = handle_data(response, output.joinpath(f"{_id}.json"))
                    else:
                        data = handle_data(response, Path(f"{_id}.json"))
        else:
            print("Provide a .txt or .csv file with one ID per line.")


if __name__ == "__main__":
    cli()
