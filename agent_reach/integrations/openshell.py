"""Run commands inside NVIDIA OpenShell sandboxes."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Sequence

from agent_reach.utils.process import utf8_subprocess_env


class OpenShellError(RuntimeError):
    """Raised when the OpenShell CLI cannot be started or finishes unexpectedly."""


@dataclass(frozen=True)
class OpenShellResult:
    """Captured output from an OpenShell CLI command."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def exec_in_sandbox(
    sandbox_name: str,
    command: Sequence[str],
    *,
    workdir: str | None = None,
    timeout: int = 300,
    executable: str = "openshell",
) -> OpenShellResult:
    """Execute an argv command in a named sandbox without invoking a host shell."""
    if not sandbox_name.strip():
        raise ValueError("sandbox_name must not be empty")
    if isinstance(command, (str, bytes)) or not command:
        raise ValueError("command must be a non-empty sequence of arguments")
    if not all(isinstance(argument, str) for argument in command):
        raise ValueError("command arguments must be strings")
    if workdir is not None and not workdir.strip():
        raise ValueError("workdir must not be empty")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    if not executable:
        raise ValueError("executable must not be empty")

    args = [executable, "sandbox", "exec", "--name", sandbox_name]
    if workdir is not None:
        args.extend(["--workdir", workdir])
    args.extend(["--", *command])
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=utf8_subprocess_env(),
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise OpenShellError(
            "OpenShell CLI not found; install NVIDIA OpenShell and ensure "
            "`openshell` is on PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise OpenShellError(
            f"OpenShell command timed out after {timeout} seconds"
        ) from exc
    except OSError as exc:
        raise OpenShellError(f"Could not run OpenShell CLI: {exc}") from exc

    return OpenShellResult(
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )
