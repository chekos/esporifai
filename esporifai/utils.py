from __future__ import annotations

import re
import json
from time import monotonic
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from typer import Exit

from .config import ConfigError, Settings, get_settings
from .constants import (
    AUTH_FILE,
    SCOPE,
    SPOTIFY_AUTH_URL,
    SPOTIFY_TOKEN_URL,
    TOKEN_FILE,
)


def load_json(path: Path):
    if not path.exists():
        return {}

    with open(path, "r") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        json.dump(payload, handle, indent=2, default=str)


def build_auth_payload(code: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    return {
        settings.user_id: {
            "code": code,
            "scope": SCOPE,
        }
    }


def build_auth_code_url(
    settings: Settings | None = None,
    *,
    client_id: str | None = None,
    redirect_uri: str | None = None,
) -> str:
    if settings is not None:
        client_id = settings.spotify_client_id
        redirect_uri = settings.redirect_uri

    if not client_id or not redirect_uri:
        raise ValueError(
            "build_auth_code_url requires either settings or client_id and redirect_uri"
        )

    return (
        f"{SPOTIFY_AUTH_URL}?"
        + urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": SCOPE,
                "response_type": "code",
            }
        )
    )


def auth_check(user_id: str | None = None):
    auth_file = load_json(AUTH_FILE)
    token_file = load_json(TOKEN_FILE)

    if user_id is None:
        try:
            user_id = get_settings().user_id
        except ConfigError:
            return bool(auth_file or token_file)

    return bool(auth_file.get(user_id) or token_file.get(user_id))


