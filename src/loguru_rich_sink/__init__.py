"""Public package API for loguru-rich-sink."""

from rich.console import Console
from rich.traceback import install as tr_install
from rich_color_ext import install as rc_install

from loguru_rich_sink.sink import (
    RichSink,
    get_console,
    get_logger,
    get_progress
)

console: Console = Console()
tr_install(console=console)
rc_install()

__all__ = [
    "RichSink",
    "get_console",
    "get_logger",
    "get_progress"
]
