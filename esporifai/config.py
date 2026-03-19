from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from hashlib import blake2b

from dotenv import dotenv_values


class ConfigError(RuntimeError):
    pass


def _load_environment() -> dict[str, str]:
    config = {**dotenv_values(), **os.environ}
    return {key: value for key, value in config.items() if value is not None}


def _require(config: dict[str, str], key: str) -> str:
    value = config.get(key)
    if value:
        return value
    raise ConfigError(f"Missing required configuration: {key}")


@dataclass(frozen=True)
class Settings:
    spotify_client_id: str
    spotify_auth_string: str
    redirect_uri: str
    username: str | None
    password: str | None
    spotify_refresh_token: str | None = None
    request_timeout_seconds: float = 30.0
    browser_slow_mo_ms: int = 300
    login_timeout_ms: int = 30_000
    consent_timeout_ms: int = 5_000
    redirect_timeout_ms: int = 90_000

    @property
    def user_id(self) -> str:
        identity = (
            f"{self.username}:{self.password}"
            if self.username and self.password
            else self.spotify_refresh_token or self.spotify_client_id
        )
        return blake2b(
            identity.encode("utf-8"),
            digest_size=13,
        ).hexdigest()

    @classmethod
    def from_env(cls) -> "Settings":
        config = _load_environment()
        username = config.get("USERNAME") or config.get("SPOTIFY_USERNAME")
        password = config.get("PASSWORD") or config.get("SPOTIFY_PASSWORD")
        spotify_refresh_token = config.get("SPOTIFY_REFRESH_TOKEN")

        if spotify_refresh_token is None and not (username and password):
            raise ConfigError(
                "Missing required configuration: USERNAME/PASSWORD or SPOTIFY_REFRESH_TOKEN"
            )

        return cls(
            spotify_client_id=_require(config, "SPOTIFY_CLIENT_ID"),
            spotify_auth_string=_require(config, "SPOTIFY_AUTH_STRING"),
            redirect_uri=_require(config, "REDIRECT_URI"),
            username=username,
            password=password,
            spotify_refresh_token=spotify_refresh_token,
            request_timeout_seconds=float(
                config.get("ESPORIFAI_REQUEST_TIMEOUT_SECONDS", "30.0")
            ),
            browser_slow_mo_ms=int(config.get("ESPORIFAI_BROWSER_SLOW_MO_MS", "300")),
            login_timeout_ms=int(config.get("ESPORIFAI_LOGIN_TIMEOUT_MS", "30000")),
            consent_timeout_ms=int(
                config.get("ESPORIFAI_CONSENT_TIMEOUT_MS", "5000")
            ),
            redirect_timeout_ms=int(
                config.get("ESPORIFAI_REDIRECT_TIMEOUT_MS", "90000")
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
