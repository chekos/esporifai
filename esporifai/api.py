import httpx

from .constants import SPOTIFY_API_BASE_URL
from .utils import handle_authorization, handle_response


def get_user_top_items(
    access_token: str,
    item_type: str,
    limit: int = 20,
    offset: int = 0,
    time_range: str = "medium_term",
):
    """Get the current user's top artists or tracks based on calculated affinity. Requires 'user-top-read' scope.

    Parameters
    ----------
    access_token : str
        Access token for authenticated user
    item_type : str
        The type of entity to return. Valid values: "artists" or "tracks"
    limit : int
        The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
    offset : int
        The index of the first item to return. Default: 0 (the first item). Use with limit to get the next set of items.
    time_range : str
        Over what time frame the affinities are computed.
        Valid values: "long_term" (calculated from several years of data and including all new data as it becomes available),
        "medium_term" (approximately last 6 months), "short_term" (approximately last 4 weeks).
        Default: medium_term
    """
    url = f"{SPOTIFY_API_BASE_URL}/me/top/{item_type}"
    params = {
        "limit": limit,
        "offset": offset,
        "time_range": time_range,
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    response = httpx.get(url=url, params=params, headers=headers)

    return response


def get_user_recently_played(
    access_token: str,
    timestamp: int,
    direction: str = "before",
    limit: int = 20,
):
    """Get tracks from the current user's recently played tracks.
    Note: Currently doesn't support podcast episodes.

    Parameters
    ----------
    access_token : str
        Access token for the authenticated user.
    timestamp : int
        A Unix timestamp in milliseconds.
    direction : str, optional
        Whether to check 'before' or 'after' timestamp, by default "before"
    limit : int, optional
        The maximum number of items to return, by default 20
    """
    url = f"{SPOTIFY_API_BASE_URL}/me/player/recently-played"
    params = {
        direction: timestamp,
        "limit": limit,
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    response = httpx.get(url=url, params=params, headers=headers)

    return response


if __name__ == "__main__":
    token_info = handle_authorization(save_files=True)
    response = get_user_top_items(
        token_info["access_token"],
        item_type="artists",
        limit=20,
        time_range="medium_term",
    )
    handle_response(response, write=True, filename="top_20_artists_medium_term.json")
