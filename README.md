# esporifai

[![PyPI](https://img.shields.io/pypi/v/esporifai.svg)](https://pypi.org/project/esporifai/)
[![Changelog](https://img.shields.io/github/v/release/chekos/esporifai?include_prereleases&label=changelog)](https://github.com/chekos/esporifai/releases)
[![Tests](https://github.com/chekos/esporifai/workflows/Test/badge.svg)](https://github.com/chekos/esporifai/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/chekos/esporifai/blob/master/LICENSE)

A simple CLI to get data from the Spotify API

## Installation

Install this tool using `pip`:

    pip install esporifai

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

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:

    cd esporifai
    python -m venv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest
