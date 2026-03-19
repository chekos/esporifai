# esporifai

[![PyPI](https://img.shields.io/pypi/v/esporifai.svg)](https://pypi.org/project/esporifai/)
[![Changelog](https://img.shields.io/github/v/release/chekos/esporifai?include_prereleases&label=changelog)](https://github.com/chekos/esporifai/releases)
[![Tests](https://github.com/chekos/esporifai/workflows/Test/badge.svg)](https://github.com/chekos/esporifai/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/chekos/esporifai/blob/master/LICENSE)

A modern CLI for collecting Spotify listening data from the Spotify Web API.

## Installation

Install this tool using `pip`:

    pip install esporifai

For development:

    python -m pip install -e '.[dev]'

## Usage

For help, run:

    esporifai --help

You can also use:

    python -m esporifai --help

### Recently played tracks
To retrieve recently played tracks, run:

    esporifai get-recently-played

For help,

    esporifai get-recently-played --help

### Authentication

`esporifai` uses Spotify authorization code flow and stores auth artifacts in your app config directory.

Required environment variables:

    SPOTIFY_CLIENT_ID=...
    SPOTIFY_AUTH_STRING=...
    REDIRECT_URI=...
    USERNAME=...
    PASSWORD=...

Useful auth commands:

    esporifai auth --check
    esporifai auth --status
    esporifai auth --force

Optional runtime tuning:

    ESPORIFAI_REQUEST_TIMEOUT_SECONDS=30
    ESPORIFAI_BROWSER_SLOW_MO_MS=300
    ESPORIFAI_LOGIN_TIMEOUT_MS=30000
    ESPORIFAI_CONSENT_TIMEOUT_MS=5000
    ESPORIFAI_REDIRECT_TIMEOUT_MS=90000

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:

    cd esporifai
    python -m venv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    python -m pip install -e '.[dev]'

To run the tests:

    python -m pytest -m "not integration"

To run the live Spotify integration tests:

    python -m pytest -m integration
