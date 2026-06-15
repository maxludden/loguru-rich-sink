"""Local script for manually previewing RichSink output."""

from loguru import logger

from loguru_rich_sink import RichSink

# Add the RichSink to your logger
logger.remove()
logger.add(RichSink(), format="{message}")

# Start logging with beautiful output!
logger.trace("This is a trace message")
logger.debug("This is a debug message")
logger.info("Hello, World!")
logger.success("Operation completed successfully!")
logger.warning("This is a warning message")
logger.error("An error occurred")
