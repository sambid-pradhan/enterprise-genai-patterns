import logging
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    cwd: str | None
    exit_code: int
    stdout: str
    stderr: str


class CommandExecutionError(RuntimeError):
    pass


class CommandTimeoutError(CommandExecutionError):
    pass


class CommandRunner:
    def run(
        self,
        command: Sequence[str],
        cwd: Path | None = None,
        timeout_seconds: int | None = None,
    ) -> CommandResult:
        command_list = list(command)
        cwd_text = str(cwd) if cwd is not None else None
        logger.info("Running command", extra={"command": command_list, "cwd": cwd_text})
        try:
            completed = subprocess.run(
                command_list,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CommandTimeoutError(f"Command timed out after {timeout_seconds}s: {command_list}") from exc
        except OSError as exc:
            raise CommandExecutionError(f"Command failed to start: {command_list}") from exc

        return CommandResult(
            command=command_list,
            cwd=cwd_text,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
