import subprocess
from unittest.mock import patch

import pytest

from agent_reach.integrations.openshell import (
    OpenShellError,
    exec_in_sandbox,
)


def test_exec_in_sandbox_passes_arguments_without_host_shell():
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="collected sources",
        stderr="",
    )
    with patch(
        "agent_reach.integrations.openshell.subprocess.run",
        return_value=completed,
    ) as run:
        result = exec_in_sandbox(
            "collector",
            ["python", "-c", "print('hello; world')"],
            workdir="/workspace",
        )

    assert result.ok
    assert result.stdout == "collected sources"
    run.assert_called_once()
    args, kwargs = run.call_args
    assert args[0] == [
        "openshell",
        "sandbox",
        "exec",
        "--name",
        "collector",
        "--workdir",
        "/workspace",
        "--",
        "python",
        "-c",
        "print('hello; world')",
    ]
    assert kwargs["check"] is False


def test_exec_in_sandbox_preserves_nonzero_exit_status():
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=2,
        stdout="",
        stderr="source unavailable",
    )
    with patch(
        "agent_reach.integrations.openshell.subprocess.run",
        return_value=completed,
    ):
        result = exec_in_sandbox("collector", ["fetch-source"])

    assert not result.ok
    assert result.returncode == 2
    assert result.stderr == "source unavailable"


@pytest.mark.parametrize(
    ("sandbox_name", "command", "kwargs"),
    [
        ("", ["echo", "ok"], {}),
        ("collector", [], {}),
        ("collector", "echo ok", {}),
        ("collector", ["echo", "ok"], {"timeout": 0}),
        ("collector", ["echo", "ok"], {"workdir": ""}),
    ],
)
def test_exec_in_sandbox_rejects_invalid_arguments(
    sandbox_name, command, kwargs
):
    with pytest.raises(ValueError):
        exec_in_sandbox(sandbox_name, command, **kwargs)


def test_exec_in_sandbox_reports_missing_cli():
    with patch(
        "agent_reach.integrations.openshell.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        with pytest.raises(OpenShellError, match="OpenShell CLI not found"):
            exec_in_sandbox("collector", ["echo", "ok"])


def test_exec_in_sandbox_reports_timeout():
    with patch(
        "agent_reach.integrations.openshell.subprocess.run",
        side_effect=subprocess.TimeoutExpired("openshell", 1),
    ):
        with pytest.raises(OpenShellError, match="timed out"):
            exec_in_sandbox("collector", ["echo", "ok"], timeout=1)
