"""A Rich sink for Loguru logger.

This package provides a Rich-based sink for the Loguru logging library,
allowing you to display beautiful, formatted log messages in the terminal.

Example:
    from loguru import logger
    from loguru_rich_sink import RichSink

    logger.add(RichSink(), format="{message}")
    logger.info("Hello, World!")
"""

from rich.console import Console
from rich.traceback import install as tr_install
from rich_color_ext import install as rc_install

from loguru_rich_sink.__main__ import main
from loguru_rich_sink.sink import (
    RichSink,
    get_console,
    get_logger,
    get_progress,
)

console: Console = Console()
tr_install(console=console)
rc_install()

__version__ = "0.0.4"

__all__ = [
    "RichSink",
    "get_console",
    "get_logger",
    "get_progress",
    "main",
]
