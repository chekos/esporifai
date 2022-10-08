import os
import urllib.parse
from enum import Enum
from pathlib import Path
from hashlib import blake2b

from dotenv import dotenv_values
from typer import get_app_dir

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

__app_name__ = "esporifai"
APP_DIR: Path = Path(get_app_dir(__app_name__))

AUTH_FILE = APP_DIR.joinpath("auth.json")
TOKEN_FILE = APP_DIR.joinpath("token_info.json")
config = {**dotenv_values(), **os.environ}

CLIENT_ID = config["SPOTIFY_CLIENT_ID"]
REDIRECT_URI = config["REDIRECT_URI"]
USERNAME = config["USERNAME"]
PASSWORD = config["PASSWORD"]
ESPORIFAI_ID = blake2b(
    f"{USERNAME}:{PASSWORD}".encode("utf-8"), digest_size=13
).hexdigest()
SCOPE = "user-read-recently-played user-top-read user-library-read playlist-read-collaborative playlist-read-private user-follow-read"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

AUTH_STRING = config["SPOTIFY_AUTH_STRING"]


access_code_params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "response_type": "code",
}

AUTH_CODE_URL = f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(access_code_params)}"


class GetTopItems(str, Enum):
    """For get_top(): The type of entity to return."""

    artists = "artists"
    tracks = "tracks"

    def __str__(self):
        return self.value


class GetTopTimeRanges(str, Enum):
    """For get_top(): Over what time frame the affinities are computed."""

    long_term = "long"
    medium_term = "medium"
    short_term = "short"

    def __str__(self):
        return self.value


class GetRecentlyPlayedDirections(str, Enum):
    """For get_recently_played(): Direction of cursor."""

    after = "after"
    before = "before"

    def __str__(self):
        return self.value