def get_auth_status(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    auth_file = load_json(AUTH_FILE)
    token_file = load_json(TOKEN_FILE)
    token_info = token_file.get(settings.user_id)
    return {
        "app_dir": str(AUTH_FILE.parent),
        "auth_file": str(AUTH_FILE),
        "token_file": str(TOKEN_FILE),
        "has_auth_artifact": bool(auth_file.get(settings.user_id)),
        "has_token_artifact": bool(token_info),
        "has_refresh_token_env": bool(settings.spotify_refresh_token),
        "token_expires_at": token_info.get("expires_at") if token_info else None,
        "token_expired": is_expired(token_info["expires_at"]) if token_info else None,
    }


def is_expired(expires_at):
    now = dt.now()
    return now > dt.fromisoformat(expires_at)


def maybe_click_consent(page) -> bool:
    candidates = [
        page.locator("[data-testid='auth-accept']").first,
        page.get_by_role(
            "button",
            name=re.compile(r"^(agree|accept|authorize|allow|continue)$", re.I),
        ).first,
    ]

    for candidate in candidates:
        try:
            candidate.wait_for(timeout=1_000)
        except PlaywrightTimeoutError:
            continue

        candidate.click()
        return True

    return False


def maybe_switch_to_password_login(page) -> bool:
    candidates = [
        page.get_by_role(
            "link",
            name=re.compile(
                r"(log ?in|login).*(with|using).*(password)|password instead",
                re.I,
            ),
        ).first,
        page.get_by_role(
            "button",
            name=re.compile(
                r"(log ?in|login).*(with|using).*(password)|password instead",
                re.I,
            ),
        ).first,
    ]

    for candidate in candidates:
        try:
            candidate.wait_for(timeout=500)
        except PlaywrightTimeoutError:
            continue

        candidate.click()
        return True

    return False


def wait_for_password_input(page, settings: Settings):
    password_selector = (
        "#password, [data-testid='login-password'], "
        "input[type='password'], input[autocomplete='current-password']"
    )
    deadline = monotonic() + (settings.login_timeout_ms / 1_000)

    while monotonic() < deadline:
        password = page.locator(password_selector).first
        try:
            password.wait_for(timeout=500)
            return password
        except PlaywrightTimeoutError:
            if maybe_switch_to_password_login(page):
                continue

            page.wait_for_timeout(500)

    raise RuntimeError(
        "Spotify did not present a password entry screen within "
        f"{settings.login_timeout_ms}ms. " + describe_page_state(page)
    )


def describe_page_state(page) -> str:
    details = [f"Last page URL: {page.url}"]

    try:
        title = page.title()
    except Exception:
        title = None
    if title:
        details.append(f"Page title: {title}")

    try:
        alerts = [
            " ".join(text.split())
            for text in page.locator("[role='alert']").all_inner_texts()
            if text.strip()
        ]
    except Exception:
        alerts = []
    if alerts:
        details.append(f"Visible alerts: {' | '.join(alerts[:3])}")

    try:
        body_text = " ".join(page.locator("body").inner_text(timeout=1_000).split())
    except Exception:
        body_text = ""
    if body_text:
        details.append(f"Body snippet: {body_text[:500]}")

    return " ".join(details)


def retrieve_code(write: bool = False, settings: Settings | None = None):
    settings = settings or get_settings()
    if not settings.username or not settings.password:
        raise ConfigError(
            "Browser authorization requires USERNAME/PASSWORD or SPOTIFY_USERNAME/SPOTIFY_PASSWORD."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(slow_mo=settings.browser_slow_mo_ms)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(build_auth_code_url(settings), wait_until="domcontentloaded")

            username_selector = "#username, [data-testid='login-username']"
            login_button_selector = "[data-testid='login-button']"

            username = page.locator(username_selector).first
            username.wait_for(timeout=settings.login_timeout_ms)
            username.fill(settings.username)
            page.locator(login_button_selector).first.click()

            password = wait_for_password_input(page, settings)
            password.fill(settings.password)
            page.locator(login_button_selector).first.click()

            redirect_pattern = f"{settings.redirect_uri}**"
            deadline = monotonic() + (settings.redirect_timeout_ms / 1_000)

            while monotonic() < deadline:
                try:
                    page.wait_for_url(redirect_pattern, timeout=1_000)
                    break
                except PlaywrightTimeoutError:
                    maybe_click_consent(page)
            else:
                raise RuntimeError(
                    "Spotify authorization did not redirect back to the configured "
                    f"redirect URI within {settings.redirect_timeout_ms}ms. "
                    + describe_page_state(page)
                )

            code = parse_qs(urlparse(page.url).query).get("code", [None])[0]
            if code is None:
                raise RuntimeError(
                    f"Spotify redirect did not include an authorization code: {page.url}"
                )

            auth = {settings.user_id: {}}
            auth[settings.user_id]["code"] = code
            auth[settings.user_id]["scope"] = SCOPE

            if write:
                write_json(AUTH_FILE, auth)

            return auth[settings.user_id]
        finally:
            browser.close()


def request_token(
    code: str,
    write: bool = False,
    settings: Settings | None = None,
):
    settings = settings or get_settings()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
    }
    headers = {"Authorization": f"Basic {settings.spotify_auth_string}"}

    response = httpx.post(
        url=SPOTIFY_TOKEN_URL,
        headers=headers,
        data=data,
        verify=True,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    response_data = response.json()

    response_data["expires_at"] = dt.now() + timedelta(
        seconds=int(response_data["expires_in"])
    )

    token_data = {settings.user_id: response_data}

    if write:
        write_json(TOKEN_FILE, token_data)

    return response_data


def refresh_token(
    refresh_token: str,
    write: bool = False,
    settings: Settings | None = None,
):
    settings = settings or get_settings()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {"Authorization": f"Basic {settings.spotify_auth_string}"}

    response = httpx.post(
        url=SPOTIFY_TOKEN_URL,
        headers=headers,
        data=data,
        verify=True,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    response_data = response.json()

    response_data["expires_at"] = dt.now() + timedelta(
        seconds=int(response_data["expires_in"])
    )
    response_data["refresh_token"] = refresh_token

    token_data = {settings.user_id: response_data}

    if write:
        write_json(TOKEN_FILE, token_data)

    return response_data


def handle_authorization(
    save_files: bool = False,
    force: bool = False,
    settings: Settings | None = None,
):
    settings = settings or get_settings()
    if force:
        token_info = load_json(TOKEN_FILE).get(settings.user_id)
        if settings.spotify_refresh_token:
            return refresh_token(
                settings.spotify_refresh_token,
                write=save_files,
                settings=settings,
            )
        if token_info and token_info.get("refresh_token"):
            return refresh_token(
                token_info["refresh_token"],
                write=save_files,
                settings=settings,
            )
        auth = retrieve_code(write=save_files, settings=settings)
        token_info = request_token(auth["code"], write=save_files, settings=settings)
        return token_info

    token_info = load_json(TOKEN_FILE).get(settings.user_id)
    if token_info:
        if not is_expired(token_info["expires_at"]):
            return token_info
        if token_info.get("refresh_token"):
            return refresh_token(
                token_info["refresh_token"],
                write=save_files,
                settings=settings,
            )

    if settings.spotify_refresh_token:
        return refresh_token(
            settings.spotify_refresh_token,
            write=save_files,
            settings=settings,
        )

    auth = load_json(AUTH_FILE).get(settings.user_id)
    if auth and auth.get("scope") == SCOPE:
        # Spotify authorization codes are single-use, so retrieve a fresh one
        # whenever we need to mint a new token.
        auth = retrieve_code(write=save_files, settings=settings)
    else:
        auth = retrieve_code(write=save_files, settings=settings)

    token_info = request_token(auth["code"], write=save_files, settings=settings)

    return token_info


def handle_response(
    response: httpx.Response,
):
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        raise Exit()


def handle_data(
    data: dict,
    output: Path,
    trim: bool = False,
    key: str = "items",
):
    if trim:
        data = data[key]

    if output != Path("-"):
        filename = output.with_suffix(".json")
        with open(filename, "w") as file:
            json.dump(data, file, indent=2, default=str)

    return data


def handle_id_file(filepath: Path):
    spotify_id_re = re.compile("[a-zA-Z0-9]{22}")
    with open(filepath, "r") as file:
        contents = file.readlines()

    ids = []
    for line in contents:
        _id = spotify_id_re.findall(line)
        if len(_id) > 0:
            ids.append(_id[0])

    return ids
