"""A Rich sink for Loguru logger.

This package provides a Rich-based sink for the Loguru logging library,
allowing you to display beautiful, formatted log messages in the terminal.

Example:
    from loguru import logger
    from loguru_rich_sink import RichSink

    logger.add(RichSink(), format="{message}")
    logger.info("Hello, World!")
"""

from loguru_rich_sink.sink import (
    RichSink,
    get_console,
    get_logger,
    get_progress,
)


def main() -> int:
    """Run the package demonstration CLI.

    Returns:
        A process exit code.
    """
    from loguru_rich_sink.__main__ import main as run_demo

    return run_demo()


__version__ = "0.0.5"

__all__ = [
    "RichSink",
    "get_console",
    "get_logger",
    "get_progress",
    "main",
]
