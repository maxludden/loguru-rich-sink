"""Rich logger setup and usage."""

from __future__ import annotations

import atexit
import sys
from typing import TYPE_CHECKING

from loguru import logger
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.traceback import install as tr_install

from loguru_rich_sink.sink import FORMAT, LOGS_DIR, RichSink, increment, read, setup

if TYPE_CHECKING:
    from loguru import Logger as _Logger


def get_console(console: Console | None = None) -> Console:
    """Initialize the console and return it.

    Args:
        console (Console, optional): A Rich console. Defaults to Console().

    Returns:
        Console: A Rich console.
    """
    if console is None:
        console = Console()
    _ = tr_install(console=console)
    return console


def get_logger() -> _Logger:
    """Initialize the logger with two sinks and return it."""
    run = setup()
    logger.remove()
    _: list[int] = logger.configure(
        handlers=[
            {
                'sink': RichSink(),
                'format': '{message}',
                'level': 'INFO',
                'backtrace': True,
                'diagnose': True,
                'colorize': False,
            },
            {
                'sink': str(LOGS_DIR / 'trace.log'),
                'format': FORMAT,
                'level': 'TRACE',
                'backtrace': True,
                'diagnose': True,
                'colorize': False,
            },
        ],
        extra={'run': run},
    )
    return logger  # type: ignore[return-value]


def get_progress(console: Console | None = None) -> Progress:
    """Initialize the progress bar and return it."""
    if console is None:
        console = get_console()
    progress = Progress(
        SpinnerColumn(spinner_name='earth'),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        MofNCompleteColumn(),
    )
    progress.start()
    return progress


def on_exit() -> None:
    """At exit, read the run number and increment it."""
    try:
        run = read()
        logger.info('Run {} Completed', run)
        run = increment()
    except FileNotFoundError as fnfe:
        logger.exception(fnfe)
        run = setup()
        logger.info('Run {} Completed', run)
    run = increment()


_ = atexit.register(on_exit)

if __name__ == '__main__':
    logger = get_logger()

    logger.info('Started')
    logger.trace('Trace')
    logger.debug('Debug')
    logger.info('Info')
    logger.success('Success')
    logger.warning('Warning')
    logger.error('Error')
    logger.critical('Critical')

    logger.info('Finished')
    sys.exit(0)
