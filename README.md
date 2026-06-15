# loguru-rich-sink

A beautiful, feature-rich sink for [Loguru](https://github.com/Delgan/loguru) that leverages the [Rich](https://github.com/Textualize/rich) library to display stunning, gradient-colored log messages in styled panels.

## Features

✨ **Beautiful Terminal Output** - Log messages displayed in Rich panels with gradient colors  
🎨 **Level-Specific Styling** - Each log level has unique colors and gradients  
📊 **Run Tracking** - Optional tracking and incrementing of run numbers  
📝 **Trace File Logging** - Write detailed trace logs when run tracking is enabled  
🔧 **Highly Customizable** - Configure console, styles, and log formats  
🐍 **Type-Safe** - Full type hints for better IDE support  
⚡ **Easy Integration** - Drop-in replacement for standard loguru sinks

## Installation

```bash
pip install loguru-rich-sink
```

Or with `uv`:

```bash
uv add loguru-rich-sink
```

## Requirements

- Python >= 3.13
- loguru >= 0.7.3
- rich >= 15.0.0

## Quick Start

```python
from loguru import logger
from loguru_rich_sink import RichSink

# Add the RichSink to your logger
logger.remove()
logger.add(RichSink(), format="{message}")

# Start logging with beautiful output!
logger.info("Hello, World!")
logger.success("Operation completed successfully!")
logger.warning("This is a warning message")
logger.error("An error occurred")
```

## Usage

### Basic Usage

The simplest way to use loguru-rich-sink:

```python
from loguru import logger
from loguru_rich_sink import RichSink

logger.remove()
logger.add(RichSink(), format="{message}")

logger.trace("Trace message")
logger.debug("Debug message")
logger.info("Info message")
logger.success("Success message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Custom Console

Pass your own Rich console for more control:

```python
from rich.console import Console
from loguru import logger
from loguru_rich_sink import RichSink

# Create a custom console
console = Console(width=120, force_terminal=True)

# Use it with RichSink
logger.remove()
logger.add(RichSink(console=console), format="{message}")
```

### Logger Helper

The package includes a helper that removes Loguru's default handlers and configures a RichSink console handler:

```python
from loguru_rich_sink import get_logger

logger = get_logger()

logger.info("Logged with Rich formatting!")
```

This configuration:
- Displays logs in the console using RichSink with beautiful formatting
- Enables backtrace and diagnose for better debugging

Pass `track_run=True` to also persist a run counter and write detailed trace logs to `logs/trace.log`:

```python
from loguru_rich_sink import get_logger

logger = get_logger(track_run=True)

logger.info("Logged to the console and trace file!")
```

### Run Tracking

Run tracking is available through `RichSink` methods:

```python
from loguru_rich_sink import RichSink

sink = RichSink(track_run=True)

# Initialize run tracking storage (creates logs directory and run file)
current_run = sink.setup()
print(f"Current run: {current_run}")

# Increment run number
next_run = sink.increment()
print(f"Next run: {next_run}")
```

When `track_run=True`, run numbers are displayed in the subtitle of each log panel.

## Log Levels and Styling

Each log level has its own distinct visual style:

| Level    | Colors | Style |
|----------|--------|-------|
| TRACE    | Gray gradient | Dim |
| DEBUG    | Cyan/teal gradient | Default |
| INFO     | Blue gradient | Default |
| SUCCESS  | Green gradient | Bold |
| WARNING  | Yellow/orange gradient | Bold |
| ERROR    | Orange/red gradient | Bold |
| CRITICAL | Red/magenta gradient | Bold |

## API Reference

### RichSink

The main sink class for loguru.

```python
class RichSink:
    def __init__(
        self,
        track_run: bool = False,
        run: int | None = None, 
        console: Console | None = None
    ) -> None:
```

**Parameters:**
- `track_run` (bool): Whether to track and persist the run count.
- `run` (int | None): Optional initial run number.
- `console` (Console | None): A Rich Console instance. If None, creates a new one.

**Usage:**
```python
sink = RichSink(run=1, console=my_console)
logger.add(sink, format="{message}")
```

### Helper Functions

#### get_console

```python
def get_console(
    record: bool = False, 
    console: Console | None = None
) -> Console:
```

Initialize and return a Rich console with traceback support.

#### get_logger

```python
def get_logger(
    console: Console | None = None,
    track_run: bool = False,
    handlers: Sequence[dict[str, Any]] | dict[str, Any] | None = None,
) -> Logger:
```

Get a configured Loguru logger with a Rich console sink. When `track_run=True`, it also increments the run counter and adds `logs/trace.log` as a trace-level file sink.

#### get_progress

```python
def get_progress(console: Console | None = None) -> Progress:
```

Return a Rich progress bar configured to match the logger output.

#### find_cwd

```python
def find_cwd(start_dir: Path | None = None, verbose: bool = False) -> Path:
```

Walk upward from `start_dir` or the current working directory until a `pyproject.toml` is found. If none is found, the search stops at the filesystem root.

## Constants

### LEVEL_STYLES

`RichSink.LEVEL_STYLES` maps log levels to Rich Style objects:
```python
LEVEL_STYLES: dict[str, Style] = {
    'TRACE': Style(dim=True),
    'DEBUG': Style(color='#aaaaaa'),
    'INFO': Style(color='#00afff'),
    'SUCCESS': Style(bold=True, color='#00ff00'),
    'WARNING': Style(bold=True, color='#ffaf00'),
    'ERROR': Style(bold=True, color='#ff5000'),
    'CRITICAL': Style(color='#ffffff', bgcolor='#ff0000', bold=True),
}
```

### GRADIENTS

`RichSink.GRADIENTS` maps log levels to color gradients:
```python
GRADIENTS: dict[str, list[str]] = {
    'TRACE': [...],    # Gray gradient
    'DEBUG': [...],    # Cyan gradient
    'INFO': [...],     # Blue gradient
    'SUCCESS': [...],  # Green gradient
    'WARNING': [...],  # Yellow gradient
    'ERROR': [...],    # Orange-red gradient
    'CRITICAL': [...], # Red-magenta gradient
}
```

### Paths

```python
LOGS_DIR: Path  # Path to logs directory
RUN_FILE: Path  # Path to run counter file
```

## Advanced Usage

### Custom Formatting

You can customize the log format while still using RichSink:

```python
from loguru import logger
from loguru_rich_sink import RichSink

logger.remove()
logger.add(
    RichSink(),
    format="{message}",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
)
```

### Multiple Sinks

Combine RichSink with other sinks:

```python
from loguru import logger
from loguru_rich_sink import RichSink

# Remove default handler
logger.remove()

# Add Rich console sink
logger.add(RichSink(), format="{message}", level="INFO")

# Add file sink for detailed logs
logger.add(
    "logs/app.log",
    format="{time} | {level} | {message}",
    level="TRACE",
    rotation="10 MB",
)

# Add JSON sink for structured logging
logger.add(
    "logs/app.json",
    format="{message}",
    level="INFO",
    serialize=True,
)
```

### Integration with Existing Projects

If you have an existing project using loguru:

```python
from loguru import logger
from loguru_rich_sink import RichSink

# Keep your existing sinks and add Rich output
# Omit remove() here if you intentionally want to keep existing handlers.
logger.remove()
logger.add(RichSink(), format="{message}", level="INFO")

# Your existing logging code works as-is
logger.info("Now with beautiful Rich formatting!")
```

## Example Output

When run tracking is enabled, logs appear as beautifully formatted panels with the run number in the subtitle:

```
┌─ INFO | app.py | Line 42 ──────────────────────────────────────┬─ Run 1 | 14:23:45.123 PM ─┐
│                                                                  │                           │
│  Application started successfully                                │                           │
│                                                                  │                           │
└──────────────────────────────────────────────────────────────────┴───────────────────────────┘
```

Each log level uses distinct gradient colors and styling to make logs easy to scan and understand.

## Running the Demo

To see loguru-rich-sink in action:

```bash
python -m loguru_rich_sink
```

This displays the INFO, SUCCESS, WARNING, ERROR, and CRITICAL demo messages with their respective styling. TRACE and DEBUG records are filtered by the demo's INFO-level console handler.

## File Structure

```
loguru-rich-sink/
├── src/
│   └── loguru_rich_sink/
│       ├── __init__.py      # Package exports
│       ├── __main__.py      # Demo/example usage
│       └── sink.py          # Core implementation
├── logs/                    # Created automatically when run tracking is enabled
│   ├── run.txt             # Run counter
│   └── trace.log           # Log file
├── pyproject.toml          # Project metadata
└── README.md               # This file
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/maxludden/loguru-rich-sink.git
cd loguru-rich-sink

# Install with uv (recommended)
uv sync

# Or install the package in editable mode
pip install -e .
```

### Running Tests

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is open source. Please check the repository for license information.

## Credits

- Built with [Loguru](https://github.com/Delgan/loguru) by [@Delgan](https://github.com/Delgan)
- Styled with [Rich](https://github.com/Textualize/rich) by [@willmcgugan](https://github.com/willmcgugan)

## Author

**Max Ludden**  
Email: dev@maxludden.com  
GitHub: [@maxludden](https://github.com/maxludden)

## Changelog

### v0.0.4
- Current version
- Full Python 3.13 support
- Improved type hints
- Enhanced documentation

### v0.0.3
- Initial release
- Core RichSink functionality
- Run tracking
- Dual sink setup

## Related Projects

- [loguru](https://github.com/Delgan/loguru) - Python logging made (stupidly) simple
- [rich](https://github.com/Textualize/rich) - Rich text and beautiful formatting in the terminal

---

Made with ❤️ and Python
