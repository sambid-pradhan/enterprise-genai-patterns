import pytest

from app.command_runner import CommandRunner, CommandTimeoutError


def test_command_runner_captures_success_output():
    result = CommandRunner().run(["python", "-c", "print('hello')"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert result.stderr == ""


def test_command_runner_captures_nonzero_exit():
    result = CommandRunner().run(
        ["python", "-c", "import sys; print('bad', file=sys.stderr); sys.exit(7)"]
    )

    assert result.exit_code == 7
    assert result.stdout == ""
    assert result.stderr.strip() == "bad"


def test_command_runner_raises_timeout():
    with pytest.raises(CommandTimeoutError):
        CommandRunner().run(["python", "-c", "import time; time.sleep(2)"], timeout_seconds=1)
