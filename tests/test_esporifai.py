import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
from esporifai import cli, __app_name__, __version__

runner = CliRunner()


@pytest.mark.parametrize(
    "options",
    (["--help"],),
)
def test_help(options):
    result = runner.invoke(cli.cli, options)
    assert result.exit_code == 0
    assert "Usage: " in result.output


def test_analyze_track():
    result = runner.invoke(
        cli.cli, ["analyze-track", "4hPl8CtzHoh9LMmKTFyiPl", "--output", "-"]
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert "track" in output.keys()
    assert "meta" in output.keys()
    assert "sections" in output.keys()


def test_analyze_tracks(tmp_path):
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


def test_get_artist():
    result = runner.invoke(
        cli.cli, ["get-artists", "--id", "4RtYPfT9hi1qBolEuVArOG", "--output", "-"]
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert output["name"] == "La Plebada"


def test_get_artists():
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


def test_get_track():
    result = runner.invoke(
        cli.cli, ["get-tracks", "--id", "4hPl8CtzHoh9LMmKTFyiPl", "--output", "-"]
    )
    output = json.loads(result.output)
    assert result.exit_code == 0
    assert output["name"] == "Lupe Esparza"
    assert output["artists"][0]["name"] == "La Banda Baston"


def test_get_tracks():
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
