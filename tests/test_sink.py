"""Tests for the Rich loguru sink behavior."""

from __future__ import annotations

import io
from pathlib import Path

from loguru import logger
from rich.console import Console

from loguru_rich_sink import sink as sink_module
from loguru_rich_sink.sink import RichSink, get_logger


def _configure_run_paths(tmp_path: Path) -> None:
    """Point the sink module to temporary run-tracking paths."""
    sink_module.LOGS_DIR = tmp_path / "logs"
    sink_module.RUN_FILE = sink_module.LOGS_DIR / "run.txt"


def test_run_tracking_persists_and_increments(tmp_path: Path) -> None:
    """Ensure run tracking creates, reads, and increments the run counter."""
    _configure_run_paths(tmp_path)
    console = Console(file=io.StringIO())
    sink = RichSink(track_run=True, console=console)

    assert sink.setup() == 0
    assert sink.read() == 0
    assert sink.increment() == 1
    assert sink.read() == 1


def test_get_logger_increments_run(tmp_path: Path) -> None:
    """Ensure get_logger increments the run counter on initialization."""
    _configure_run_paths(tmp_path)
    console = Console(file=io.StringIO(), record=True, force_terminal=True, width=120)

    logger_instance = get_logger(console=console, track_run=True)
    logger_instance.info("Run initialized")

    assert sink_module.RUN_FILE.read_text(encoding="utf-8") == "1"
    output = console.export_text()
    assert "Run 1" in output
    assert "Run initialized" in output


def test_unknown_level_falls_back_to_default() -> None:
    """Ensure unknown log levels do not raise exceptions."""
    console = Console(file=io.StringIO())
    sink = RichSink(console=console)
    logger.remove()
    logger.add(sink, format="{message}")
    logger.level("CUSTOM", no=15, color="<yellow>")

    logger.log("CUSTOM", "custom level")
