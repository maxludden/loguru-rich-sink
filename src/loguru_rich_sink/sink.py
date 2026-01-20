"""Rich sink implementation for Loguru with optional run tracking."""

from __future__ import annotations

# import atexit
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypeAlias

import loguru
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.style import Style
from rich.text import Text as RichText
from rich.traceback import install as tr_install
from rich_gradient import Text

if TYPE_CHECKING:
    from loguru import Logger as Logger1
    from loguru import Message, logger
    from loguru._logger import Logger as Logger2

    Logger: TypeAlias = Logger1 | Logger2
    HandlerConfig: TypeAlias = dict[str, Any]
else:
    logger = loguru.logger


CWD: Path = Path.cwd()
LOGS_DIR: Path = CWD / "logs"
RUN_FILE: Path = LOGS_DIR / "run.txt"


def get_console(record: bool = False, console: Optional[Console] = None) -> Console:
    """Return a Rich console with rich tracebacks enabled.

    Args:
        record: Whether to enable recording for console export.
        console: Optional existing Rich console to configure.

    Returns:
        A Rich console configured for this sink.
    """
    if console is None:
        if record:
            console = Console(record=True)
        else:
            console = Console()
    else:
        console.record = True if record else False
    tr_install(console=console)
    return console


def find_cwd(start_dir: Path = Path.cwd(), verbose: bool = False) -> Path:
    """Find the project root by walking up to a pyproject.toml.

    Args:
        start_dir: Directory to begin the search from.
        verbose: Whether to print the resolved working directory panel.

    Returns:
        The resolved project root directory.
    """
    cwd: Path = start_dir
    while not (cwd / "pyproject.toml").exists():
        cwd = cwd.parent
        if cwd == Path.home():
            break
    if verbose:
        console = get_console()
        console.line(2)
        console.print(
            Panel(
                f"[i #5f00ff]{cwd.resolve()}",
                title=Text(
                    "Current Working Directory",
                    colors=[
                        "#ff005f",
                        "#ff00af",
                        "#ff00ff",
                    ],
                    style="bold",
                ),
            )
        )
        console.line(2)
    return cwd


