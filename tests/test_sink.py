"""Tests for the Rich loguru sink behavior."""

from __future__ import annotations

import io
import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path
from types import FrameType

import pytest
from loguru import logger
from rich.console import Console

from loguru_rich_sink import sink as sink_module
from loguru_rich_sink.sink import RichSink, find_cwd, get_logger


def _configure_run_paths(tmp_path: Path) -> None:
    """Point the sink module to temporary run-tracking paths."""
    sink_module.LOGS_DIR = tmp_path / "logs"
    sink_module.RUN_FILE = sink_module.LOGS_DIR / "run.txt"


def _raise_timeout(_signum: int, _frame: FrameType | None) -> None:
    """Raise a timeout error when a signal alarm expires."""
    raise TimeoutError("find_cwd did not stop at the filesystem root")


def _loguru_env(**overrides: str) -> dict[str, str]:
    """Return a subprocess environment with isolated Loguru settings."""
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("LOGURU_")
    }
    env.update(overrides)
    return env


def _clear_loguru_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove Loguru environment variables for default-behavior tests."""
    for name in list(os.environ):
        if name.startswith("LOGURU_"):
            monkeypatch.delenv(name, raising=False)


def test_package_import_does_not_reconfigure_loguru_handlers() -> None:
    """Ensure importing the package leaves existing Loguru handlers untouched."""
    script = textwrap.dedent(
        """
        from loguru import logger

        before = repr(logger._core.handlers)
        import loguru_rich_sink  # noqa: F401
        after = repr(logger._core.handlers)

        assert after == before, f"{before!r} changed to {after!r}"
        """
    )

    subprocess.run([sys.executable, "-c", script], check=True)


def test_find_cwd_stops_at_filesystem_root(tmp_path: Path) -> None:
    """Ensure find_cwd terminates when no pyproject.toml exists above the start."""
    previous_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    try:
        signal.alarm(1)
        cwd = find_cwd(tmp_path)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)

    assert cwd == Path(cwd.anchor)


def test_run_tracking_persists_and_increments(tmp_path: Path) -> None:
    """Ensure run tracking creates, reads, and increments the run counter."""
    _configure_run_paths(tmp_path)
    console = Console(file=io.StringIO())
    sink = RichSink(track_run=True, console=console)

    assert sink.setup() == 0
    assert sink.read() == 0
    assert sink.increment() == 1
    assert sink.read() == 1


def test_get_logger_increments_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure get_logger increments the run counter on initialization."""
    _clear_loguru_env(monkeypatch)
    _configure_run_paths(tmp_path)
    console = Console(file=io.StringIO(), record=True, force_terminal=True, width=120)

    logger_instance = get_logger(console=console, track_run=True)
    logger_instance.info("Run initialized")

    assert sink_module.RUN_FILE.read_text(encoding="utf-8") == "1"
    output = console.export_text()
    assert "Run 1" in output
    assert "Run initialized" in output


def test_get_logger_respects_loguru_level_environment() -> None:
    """Ensure LOGURU_LEVEL controls the default Rich sink handler level."""
    script = textwrap.dedent(
        """
        import io

        from rich.console import Console

        from loguru_rich_sink.sink import get_logger

        console = Console(file=io.StringIO(), record=True, force_terminal=True)
        logger = get_logger(console=console)

        logger.info("hidden info")
        logger.warning("visible warning")

        output = console.export_text()
        assert "hidden info" not in output
        assert "visible warning" in output
        """
    )
    env = _loguru_env(LOGURU_LEVEL="WARNING", LOGURU_AUTOINIT="False")

    subprocess.run([sys.executable, "-c", script], check=True, env=env)


def test_get_logger_respects_loguru_format_environment() -> None:
    """Ensure LOGURU_FORMAT controls the formatted Rich sink message text."""
    script = textwrap.dedent(
        """
        import io

        from rich.console import Console

        from loguru_rich_sink.sink import get_logger

        console = Console(file=io.StringIO(), record=True, force_terminal=True)
        logger = get_logger(console=console)

        logger.info("formatted message")

        output = console.export_text()
        assert "ENV:formatted message" in output
        """
    )
    env = _loguru_env(LOGURU_AUTOINIT="False", LOGURU_FORMAT="ENV:{message}")

    subprocess.run([sys.executable, "-c", script], check=True, env=env)


def test_rich_sink_preserves_literal_bracketed_message_text() -> None:
    """Ensure Rich markup-like text in log messages is not stripped."""
    console = Console(file=io.StringIO(), record=True, force_terminal=True)
    sink = RichSink(console=console)
    logger.remove()
    logger.add(sink, format="{message}")

    logger.info("literal [abc] bracket")

    output = console.export_text()
    assert "literal [abc] bracket" in output


def test_package_demo_runs_without_main_module_warning() -> None:
    """Ensure python -m loguru_rich_sink does not preload __main__."""
    env = _loguru_env(LOGURU_AUTOINIT="False")

    result = subprocess.run(
        [sys.executable, "-m", "loguru_rich_sink"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "found in sys.modules after import of package" not in result.stderr


def test_rich_sink_ignores_loguru_serialize_environment() -> None:
    """Ensure LOGURU_SERIALIZE does not wrap Rich panel output in JSON."""
    script = textwrap.dedent(
        """
        import io

        from rich.console import Console

        from loguru_rich_sink.sink import get_logger

        console = Console(file=io.StringIO(), record=True, force_terminal=True)
        logger = get_logger(console=console)

        logger.info("json message")

        output = console.export_text()
        assert "json message" in output
        assert '"record"' not in output
        """
    )
    env = _loguru_env(LOGURU_AUTOINIT="False", LOGURU_SERIALIZE="True")

    subprocess.run([sys.executable, "-c", script], check=True, env=env)


def test_unknown_level_falls_back_to_default() -> None:
    """Ensure unknown log levels do not raise exceptions."""
    console = Console(file=io.StringIO())
    sink = RichSink(console=console)
    logger.remove()
    logger.add(sink, format="{message}")
    logger.level("CUSTOM", no=15, color="<yellow>")

    logger.log("CUSTOM", "custom level")
