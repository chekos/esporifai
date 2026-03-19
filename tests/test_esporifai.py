import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from typer.testing import CliRunner
from esporifai import cli, __app_name__, __version__
from esporifai.config import get_settings
from esporifai import utils

runner = CliRunner()
integration = pytest.mark.integration


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def require_spotify_env():
    missing = [
        key
        for key in (
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_AUTH_STRING",
            "REDIRECT_URI",
            "USERNAME",
            "PASSWORD",
        )
        if not os.environ.get(key)
    ]
    if missing:
        pytest.skip(f"Missing Spotify integration env vars: {', '.join(missing)}")


@pytest.mark.parametrize(
    "options",
    (["--help"],),
)
def test_help(options):
    result = runner.invoke(cli.cli, options)
    assert result.exit_code == 0
    assert "Usage: " in result.output


def test_auth_check_without_saved_files_returns_false(monkeypatch, tmp_path):
    monkeypatch.setattr(utils, "AUTH_FILE", tmp_path / "auth.json")
    monkeypatch.setattr(utils, "TOKEN_FILE", tmp_path / "token_info.json")
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_AUTH_STRING", raising=False)
    monkeypatch.delenv("REDIRECT_URI", raising=False)
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)

    assert utils.auth_check() is False


def test_settings_accept_spotify_username_password_aliases(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("SPOTIFY_USERNAME", "sergio")
    monkeypatch.setenv("SPOTIFY_PASSWORD", "secret")
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)

    settings = get_settings()

    assert settings.username == "sergio"
    assert settings.password == "secret"


def test_settings_accept_refresh_token_without_password_credentials(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "refresh-token")
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)
    monkeypatch.delenv("SPOTIFY_USERNAME", raising=False)
    monkeypatch.delenv("SPOTIFY_PASSWORD", raising=False)

    settings = get_settings()

    assert settings.spotify_refresh_token == "refresh-token"
    assert settings.username is None
    assert settings.password is None


