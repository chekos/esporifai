import json
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from typer import Exit

from .constants import (
    AUTH_CODE_URL,
    AUTH_FILE,
    AUTH_STRING,
    PASSWORD,
    REDIRECT_URI,
    SCOPE,
    SPOTIFY_TOKEN_URL,
    TOKEN_FILE,
    USERNAME,
    __app_name__,
    __version__,
    ESPORIFAI_ID,
)


def auth_check(user_id: str = ESPORIFAI_ID):
    with open(AUTH_FILE, "r") as auth_file:
        auth_file = json.load(auth_file)
    return bool(auth_file.get(user_id))


def is_expired(expires_at):
    now = dt.now()
    return now > dt.fromisoformat(expires_at)


def retrieve_code(write: bool = False):
    with sync_playwright() as p:
        browser = p.chromium.launch(slow_mo=300)
        context = browser.new_context()
        page = context.new_page()
        page.goto(AUTH_CODE_URL)

        # Interact with login form
        page.locator("#login-username").fill(USERNAME)
        page.locator("#login-password").fill(PASSWORD)
        page.locator("#login-button").click()
        try:
            page.locator("[data-testid=auth-accept]").click(timeout=3_000)
        except:
            pass
        page.wait_for_url(f"{REDIRECT_URI}**", timeout=90_000)

        # Authorized page
        auth = {ESPORIFAI_ID: {}}
        auth[ESPORIFAI_ID]["code"] = page.url.split("code=")[-1]
        auth[ESPORIFAI_ID]["scope"] = SCOPE

        if write:

            with open(AUTH_FILE, "w") as auth_file:
                json.dump(auth, auth_file)

        return auth[ESPORIFAI_ID]


def request_token(
    code: str,
    write: bool = False,
):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Authorization": f"Basic {AUTH_STRING}"}

    response = httpx.post(
        url=SPOTIFY_TOKEN_URL, headers=headers, data=data, verify=True
    )
    response_data = response.json()

    response_data["expires_at"] = dt.now() + timedelta(
        seconds=int(response_data["expires_in"])
    )

    token_data = {ESPORIFAI_ID: response_data}

    if write:
        with open(TOKEN_FILE, "w") as token_file:
            json.dump(token_data, token_file, default=str)

    return response_data


def refresh_token(
    refresh_token: str,
    write: bool = False,
):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    headers = {"Authorization": f"Basic {AUTH_STRING}"}

    response = httpx.post(
        url=SPOTIFY_TOKEN_URL, headers=headers, data=data, verify=True
    )
    response_data = response.json()

    response_data["expires_at"] = dt.now() + timedelta(
        seconds=int(response_data["expires_in"])
    )
    response_data["refresh_token"] = refresh_token

    token_data = {ESPORIFAI_ID: response_data}

    if write:
        with open(TOKEN_FILE, "w") as token_file:
            json.dump(token_data, token_file, default=str)

    return response_data


def handle_authorization(save_files: bool = False, force: bool = False):
    if force:
        auth = retrieve_code(write=True)
        token_info = request_token(auth["code"], write=True)
        return token_info

    if AUTH_FILE.exists():
        with open(AUTH_FILE, "r") as auth_file:
            auth_file = json.load(auth_file)

        if ESPORIFAI_ID in auth_file.keys():
            auth = auth_file[ESPORIFAI_ID]
            if auth["scope"] != SCOPE:
                # need new code
                auth = retrieve_code(write=save_files)
        else:
            auth = retrieve_code(write=save_files)
    else:
        auth = retrieve_code(write=save_files)

    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "r") as token_file:
            token_info_file = json.load(token_file)

        if ESPORIFAI_ID in token_info_file.keys():
            token_info = token_info_file[ESPORIFAI_ID]
            if is_expired(token_info["expires_at"]):
                token_info = refresh_token(
                    token_info["refresh_token"], write=save_files
                )
        else:
            token_info = request_token(auth["code"], write=save_files)
    else:
        token_info = request_token(auth["code"], write=save_files)

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
