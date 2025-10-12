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
    FORMAT,
    GRADIENTS,
    LEVEL_STYLES,
    LOGS_DIR,
    RUN_FILE,
    RichSink,
    get_console,
    increment,
    read,
    rich_sink,
    setup,
    write,
)

__version__ = '0.0.3'

__all__ = [
    'FORMAT',
    'GRADIENTS',
    'LEVEL_STYLES',
    'LOGS_DIR',
    'RUN_FILE',
    'RichSink',
    'get_console',
    'increment',
    'read',
    'rich_sink',
    'setup',
    'write',
]
