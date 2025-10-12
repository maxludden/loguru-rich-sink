"""The Rich Sink for the loguru logger."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Message

from rich.color import Color
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text as RichText
from rich.traceback import install as tr_install
from rich_gradient.text import Text


def get_console(record: bool = False, console: Console | None = None) -> Console:
    """Initialize the console and return it.

    Args:
        console (Console, optional): A Rich console. Defaults to Console().

    Returns:
        Console: A Rich console.
    """
    if console is None:
        console = Console(record=True) if record else Console()
    else:
        console.record = bool(record)
    _ = tr_install(console=console)
    return console


FORMAT: str = '{time:HH:mm:ss.SSS} | Run {extra[run]} | {file.name: ^12} | Line {line} | {level} | {message}'
CWD: Path = Path.cwd()
LOGS_DIR: Path = CWD / 'logs'
RUN_FILE: Path = LOGS_DIR / 'run.txt'


def find_cwd(start_dir: Path | None = None, verbose: bool = False) -> Path:
    """Find the current working directory.

    Args:
        start_dir (Path, optional): The starting directory. Defaults to Path.cwd().
        verbose (bool, optional): Print the output of the where command. Defaults to False.

    Returns:
        Path: The current working directory.
    """
    cwd: Path = start_dir if start_dir is not None else Path.cwd()
    while not (cwd / 'pyproject.toml').exists():
        cwd = cwd.parent
        if cwd == Path.home():
            break
    if verbose:
        console = get_console()
        _ = console.line(2)
        gradient_title = Text(
            'Current Working Directory',
            colors=[Color.parse('#ff005f'), Color.parse('#ff00af'), Color.parse('#ff00ff')],
            rainbow=False,
        )
        console.print(
            Panel(
                f'[i #5f00ff]{cwd.resolve()}',
                title=gradient_title,
            )
        )
        _ = console.line(2)
    return cwd


def setup() -> int:
    """Setup the logger and return the run count."""
    console = get_console()
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True)
        console.print(f'Created Logs Directory: {LOGS_DIR}')
    if not RUN_FILE.exists():
        with open(RUN_FILE, 'w', encoding='utf-8') as f:
            _ = f.write('0')
            _ = console.print('Created Run File, Set to 0')

    with open(RUN_FILE, encoding='utf-8') as f:
        return int(f.read())


def read() -> int:
    """Read the run count from the file."""
    if not RUN_FILE.exists():
        console = get_console()
        _ = console.print('[b #ff0000]Run File Not Found[/][i #ff9900], Creating...[/]')
        _ = setup()
    with open(RUN_FILE, encoding='utf-8') as f:
        return int(f.read())


def write(run: int) -> None:
    """Write the run count to the file."""
    with open(RUN_FILE, 'w', encoding='utf-8') as f:
        _ = f.write(str(run))


def increment() -> int:
    """Increment the run count and write it to the file."""
    run = read()
    run += 1
    write(run)
    return run


LEVEL_STYLES: dict[str, Style] = {
    'TRACE': Style(italic=True),
    'DEBUG': Style(color='#aaaaaa'),
    'INFO': Style(color='#00afff'),
    'SUCCESS': Style(bold=True, color='#00ff00'),
    'WARNING': Style(italic=True, color='#ffaf00'),
    'ERROR': Style(bold=True, color='#ff5000'),
    'CRITICAL': Style(bold=True, color='#ff0000'),
}

GRADIENTS: dict[str, list[Color]] = {
    'TRACE': [Color.parse('#888888'), Color.parse('#aaaaaa'), Color.parse('#cccccc')],
    'DEBUG': [Color.parse('#338888'), Color.parse('#55aaaa'), Color.parse('#77cccc')],
    'INFO': [Color.parse('#008fff'), Color.parse('#00afff'), Color.parse('#00cfff')],
    'SUCCESS': [Color.parse('#00aa00'), Color.parse('#00ff00'), Color.parse('#afff00')],
    'WARNING': [Color.parse('#ffaa00'), Color.parse('#ffcc00'), Color.parse('#ffff00')],
    'ERROR': [Color.parse('#ff0000'), Color.parse('#ff5500'), Color.parse('#ff7700')],
    'CRITICAL': [Color.parse('#ff0000'), Color.parse('#ff005f'), Color.parse('#ff00af')],
}


class RichSink:
    """A loguru sink that uses the great `rich` library to print log messages.

    Args:
        run (Optional[int], optional): The current run number. If None, it will \
be read from a file. Defaults to None.
        console (Optional[Console]): A Rich console. If None, it will be \
initialized. Defaults to None.


    """

    def __init__(self, run: int | None = None, console: Console | None = None) -> None:
        if run is None:
            try:
                run = read()
            except FileNotFoundError:
                run = setup()
        self.run: int = run
        self.console: Console = console or get_console()

    def __call__(self, message: "Message") -> None:
        record = message.record
        level = record['level'].name
        colors = GRADIENTS[level]
        style = LEVEL_STYLES[level]

        # title with gradient
        title = Text(f' {level} | {record["file"].name} | Line {record["line"]} ', colors=colors, rainbow=False)

        # subtitle
        subtitle = RichText.assemble(
            RichText(f'Run {self.run}'),
            RichText(' | '),
            RichText(record['time'].strftime('%H:%M:%S.%f')[:-3]),
            RichText(record['time'].strftime(' %p')),
        )
        _ = subtitle.highlight_words(':', style='dim #aaaaaa')

        # Message with gradient
        message_text = Text(record['message'], colors=colors, rainbow=False)
        # Generate and print log panel with aligned title and subtitle
        log_panel: Panel = Panel(
            message_text,
            title=title,
            title_align='left',  # Left align the title
            subtitle=subtitle,
            subtitle_align='right',  # Right align the subtitle
            border_style=style + Style(bold=True),
            padding=(1, 2),
        )
        self.console.print(log_panel)


def rich_sink(message: "Message") -> None:
    """A loguru sink that uses the great `rich` library to print log messages."""
    record = message.record
    level = record['level'].name
    colors = GRADIENTS[level]
    style = LEVEL_STYLES[level]

    # title with gradient
    title = Text(f' {level} | {record["file"].name} | Line {record["line"]} ', colors=colors, rainbow=False)

    # subtitle
    run: int = read()
    subtitle = RichText.assemble(
        RichText(f'Run {run}'),
        RichText(' | '),
        RichText(record['time'].strftime('%H:%M:%S.%f')[:-3]),
        RichText(record['time'].strftime(' %p')),
    )
    _ = subtitle.highlight_words(':', style='dim #aaaaaa')

    # Message with gradient
    message_text = Text(record['message'], colors=colors, rainbow=False)
    # Generate and print log panel with aligned title and subtitle
    log_panel: Panel = Panel(
        message_text,
        title=title,
        title_align='left',  # Left align the title
        subtitle=subtitle,
        subtitle_align='right',  # Right align the subtitle
        border_style=style + Style(bold=True),
        padding=(1, 2),
    )
    console = get_console(True)
    console.print(log_panel)
    record['extra']['rich'] = console.export_text()


if __name__ == '__main__':
    console = get_console()
    console.print('CWD:', find_cwd(verbose=True))