class RichSink:
    """Loguru sink that renders log entries with Rich.

    Args:
        track_run: Whether to track and persist run counts.
        run: Optional run number to seed the tracker.
        console: Rich console to render log panels to.
    """

    LEVEL_STYLES: dict[str, Style] = {
        "TRACE": Style(dim=True),
        "DEBUG": Style(color="#aaaaaa"),
        "INFO": Style(color="#00afff"),
        "SUCCESS": Style(bold=True, color="#00ff00"),
        "WARNING": Style(bold=True, color="#ffaf00"),
        "ERROR": Style(bold=True, color="#ff5000"),
        "CRITICAL": Style(color="#ffffff", bgcolor="#ff0000", bold=True),
    }

    GRADIENTS: dict[str, list[str]] = {
        "TRACE": ["#888888", "#aaaaaa", "#cccccc"],
        "DEBUG": ["#338888", "#55aaaa", "#77cccc"],
        "INFO": ["#008fff", "#00afff", "#00cfff"],
        "SUCCESS": ["#00aa00", "#00ff00", "#afff00"],
        "WARNING": ["#ffaa00", "#ffcc00", "#ffff00"],
        "ERROR": ["#ff0000", "#ff5500", "#ff7700"],
        "CRITICAL": ["#ff0000", "#ff005f", "#ff00af"],
    }

    def __init__(
        self,
        track_run: bool = False,
        run: Optional[int] = None,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize a Rich sink for Loguru logging.

        Args:
            track_run: Whether to track and persist the run count.
            run: Optional initial run number.
            console: Optional Rich console to render to.
        """
        self.run: Optional[int] = run
        self.track_run = track_run
        if self.track_run:
            if run is None:
                try:
                    run = self.read()
                except FileNotFoundError:
                    run = self.setup()
            self.run = run
        self.console = console or get_console()

    @property
    def track_run(self) -> bool:
        """Whether this sink tracks a persistent run count."""
        return bool(getattr(self, "_track_run", False))

    @track_run.setter
    def track_run(self, value: bool) -> None:
        """Enable or disable run count tracking."""
        if not isinstance(value, bool):
            raise NotImplementedError(f"Invalid track_run value: {type(value)}")
        self._track_run = value

    @property
    def format(self) -> str:
        """Return the Loguru format string for this sink."""
        if self.track_run:
            return "{time:HH:mm:ss.SSS} | Run {extra[run]} | {file.name: ^12} \
| Line {line} | {level} | {message}"
        return (
            "{time:HH:mm:ss.SSS} | {file.name: ^12} | Line {line} | {level} | {message}"
        )

    def __call__(self, message: Message) -> None:
        """Render a Loguru message as a Rich panel."""
        record = message.record
        level = record["level"].name
        colors = self.GRADIENTS[level]
        style = self.LEVEL_STYLES[level]

        # title
        title: Text = Text(
            f" {level} | {record['file'].name} | Line {record['line']} ", colors=colors
        )
        title.highlight_words("|", style="italic #666666")
        title.stylize(Style(reverse=True))

        # subtitle
        subtitle_lines: list[Text] = []
        if self.track_run:
            run = self.read()
            if run is None:
                run = self.setup()
            if run is not None:
                self.run = run
                subtitle_lines.extend([Text(f"Run {run}"), Text(" | ")])
        subtitle_lines.extend([
            Text(record["time"].strftime("%H:%M:%S.%f")[:-3]),
            Text(record["time"].strftime(" %p")),
        ])

        subtitle: RichText = RichText.assemble(*subtitle_lines)
        subtitle.highlight_words(":", style="dim #aaaaaa")

        # Message
        message_text: Text = Text(record["message"], colors, style="bold")
        # Generate and print log panel with aligned title and subtitle
        log_panel: Panel = Panel(
            message_text,
            title=title,
            title_align="left",  # Left align the title
            subtitle=subtitle,
            subtitle_align="right",  # Right align the subtitle
            border_style=style + Style(bold=True),
            padding=(1, 2),
        )

        self.console.print(log_panel)
        if self.console.record:
            record["extra"]["rich"] = self.console.export_text()

    def setup(self) -> int | None:
        """Initialize run tracking storage and return the current run count.

        Returns:
            The current run count when tracking is enabled, otherwise None.
        """

        if self.track_run:
            if not LOGS_DIR.exists():
                LOGS_DIR.mkdir(parents=True)
                self.console.print(f"Created Logs Directory: {LOGS_DIR}")
            if not RUN_FILE.exists():
                with open(RUN_FILE, "w", encoding="utf-8") as f:
                    f.write("0")
                    self.console.print("Created Run File, Set to 0")

            with open(RUN_FILE, "r", encoding="utf-8") as f:
                run = int(f.read())
                return run
        return None

    def read(self) -> int | None:
        """Read the current run count from disk.

        Returns:
            The persisted run count when tracking is enabled, otherwise None.
        """
        if self.track_run:
            if not RUN_FILE.exists():
                self.console.print(
                    "[b #ff0000]Run File Not Found[/][i #ff9900], Creating...[/]"
                )
                self.setup()
            with open(RUN_FILE, "r", encoding="utf-8") as f:
                run = int(f.read())
            return run
        return None

    def write(self, run: int) -> None:
        """Persist the run count to disk."""
        if self.track_run:
            with open(RUN_FILE, "w", encoding="utf-8") as f:
                f.write(str(run))

    def increment(self) -> int | None:
        """Increment the run count and persist it."""
        if self.track_run:
            run = self.read()
            if run is None:
                return None
            run += 1
            self.write(run)
            return run
        return None


def get_logger(
    console: Optional[Console] = None,
    track_run: bool = False,
    handlers: Sequence[HandlerConfig] | HandlerConfig | None = None,
) -> Logger:
    """Return a configured Loguru logger with a Rich sink.

    Args:
        console: Optional Rich console to use for rendering.
        track_run: Whether to track run counts and emit trace logs.
        handlers: Optional handler config(s) appended after the defaults.

    Returns:
        A configured Loguru logger instance.
    """
    if console is None:
        console = get_console()
    # active_logger = logger if logger is not None else loguru_logger
    sink = RichSink(console=console, track_run=track_run)
    run = sink.setup() if track_run else None
    default_handlers: list[HandlerConfig] = [
        {
            "sink": sink,
            "format": "{message}",
            "level": "INFO",
            "backtrace": True,
            "diagnose": True,
            "colorize": False,
        }
    ]
    if track_run:
        _format: str = (
            "{time:HH:mm:ss.SSS} | Run {extra[run]} | {file.name: ^12} | Line {line} \
| {level} | {message}"
        )
        default_handlers.append({
            "sink": str(LOGS_DIR / "trace.log"),
            "format": _format,
            "level": "TRACE",
            "backtrace": True,
            "diagnose": True,
            "colorize": False,
        })
    if handlers:
        if isinstance(handlers, dict):
            default_handlers.append(handlers)
        else:
            default_handlers.extend(handlers)
    global run_sink  # pylint: disable=W0601 global-statement
    run_sink = sink
    logger.remove()
    logger.configure(
        handlers=default_handlers,
        extra={"run": run},
    )
    return logger


def get_progress(console: Optional[Console] = None) -> Progress:
    """Return a Rich progress bar configured to match the logger output.

    Args:
        console: Optional Rich console to attach to the progress instance.

    Returns:
        A configured Rich Progress instance.
    """
    if console is None:
        console = get_console()
    progress = Progress(
        SpinnerColumn(spinner_name="point"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        MofNCompleteColumn(),
        transient=True,
        expand=True,
    )
    return progress


# def on_exit() -> None:
#     """Finalize the run tracking state on interpreter exit."""
#     if run_sink is None or not run_sink.track_run:
#         return
#     try:
#         run = run_sink.read()
#         logger.info(f"Run {run} Completed")
#     except FileNotFoundError as fnfe:
#         logger.error(fnfe)
#         run = run_sink.setup()
#         logger.info(f"Run {run} Completed")
#     run_sink.increment()


# atexit.register(on_exit)


if __name__ == "__main__":

    _console = get_console()
    rich_sink = RichSink(console=_console)

    log = get_logger(console=_console)

    log.trace("This is a loguru.Message logged at the [b]TRACE[/] level...")
    log.debug("This is a loguru.Message logged at the [b]DEBUG[/] level...")
    log.info("This is a loguru.Message logged at the [b]INFO[/] level...")
    log.success("This is a loguru.Message logged at the [b]SUCCESS[/] level...")
    log.warning("This is a loguru.Message logged at the [b]WARNING[/] level...")
    log.error("This is a loguru.Message logged at the [b]ERROR[/] level...")
    log.critical("This is a loguru.Message logged at the [b]CRITICAL[/] level...")
    log.exception("This is a loguru.Message logged with an exception...")
