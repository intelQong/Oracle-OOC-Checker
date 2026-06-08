import sys
from unittest.mock import patch
from pathlib import Path
from ooc_checker.cli import parse_args, _post_configure_hint


def test_parse_args_defaults():
    # Test parsed args with no subcommand
    args = parse_args([])
    assert args.command is None
    assert args.watch is False
    assert args.interval == 300
    assert args.verbose is False


def test_parse_args_configure():
    # Test parse args with configure subcommand
    args = parse_args(["configure"])
    assert args.command == "configure"
    assert args.watch is False
    assert args.interval == 300
    assert args.verbose is False


def test_post_configure_hint():
    dest = Path(".env")
    with patch("sys.platform", "win32"):
        hint = _post_configure_hint(dest)
        assert "PowerShell" in hint
        assert "Get-Content" in hint

    with patch("sys.platform", "linux"):
        hint = _post_configure_hint(dest)
        assert "set -a" in hint
        assert "PowerShell" not in hint
