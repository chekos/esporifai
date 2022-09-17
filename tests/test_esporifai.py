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
    assert result.output.strip().startswith("Usage: ")
    assert "--help" in result.output
