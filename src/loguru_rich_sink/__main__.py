"""Command-line entrypoint for the loguru-rich-sink demo."""

from __future__ import annotations

from loguru_rich_sink.sink import get_console, get_logger


def main() -> int:
    """Run a short demonstration of the Rich Loguru sink.

    Returns:
        A process exit code.
    """
    console = get_console()
    logger = get_logger(console=console)

    logger.info("Started")
    logger.trace("Trace")
    logger.debug("Debug")
    logger.info("Info")
    logger.success("Success")
    logger.warning("Warning")
    logger.error("Error")
    logger.critical("Critical")
    logger.info("Finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
