import json

import pytest
from typer.testing import CliRunner
from esporifai import cli, __app_name__, __version__

runner = CliRunner()


@pytest.mark.parametrize(
    "options",
    (["--help"],),
)
def test_help(options):
    result = CliRunner().invoke(cli.cli, options)
    assert result.exit_code == 0
    assert "Usage: " in result.output


def test_get_analyze_track():
    result = CliRunner().invoke(
        cli.cli, "analyze-track 4hPl8CtzHoh9LMmKTFyiPl --output -"
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "track" in output.keys()
    assert "meta" in output.keys()
    assert "sections" in output.keys()


def test_get_artist():
    result = CliRunner().invoke(
        cli.cli, "get-artists --id 4RtYPfT9hi1qBolEuVArOG --output -"
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert output["name"] == "La Plebada"


def test_get_artists():
    result = CliRunner().invoke(
        cli.cli,
        "get-artists --id 4RtYPfT9hi1qBolEuVArOG --id 3vV4Tf1iC8vEP9fLOLGUfP --output -",
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "artists" in output.keys()
    assert len(output["artists"]) == 2
    artists = output["artists"]
    assert artists[0]["name"] == "La Plebada"
    assert artists[1]["name"] == "La Banda Baston"
