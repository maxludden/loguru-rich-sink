"""Rich sink implementation for Loguru with optional run tracking."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias, cast

import loguru
from rich.color import Color
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
from rich.style import Style, StyleType
from rich.text import Text as RichText
from rich.traceback import install as tr_install

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
LOGURU_HANDLER_ENV_PARAMS: tuple[str, ...] = (
    "level",
    "format",
    "filter",
    "colorize",
    "backtrace",
    "diagnose",
    "enqueue",
    "catch",
)


def _respect_loguru_environment(handler: HandlerConfig) -> HandlerConfig:
    """Remove explicit handler defaults when Loguru environment vars are set.

    Args:
        handler: Handler configuration passed to ``logger.configure()``.

    Returns:
        The handler configuration with environment-controlled values omitted.
    """
    for param in LOGURU_HANDLER_ENV_PARAMS:
        if f"LOGURU_{param.upper()}" in os.environ:
            handler.pop(param, None)
    return handler


def _interpolate_hex_color(start: str, end: str, position: float) -> str:
    """Return an interpolated hex color between two Rich color strings.

    Args:
        start: Starting color string parseable by Rich.
        end: Ending color string parseable by Rich.
        position: Interpolation position from 0.0 to 1.0.

    Returns:
        A hex color string for the interpolated position.
    """
    start_triplet = Color.parse(start).get_truecolor()
    end_triplet = Color.parse(end).get_truecolor()
    red = round(start_triplet.red + (end_triplet.red - start_triplet.red) * position)
    green = round(
        start_triplet.green + (end_triplet.green - start_triplet.green) * position
    )
    blue = round(
        start_triplet.blue + (end_triplet.blue - start_triplet.blue) * position
    )
    return f"#{red:02x}{green:02x}{blue:02x}"


def _gradient_text(
    text: object, colors: Sequence[str], style: StyleType = ""
) -> RichText:
    """Return Rich text with a per-character color gradient.

    Args:
        text: Text or markup content to render.
        colors: Color stops used for the gradient.
        style: Base Rich style applied under the gradient colors.

    Returns:
        Rich text with interpolated foreground colors.
    """
    rich_text = RichText(str(text), style=style)
    if not rich_text.plain or not colors:
        return rich_text
    if len(colors) == 1:
        rich_text.stylize(Style(color=colors[0]))
        return rich_text

    last_index = max(len(rich_text.plain) - 1, 1)
    segment_count = len(colors) - 1
    for index in range(len(rich_text.plain)):
        scaled_position = (index / last_index) * segment_count
        segment_index = min(int(scaled_position), segment_count - 1)
        segment_position = scaled_position - segment_index
        color = _interpolate_hex_color(
            colors[segment_index],
            colors[segment_index + 1],
            segment_position,
        )
        rich_text.stylize(Style(color=color), index, index + 1)
    return rich_text


def get_console(record: bool = False, console: Console | None = None) -> Console:
    """Return a Rich console with rich tracebacks enabled.

    Args:
        record: Whether to enable recording for console export.
        console: Optional existing Rich console to configure.

    Returns:
        A Rich console configured for this sink.
    """
    if console is None:
        console = Console(record=record)
    else:
        console.record = record
    tr_install(console=console)
    return console


def find_cwd(start_dir: Path | None = None, verbose: bool = False) -> Path:
    """Find the project root by walking up to a pyproject.toml.

    Args:
        start_dir: Optional directory to begin the search from.
        verbose: Whether to print the resolved working directory panel.

    Returns:
        The resolved project root directory.
    """
    cwd = start_dir if start_dir is not None else Path.cwd()
    while not (cwd / "pyproject.toml").exists():
        parent = cwd.parent
        if parent == cwd:
            break
        cwd = parent
    if verbose:
        console = get_console()
        console.line(2)
        console.print(
            Panel(
                f"[i #5f00ff]{cwd.resolve()}",
                title=_gradient_text(
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
    DEFAULT_LEVEL: str = "INFO"
    ANSI_TRACEBACK_LEVELS: frozenset[str] = frozenset(
        {"WARNING", "ERROR", "CRITICAL"}
    )

    GRADIENTS: dict[str, list[str]] = {
        "TRACE": ["#888888", "#aaaaaa", "#cccccc"],
        "DEBUG": ["#338888", "#55aaaa", "#77cccc"],
        "INFO": ["#008fff", "#00afff", "#00cfff"],
        "SUCCESS": ["#00aa00", "#00ff00", "#afff00"],
        "WARNING": ["#ffaa00", "#ffcc00", "#ffff00"],
        "ERROR": ["#FF7700", "#ff5500", "#ff0000"],
        "CRITICAL": ["#ff0000", "#ff005f", "#ff00af"],
    }

    def __init__(
        self,
        track_run: bool = False,
        run: int | None = None,
        console: Console | None = None,
    ) -> None:
        """Initialize a Rich sink for Loguru logging.

        Args:
            track_run: Whether to track and persist the run count.
            run: Optional initial run number.
            console: Optional Rich console to render to.
        """
        self.console = console or get_console()
        self.run: int | None = run
        self.track_run = track_run
        if self.track_run:
            if run is None:
                try:
                    run = self.read()
                except FileNotFoundError:
                    run = self.setup()
            self.run = run

    @property
    def track_run(self) -> bool:
        """Whether this sink tracks a persistent run count."""
        return bool(getattr(self, "_track_run", False))

    @track_run.setter
    def track_run(self, value: bool) -> None:
        """Enable or disable run count tracking."""
        if not isinstance(value, bool):
            raise TypeError(f"track_run must be bool, got {type(value).__name__}")
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
        colors = self.GRADIENTS.get(level, self.GRADIENTS[self.DEFAULT_LEVEL])
        style = self.LEVEL_STYLES.get(level, self.LEVEL_STYLES[self.DEFAULT_LEVEL])
        function = record.get("function")
        function_part = f":{function}" if function and function != "<module>" else ""
        location = f"{record['file'].name}{function_part}:{record['line']}"

        title: RichText = _gradient_text(
            f" {record['level'].icon} {level} {record['level'].icon} | {location} ",
            colors=colors,
        )
        title.stylize(Style(reverse=True))

        subtitle_lines: list[RichText] = []
        if self.track_run:
            run = self.run
            if run is None:
                run = self.read()
                if run is None:
                    run = self.setup()
            if run is not None:
                self.run = run
                record["extra"]["run"] = run
                subtitle_lines.extend([RichText(f"Run {run}"), RichText(" | ")])
        subtitle_lines.extend(
            [
                RichText(record["time"].strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]), # "%Y/%m/%d %H:%M:%S.%f" --- IGNORE ---
                RichText(record["time"].strftime(" %p")),
            ]
        )

        subtitle: RichText = RichText.assemble(*subtitle_lines)
        subtitle.highlight_words(":", style="dim #aaaaaa")

        raw_message = str(message).rstrip("\n")
        if level in self.ANSI_TRACEBACK_LEVELS and record["exception"] is not None:
            message_text = RichText.from_ansi(raw_message)
        else:
            message_text = _gradient_text(raw_message, colors, style="bold")
        log_panel: Panel = Panel(
            message_text,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="right",
            border_style=style + Style(bold=True),
            padding=(1, 2),
        )

        self.console.print(log_panel)
        if self.console.record:
            record["extra"]["rich"] = self.console.export_text(clear=False)

    def setup(self) -> int | None:
        """Initialize run tracking storage and return the current run count.

        Returns:
            The current run count when tracking is enabled, otherwise None.
        """
        if not self.track_run:
            return None
        if not LOGS_DIR.exists():
            LOGS_DIR.mkdir(parents=True)
            self.console.print(f"Created Logs Directory: {LOGS_DIR}")
        if not RUN_FILE.exists():
            with open(RUN_FILE, "w", encoding="utf-8") as f:
                f.write("0")
                self.console.print("Created Run File, Set to 0")

        with open(RUN_FILE, "r", encoding="utf-8") as f:
            return int(f.read())

    def read(self) -> int | None:
        """Read the current run count from disk.

        Returns:
            The persisted run count when tracking is enabled, otherwise None.
        """
        if not self.track_run:
            return None
        if not RUN_FILE.exists():
            self.console.print(
                "[b #ff0000]Run File Not Found[/][i #ff9900], Creating...[/]"
            )
            self.setup()
        with open(RUN_FILE, "r", encoding="utf-8") as f:
            return int(f.read())

    def write_run(self, run: int) -> None:
        """Persist the run count to disk."""
        if not self.track_run:
            return
        with open(RUN_FILE, "w", encoding="utf-8") as f:
            f.write(str(run))

    def increment(self) -> int | None:
        """Increment the run count and persist it."""
        if not self.track_run:
            return None
        run = self.read()
        if run is None:
            return None
        run += 1
        self.write_run(run)
        return run


run_sink: RichSink | None = None


def get_logger(
    console: Console | None = None,
    track_run: bool = False,
    handlers: Sequence[HandlerConfig] | HandlerConfig | None = None,
) -> Logger:
    """Return a configured Loguru logger with a Rich sink.

    Args:
        console: Optional Rich console to use for rendering.
        track_run: Whether to track run counts and emit trace logs.
        handlers: Optional handler config(s) appended after the defaults.

    Returns:
        A configured Loguru logger instance with run tracking incremented.
    """
    if console is None:
        console = get_console()
    sink = RichSink(console=console, track_run=track_run)
    run: int | None = None
    if track_run:
        run = sink.read()
        if run is None:
            run = sink.setup()
        if run is not None:
            run += 1
            sink.write_run(run)
            sink.run = run
    default_handlers: list[HandlerConfig] = [
        _respect_loguru_environment(
            {
                "sink": sink,
                "format": "{message}",
                "level": "INFO",
                "backtrace": True,
                "diagnose": True,
                "colorize": True,
                "serialize": False,
            }
        )
    ]
    if track_run:
        _format: str = (
            "{time:HH:mm:ss.SSS} | Run {extra[run]} | {file.name: ^12} | Line {line} \
| {level} | {message}"
        )
        default_handlers.append(
            _respect_loguru_environment(
                {
                    "sink": str(LOGS_DIR / "trace.log"),
                    "format": _format,
                    "level": "TRACE",
                    "backtrace": True,
                    "diagnose": True,
                    "colorize": False,
                }
            )
        )
    if handlers:
        if isinstance(handlers, dict):
            default_handlers.append(cast(HandlerConfig, handlers))
        else:
            default_handlers.extend(handlers)
    global run_sink
    run_sink = sink
    logger.remove()
    logger.configure(
        handlers=cast(Any, default_handlers),
        extra={"run": run},
    )
    return logger


def get_progress(console: Console | None = None) -> Progress:
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
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        MofNCompleteColumn(),
        transient=True,
        expand=True,
        console=console,
    )
    return progress


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
