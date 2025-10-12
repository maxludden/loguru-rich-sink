# loguru-rich-sink

A beautiful, feature-rich sink for [Loguru](https://github.com/Delgan/loguru) that leverages the [Rich](https://github.com/Textualize/rich) library to display stunning, gradient-colored log messages in styled panels.

## Features

✨ **Beautiful Terminal Output** - Log messages displayed in Rich panels with gradient colors  
🎨 **Level-Specific Styling** - Each log level has unique colors and gradients  
📊 **Run Tracking** - Automatic tracking and incrementing of run numbers  
📝 **Dual Logging** - Console output with Rich formatting + file logging  
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
- rich >= 14.2.0
- rich-gradient >= 0.3.4

## Quick Start

```python
from loguru import logger
from loguru_rich_sink import RichSink

# Add the RichSink to your logger
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

logger.add(RichSink(), format="{message}")

logger.trace("Trace message")
logger.debug("Debug message")
logger.info("Info message")
logger.success("Success message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Using the Function-Based Sink

```python
from loguru import logger
from loguru_rich_sink import rich_sink

logger.add(rich_sink, format="{message}")
logger.info("This also works!")
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
logger.add(RichSink(console=console), format="{message}")
```

### Full Logger Setup with Dual Sinks

The package includes a complete logger setup with both console and file logging:

```python
from loguru_rich_sink import get_logger

# This sets up both Rich console output and file logging
logger = get_logger()

logger.info("Logged to both console and file!")
```

This configuration:
- Displays logs in the console using RichSink with beautiful formatting
- Writes detailed logs to `logs/trace.log` with full formatting
- Tracks run numbers automatically
- Enables backtrace and diagnose for better debugging

### Run Tracking

The package automatically tracks how many times your application has been run:

```python
from loguru_rich_sink import read, increment, setup

# Initialize run tracking (creates logs directory and run file)
run = setup()

# Read current run number
current_run = read()
print(f"Current run: {current_run}")

# Increment run number
next_run = increment()
print(f"Next run: {next_run}")
```

Run numbers are displayed in the subtitle of each log panel.

## Log Levels and Styling

Each log level has its own distinct visual style:

| Level    | Colors | Style |
|----------|--------|-------|
| TRACE    | Gray gradient | Italic |
| DEBUG    | Cyan/teal gradient | Default |
| INFO     | Blue gradient | Default |
| SUCCESS  | Green gradient | Bold |
| WARNING  | Yellow/orange gradient | Italic |
| ERROR    | Orange/red gradient | Bold |
| CRITICAL | Red/magenta gradient | Bold |

## API Reference

### RichSink

The main sink class for loguru.

```python
class RichSink:
    def __init__(
        self, 
        run: int | None = None, 
        console: Console | None = None
    ) -> None:
```

**Parameters:**
- `run` (int | None): The current run number. If None, reads from file.
- `console` (Console | None): A Rich Console instance. If None, creates a new one.

**Usage:**
```python
sink = RichSink(run=1, console=my_console)
logger.add(sink, format="{message}")
```

### rich_sink

A function-based alternative to RichSink.

```python
def rich_sink(message: Message) -> None:
```

**Parameters:**
- `message` (Message): The loguru message object.

**Usage:**
```python
logger.add(rich_sink, format="{message}")
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
def get_logger() -> Logger:
```

Get a fully configured logger with both Rich console sink and file sink.

#### setup

```python
def setup() -> int:
```

Initialize the logging directory structure and return the current run number.

#### read

```python
def read() -> int:
```

Read the current run number from the run file.

#### write

```python
def write(run: int) -> None:
```

Write a run number to the run file.

#### increment

```python
def increment() -> int:
```

Increment the run counter and return the new run number.

## Constants

### FORMAT

Default log format string:
```python
FORMAT = '{time:HH:mm:ss.SSS} | Run {extra[run]} | {file.name: ^12} | Line {line} | {level} | {message}'
```

### LEVEL_STYLES

Dictionary mapping log levels to Rich Style objects:
```python
LEVEL_STYLES: dict[str, Style] = {
    'TRACE': Style(italic=True),
    'DEBUG': Style(color='#aaaaaa'),
    'INFO': Style(color='#00afff'),
    'SUCCESS': Style(bold=True, color='#00ff00'),
    'WARNING': Style(italic=True, color='#ffaf00'),
    'ERROR': Style(bold=True, color='#ff5000'),
    'CRITICAL': Style(bold=True, color='#ff0000'),
}
```

### GRADIENTS

Dictionary mapping log levels to color gradients:
```python
GRADIENTS: dict[str, list[Color]] = {
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
LOGS_DIR: Path  # Path to logs directory (defaults to ./logs)
RUN_FILE: Path  # Path to run counter file (defaults to ./logs/run.txt)
```

## Advanced Usage

### Custom Formatting

You can customize the log format while still using RichSink:

```python
from loguru import logger
from loguru_rich_sink import RichSink, FORMAT

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
logger.add(RichSink(), format="{message}", level="INFO")

# Your existing logging code works as-is
logger.info("Now with beautiful Rich formatting!")
```

## Example Output

When you run your application, logs appear as beautifully formatted panels:

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

This will display all log levels with their respective styling.

## File Structure

```
loguru-rich-sink/
├── src/
│   └── loguru_rich_sink/
│       ├── __init__.py      # Package exports
│       ├── __main__.py      # Demo/example usage
│       └── sink.py          # Core implementation
├── logs/                    # Created automatically
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

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run the demo
python -m loguru_rich_sink

# Run with custom console width
python -c "from rich.console import Console; from loguru_rich_sink import RichSink; from loguru import logger; logger.add(RichSink(console=Console(width=80)), format='{message}'); logger.info('Test')"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is open source. Please check the repository for license information.

## Credits

- Built with [Loguru](https://github.com/Delgan/loguru) by [@Delgan](https://github.com/Delgan)
- Styled with [Rich](https://github.com/Textualize/rich) by [@willmcgugan](https://github.com/willmcgugan)
- Uses [rich-gradient](https://github.com/maxludden/rich-gradient) for gradient text

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
- [rich-gradient](https://github.com/maxludden/rich-gradient) - Gradient text for Rich

---

Made with ❤️ and Python
