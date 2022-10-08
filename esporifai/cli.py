from pathlib import Path
from datetime import datetime as dt
import json
from typing import List

import typer
from rich import print
from pytz import timezone

from .api import (
    get_track_audio_analysis,
    get_user_top_items,
    get_user_recently_played,
    get_artist,
    get_several_artists,
    get_track,
    get_several_tracks,
)
from .constants import (
    APP_DIR,
    GetTopItems,
    GetTopTimeRanges,
    GetRecentlyPlayedDirections,
    __version__,
    __app_name__,
)
from .utils import auth_check, handle_authorization, handle_response, handle_data


def init():
    if not APP_DIR.exists():
        APP_DIR.mkdir()
    global token_info
    token_info = handle_authorization(save_files=True)


cli = typer.Typer(callback=init)


@cli.command()
def auth(
    force: bool = typer.Option(False, "--force", help="Force authorization flow"),
    check: bool = typer.Option(
        False, "--check", help="Check if auth credentials are saved."
    ),
):
    if check:
        print(auth_check())
        return None

    global token_info
    token_info = handle_authorization(save_files=True, force=force)


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
    # transform date from timestamp to unix timestamp in milliseconds
    timestamp = timestamp.replace(tzinfo=timezone(time_zone))
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
    track_id: str,
    output: Path = typer.Option(
        "output.json",
        "--output",
        "-o",
        help="File to write output to.",
        allow_dash=True,
    ),
):
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


if __name__ == "__main__":
    cli()
