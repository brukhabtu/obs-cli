"""Test CLI functionality."""

from click.testing import CliRunner
from obs_cli.cli import cli


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Obsidian CLI' in result.output


def test_notes_help():
    """Test notes command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['notes', '--help'])
    assert result.exit_code == 0
    assert 'Manage and query Obsidian notes' in result.output


def test_tags_help():
    """Test tags command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ['tags', '--help'])
    assert result.exit_code == 0
    assert 'Manage and query Obsidian tags' in result.output