def test_auth_check_command_skips_authorization(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("handle_authorization should not run for auth --check")

    monkeypatch.setattr(cli, "handle_authorization", fail)
    monkeypatch.setattr(cli, "auth_check", lambda: True)
    monkeypatch.setattr(cli, "token_info", None)

    result = runner.invoke(cli.cli, ["auth", "--check"])

    assert result.exit_code == 0
    assert "True" in result.output


def test_build_auth_code_url_uses_standard_authorize_query(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("USERNAME", "sergio")
    monkeypatch.setenv("PASSWORD", "secret")

    url = utils.build_auth_code_url(get_settings())

    assert "client_id=client-id" in url
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
    assert "response_type=code" in url


def test_build_auth_code_url_normalizes_preencoded_redirect_uri(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https%3A%2F%2Fexample.com%2Fcallback%2F")
    monkeypatch.setenv("USERNAME", "sergio")
    monkeypatch.setenv("PASSWORD", "secret")

    url = utils.build_auth_code_url(get_settings())

    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback%2F" in url
    assert "redirect_uri=https%253A" not in url


def test_auth_url_command_only_requires_client_id_and_redirect_uri(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("REDIRECT_URI", "https%3A%2F%2Fexample.com%2Fcallback%2F")
    monkeypatch.delenv("SPOTIFY_AUTH_STRING", raising=False)
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)
    monkeypatch.delenv("SPOTIFY_USERNAME", raising=False)
    monkeypatch.delenv("SPOTIFY_PASSWORD", raising=False)
    monkeypatch.delenv("SPOTIFY_REFRESH_TOKEN", raising=False)

    result = runner.invoke(cli.cli, ["auth", "--url"])
    output = "".join(result.output.splitlines())
    query = parse_qs(urlparse(output).query)

    assert result.exit_code == 0
    assert query["response_type"] == ["code"]
    assert query["redirect_uri"] == ["https://example.com/callback/"]
    assert "redirect_uri=https%253A" not in output


def test_retrieve_code_handles_two_step_login(monkeypatch, tmp_path):
    class FakeTimeoutError(Exception):
        pass

    class FakeLocator:
        def __init__(self, page, selector):
            self.page = page
            self.selector = selector
            self.first = self

        def wait_for(self, timeout=None):
            self.page.calls.append(("wait_for", self.selector, timeout))
            if self.selector == "[data-testid='auth-accept']":
                raise FakeTimeoutError()
            if (
                self.selector
                == "#password, [data-testid='login-password'], input[type='password'], input[autocomplete='current-password']"
                and self.page.password_wait_attempts == 0
            ):
                self.page.password_wait_attempts += 1
                raise FakeTimeoutError()

        def fill(self, value):
            self.page.calls.append(("fill", self.selector, value))

        def click(self):
            self.page.calls.append(("click", self.selector))

    class FakePage:
        def __init__(self):
            self.calls = []
            self.url = "https://example.com/callback?code=test-code"
            self.password_wait_attempts = 0

        def goto(self, url, wait_until=None):
            self.calls.append(("goto", url, wait_until))

        def locator(self, selector):
            self.calls.append(("locator", selector))
            return FakeLocator(self, selector)

        def get_by_role(self, role, name=None):
            selector = f"{role}:{getattr(name, 'pattern', name)}"
            self.calls.append(("get_by_role", selector))
            return FakeLocator(self, selector)

        def wait_for_url(self, pattern, timeout=None):
            self.calls.append(("wait_for_url", pattern, timeout))

        def wait_for_timeout(self, timeout):
            self.calls.append(("wait_for_timeout", timeout))

    class FakeContext:
        def __init__(self, page):
            self.page = page

        def new_page(self):
            return self.page

    class FakeBrowser:
        def __init__(self, page):
            self.page = page

        def new_context(self):
            return FakeContext(self.page)

        def close(self):
            self.page.calls.append(("browser_close",))

    class FakeChromium:
        def __init__(self, page):
            self.page = page

        def launch(self, slow_mo=None):
            self.page.calls.append(("launch", slow_mo))
            return FakeBrowser(self.page)

    class FakePlaywright:
        def __init__(self, page):
            self.chromium = FakeChromium(page)

    class FakePlaywrightManager:
        def __init__(self, page):
            self.page = page

        def __enter__(self):
            return FakePlaywright(self.page)

        def __exit__(self, exc_type, exc, tb):
            return False

    page = FakePage()

    monkeypatch.setattr(utils, "sync_playwright", lambda: FakePlaywrightManager(page))
    monkeypatch.setattr(utils, "PlaywrightTimeoutError", FakeTimeoutError)
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("USERNAME", "sergio")
    monkeypatch.setenv("PASSWORD", "secret")
    monkeypatch.setattr(utils, "AUTH_FILE", tmp_path / "auth.json")

    auth = utils.retrieve_code(write=True)

    assert auth["code"] == "test-code"
    assert ("locator", "#username, [data-testid='login-username']") in page.calls
    assert (
        "locator",
        "#password, [data-testid='login-password'], input[type='password'], input[autocomplete='current-password']",
    ) in page.calls
    assert ("fill", "#username, [data-testid='login-username']", "sergio") in page.calls
    assert (
        "wait_for",
        "#password, [data-testid='login-password'], input[type='password'], input[autocomplete='current-password']",
        500,
    ) in page.calls
    assert any(
        call[0] == "get_by_role" and "password" in call[1].lower()
        for call in page.calls
    )
    assert (
        "fill",
        "#password, [data-testid='login-password'], input[type='password'], input[autocomplete='current-password']",
        "secret",
    ) in page.calls
    assert any(
        call == ("wait_for_url", "https://example.com/callback**", 1_000)
        for call in page.calls
    )
    assert utils.AUTH_FILE.exists()


def test_auth_status_reports_saved_token(monkeypatch, tmp_path):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("USERNAME", "sergio")
    monkeypatch.setenv("PASSWORD", "secret")
    monkeypatch.setattr(utils, "AUTH_FILE", tmp_path / "auth.json")
    monkeypatch.setattr(utils, "TOKEN_FILE", tmp_path / "token.json")

    settings = get_settings()
    utils.write_json(utils.AUTH_FILE, {settings.user_id: {"code": "abc", "scope": utils.SCOPE}})
    utils.write_json(
        utils.TOKEN_FILE,
        {settings.user_id: {"access_token": "token", "expires_at": "2099-01-01 00:00:00"}},
    )

    status = utils.get_auth_status()

    assert status["has_auth_artifact"] is True
    assert status["has_token_artifact"] is True
    assert status["token_expired"] is False


def test_handle_authorization_prefers_refresh_token_env(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "refresh-token")
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)
    monkeypatch.delenv("SPOTIFY_USERNAME", raising=False)
    monkeypatch.delenv("SPOTIFY_PASSWORD", raising=False)

    monkeypatch.setattr(utils, "load_json", lambda path: {})
    monkeypatch.setattr(
        utils,
        "refresh_token",
        lambda refresh_token, write=False, settings=None: {
            "access_token": "token",
            "refresh_token": refresh_token,
        },
    )

    token_info = utils.handle_authorization(save_files=False, force=False)

    assert token_info["refresh_token"] == "refresh-token"


def test_handle_authorization_force_still_prefers_refresh_token_env(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_AUTH_STRING", "auth-string")
    monkeypatch.setenv("REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("SPOTIFY_REFRESH_TOKEN", "refresh-token")
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)
    monkeypatch.delenv("SPOTIFY_USERNAME", raising=False)
    monkeypatch.delenv("SPOTIFY_PASSWORD", raising=False)

    monkeypatch.setattr(utils, "load_json", lambda path: {})
    monkeypatch.setattr(
        utils,
        "refresh_token",
        lambda refresh_token, write=False, settings=None: {
            "access_token": "token",
            "refresh_token": refresh_token,
        },
    )

    token_info = utils.handle_authorization(save_files=False, force=True)

    assert token_info["refresh_token"] == "refresh-token"


@integration
def test_analyze_track():
    require_spotify_env()
    result = runner.invoke(
        cli.cli, ["analyze-track", "4hPl8CtzHoh9LMmKTFyiPl", "--output", "-"]
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "track" in output.keys()
    assert "meta" in output.keys()
    assert "sections" in output.keys()


@integration
def test_analyze_tracks(tmp_path):
    require_spotify_env()
    track_ids_file = tmp_path.joinpath("track_ids.txt")
    with open(track_ids_file, "w") as file:
        file.write("2pEa0vCzu86pDLz9KPDAcg\n")  # Alivianado
        file.write("2O8aEi9SpwobvFLvKHvIl3\n")  # Estamos Bien
        file.write("1XReTPKaJypMIXSvOW9YXV\n")  # Semillas
    runner.invoke(
        cli.cli,
        [
            "analyze-track",
            "-",
            "--file",
            f"{track_ids_file}",
            "--output",
            f"{tmp_path}",
        ],
    )
    analysis_files = sorted([file.name for file in tmp_path.glob("*.json")])
    assert analysis_files == [
        "1XReTPKaJypMIXSvOW9YXV.json",
        "2O8aEi9SpwobvFLvKHvIl3.json",
        "2pEa0vCzu86pDLz9KPDAcg.json",
    ]


@integration
def test_get_artist():
    require_spotify_env()
    result = runner.invoke(
        cli.cli, ["get-artists", "--id", "4RtYPfT9hi1qBolEuVArOG", "--output", "-"]
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert output["name"] == "La Plebada"


@integration
def test_get_artists():
    require_spotify_env()
    result = runner.invoke(
        cli.cli,
        [
            "get-artists",
            "--id",
            "4RtYPfT9hi1qBolEuVArOG",
            "--id",
            "3vV4Tf1iC8vEP9fLOLGUfP",
            "--output",
            "-",
        ],
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "artists" in output.keys()
    assert len(output["artists"]) == 2
    artists = output["artists"]
    assert artists[0]["name"] == "La Plebada"
    assert artists[1]["name"] == "La Banda Baston"


@integration
def test_get_track():
    require_spotify_env()
    result = runner.invoke(
        cli.cli, ["get-tracks", "--id", "4hPl8CtzHoh9LMmKTFyiPl", "--output", "-"]
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert output["name"] == "Lupe Esparza"
    assert output["artists"][0]["name"] == "La Banda Baston"


@integration
def test_get_tracks():
    require_spotify_env()
    result = runner.invoke(
        cli.cli,
        [
            "get-tracks",
            "--id",
            "4hPl8CtzHoh9LMmKTFyiPl",
            "--id",
            "2O8aEi9SpwobvFLvKHvIl3",
            "--output",
            "-",
        ],
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "tracks" in output.keys()
    assert len(output["tracks"]) == 2
    tracks = output["tracks"]
    assert tracks[0]["name"] == "Lupe Esparza"
    assert tracks[1]["name"] == "Estamos Bien"
    assert len(tracks[0]["artists"]) == 2
    assert tracks[0]["artists"][0]["name"] == "La Banda Baston"
    assert tracks[0]["artists"][1]["name"] == "Primero Company"


@integration
def test_get_audio_features():
    require_spotify_env()
    result = runner.invoke(
        cli.cli,
        [
            "get-audio-features",
            "--id",
            "4hPl8CtzHoh9LMmKTFyiPl",
            "--id",
            "2O8aEi9SpwobvFLvKHvIl3",
            "--output",
            "-",
        ],
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "audio_features" in output.keys()
    assert len(output["audio_features"]) == 2
    audio_features = output["audio_features"]
    assert audio_features[0]["id"] == "4hPl8CtzHoh9LMmKTFyiPl"
    assert "danceability" in audio_features[0].keys()
    assert "energy" in audio_features[0].keys()
    assert "key" in audio_features[0].keys()
    assert "loudness" in audio_features[0].keys()
    assert "mode" in audio_features[0].keys()
    assert "speechiness" in audio_features[0].keys()
    assert "acousticness" in audio_features[0].keys()
    assert "instrumentalness" in audio_features[0].keys()
    assert "liveness" in audio_features[0].keys()
    assert "valence" in audio_features[0].keys()
    assert "tempo" in audio_features[0].keys()
    assert "type" in audio_features[0].keys()
    assert "uri" in audio_features[0].keys()
    assert "track_href" in audio_features[0].keys()
    assert "analysis_url" in audio_features[0].keys()
    assert "duration_ms" in audio_features[0].keys()
    assert "time_signature" in audio_features[0].keys()
    assert audio_features[1]["id"] == "2O8aEi9SpwobvFLvKHvIl3"
    assert "danceability" in audio_features[1].keys()
    assert "energy" in audio_features[1].keys()
    assert "key" in audio_features[1].keys()
    assert "loudness" in audio_features[1].keys()
    assert "mode" in audio_features[1].keys()
    assert "speechiness" in audio_features[1].keys()
    assert "acousticness" in audio_features[1].keys()
    assert "instrumentalness" in audio_features[1].keys()
    assert "liveness" in audio_features[1].keys()
    assert "valence" in audio_features[1].keys()
    assert "tempo" in audio_features[1].keys()
    assert "type" in audio_features[1].keys()
    assert "uri" in audio_features[1].keys()
    assert "track_href" in audio_features[1].keys()
    assert "analysis_url" in audio_features[1].keys()
    assert "duration_ms" in audio_features[1].keys()
    assert "time_signature" in audio_features[1].keys()
