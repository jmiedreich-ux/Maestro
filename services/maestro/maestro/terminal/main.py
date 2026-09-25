"""Minimal connected terminal entry point and offline command boundary."""

from __future__ import annotations

import codecs
import os
import select
import signal
import sys
import termios
import threading
import tty
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from shutil import get_terminal_size
from typing import TextIO

from .connection import (
    ConnectionState,
    ConnectionStatus,
    ServiceError,
    TerminalConnection,
    TerminalConnectionError,
)
from .extensions import ExtensionRegistry
from .architecture import ArchitectureExtension
from .execution import ExecutionExtension
from .registration import RegistrationExtension
from .questions import QuestionsExtension
from .rendering import TerminalRenderer, TerminalSize
from .workspace import View, Workspace, WorkspaceError


HELP_TOPICS = {
    "help": (
        "/help [command]",
        "List the commands, or show the syntax of one. Works without the service.",
        "/help projects",
        "No project context needed.",
    ),
    "projects": (
        "/projects",
        "Open the project overview; choose a project with the arrow keys and Enter.",
        "/projects",
        "No project context needed; needs a connected service.",
    ),
    "attention": (
        "/attention",
        "List questions and actions that need you, across all projects.",
        "/attention",
        "No project context needed; needs a connected service.",
    ),
    "findings": (
        "/findings",
        "List findings of the selected activity. Viewing changes nothing.",
        "/findings",
        "Needs a selected project activity.",
    ),
    "retry": (
        "/retry",
        "Reread connection settings and reconnect now; repeats no earlier command or answer.",
        "/retry",
        "No project context needed.",
    ),
    "exit": (
        "/exit",
        "Leave the terminal; service work and saved records continue. Unsent text asks you to repeat /exit.",
        "/exit",
        "No project context needed.",
    ),
}
OFFLINE_HELP = (
    "Available commands:\n"
    + "".join(f"  /{name:<10}{topic[1]}\n" for name, topic in HELP_TOPICS.items())
    + "Keys: Tab and Shift+Tab move focus, Up and Down move in a list, Enter activates, "
    "Escape closes details. Type /help <command> for syntax.\n"
)


def help_text(argument: str) -> str:
    name = argument.strip().lstrip("/").casefold()
    if not name:
        return OFFLINE_HELP
    topic = HELP_TOPICS.get(name)
    if topic is None:
        return f"No command named /{name}. Type /help for the commands.\n"
    syntax, explanation, example, context = topic
    return f"{syntax}\n  {explanation}\n  Example: {example}\n  Context: {context}\n"


class TerminalApplication:
    """Keep local commands available when the service cannot be reached."""

    def __init__(
        self,
        connection: TerminalConnection,
        *,
        input_stream: TextIO,
        output_stream: TextIO,
    ) -> None:
        self.connection = connection
        self.input = input_stream
        self.output = output_stream
        extensions = ExtensionRegistry()
        QuestionsExtension().install(extensions)
        architecture = ArchitectureExtension()
        architecture.install(extensions)
        execution = ExecutionExtension()
        execution.install(extensions)
        RegistrationExtension(architecture=architecture, execution=execution).install(extensions)
        self.workspace = Workspace(self.connection.client, extensions=extensions)
        self.renderer = TerminalRenderer(
            color=getattr(output_stream, "isatty", lambda: False)()
            and "NO_COLOR" not in os.environ
        )
        self._lock = threading.RLock()
        self._stopping = threading.Event()
        self._resized = threading.Event()
        self._event_generation = 0
        self._explicit_connect = False
        self._exit_warning_text: str | None = None
        self._cursor_at_prompt = False
        self._lines_below_prompt = 0
        self.connection.subscribe(self._handle_status)

    def run(self) -> int:
        configuration = self.connection.configuration
        if configuration.fallback_reason:
            self._write(
                f"Configuration fallback: {configuration.fallback_reason}; "
                f"using {configuration.service_url}"
            )
        credential_status = self.connection.credential_status()
        if credential_status != "Owner credential ready":
            self._write(f"Authentication: {credential_status}")
        try:
            self._explicit_connect = True
            self.connection.connect()
            self._activate_workspace()
        except TerminalConnectionError:
            self._write(
                "Retry connection with /retry. Local /help and /exit remain available."
            )
            self._render()
        finally:
            self._explicit_connect = False

        try:
            command_candidate: str | None = ""
            bracketed_paste = all(
                getattr(stream, "isatty", lambda: False)()
                for stream in (self.input, self.output)
            )
            if bracketed_paste:
                self.output.write("\x1b[?2004h")
                self.output.flush()
            previous_winch = None
            if bracketed_paste:
                try:
                    previous_winch = signal.signal(
                        signal.SIGWINCH, lambda *_: self._resized.set()
                    )
                    threading.Thread(target=self._redraw_on_resize, daemon=True).start()
                except ValueError:
                    previous_winch = None
            try:
                with _terminal_input(self.input):
                    for key in _keys(self.input):
                        if key == "PASTE_END":
                            command_candidate = ""
                            continue
                        if len(key) == 1:
                            if command_candidate == "" and key == "/":
                                command_candidate = "/"
                            elif (
                                command_candidate is not None
                                and command_candidate.startswith("/")
                            ):
                                command_candidate += key
                            else:
                                command_candidate = None
                        elif key == "BACKSPACE" and command_candidate:
                            command_candidate = command_candidate[:-1]
                        elif key != "ENTER":
                            command_candidate = ""
                        if key == "ENTER":
                            command = command_candidate or ""
                            command_candidate = ""
                        else:
                            command = ""
                        if key == "ENTER" and self._local_command(command):
                            if self._stopping.is_set():
                                return 0
                            continue
                        try:
                            with self._lock:
                                self.workspace.handle_key(key)
                                self._render_locked()
                        except (
                            TerminalConnectionError,
                            WorkspaceError,
                            ValueError,
                        ) as error:
                            with self._lock:
                                self.workspace.error = str(error)
                                self._render_locked()
            finally:
                if previous_winch is not None:
                    signal.signal(signal.SIGWINCH, previous_winch)
                if bracketed_paste:
                    self.output.write("\x1b[?2004l")
                    self.output.flush()
            return 0
        finally:
            self._stopping.set()
            self._event_generation += 1
            self.connection.close()

    def _redraw_on_resize(self) -> None:
        # The signal handler only sets the flag; drawing waits for the normal lock.
        while not self._stopping.is_set():
            if self._resized.wait(0.2):
                self._resized.clear()
                self._render()

    def _local_command(self, command: str) -> bool:
        command = command.strip()
        name, _, argument = command.partition(" ")
        if name not in {"/exit", "/help", "/retry"} or (
            argument and name != "/help"
        ):
            return False
        self._remove_local_command(command)
        with self._lock:
            if (
                self.workspace.connection_state == ConnectionState.CONNECTED
                and not self.workspace.stale
            ):
                self.workspace.error = None
        if command == "/exit":
            unsent = self.workspace.input.text
            if unsent and self._exit_warning_text != unsent:
                self._exit_warning_text = unsent
                self._write(
                    "Unsent text remains. Enter /exit again to discard it and exit."
                )
                self._render()
                return True
            self.workspace.input.clear()
            self._stopping.set()
            self._write("Exiting Maestro; service work continues.")
            return True
        self._exit_warning_text = None
        if name == "/help":
            with self._lock:
                self.workspace.extension_view_name = "Help"
                self.workspace.extension_view_content = help_text(argument)
                self.workspace.view = View.EXTENSION
            self._render()
            return True
        try:
            self._explicit_connect = True
            self.connection.retry_now()
            self._activate_workspace()
        except TerminalConnectionError:
            self._write("Retry failed; no previous command or answer was replayed.")
            self._render()
        finally:
            self._explicit_connect = False
        return True

    def _remove_local_command(self, command: str) -> None:
        text = self.workspace.input.text
        if not text.endswith(command):
            return
        self.workspace.input.text = text[: -len(command)]
        self.workspace.input.cursor = min(
            self.workspace.input.cursor, len(self.workspace.input.text)
        )

    def _handle_status(self, status: ConnectionStatus) -> None:
        retry = (
            ""
            if status.retry_in_seconds is None
            else f"; retrying in {status.retry_in_seconds} seconds"
        )
        if status.state not in (ConnectionState.CONNECTING, ConnectionState.CONNECTED):
            self._write(
                f"Connection {status.state.value}: {status.service_url} — {status.message}{retry}"
            )
        if status.clear_service_context:
            self._write("Prior service view and input cleared.")
        with self._lock:
            self.workspace.client = self.connection.client
            if status.state == ConnectionState.CONNECTED and self._explicit_connect:
                self.workspace.connection_state = ConnectionState.CONNECTED
                self.workspace.stale = False
                self.workspace.error = None
                return
            self.workspace.handle_connection_status(status)
            if status.state == ConnectionState.CONNECTED:
                self._start_events_locked()
            self._render_locked()

    def _activate_workspace(self) -> None:
        with self._lock:
            self.workspace.client = self.connection.client
            self.workspace.refresh()
            self._start_events_locked()
            self._render_locked()

    def _start_events_locked(self) -> None:
        if self.workspace.connection_state != ConnectionState.CONNECTED:
            return
        self._event_generation += 1
        generation = self._event_generation
        client = self.connection.client
        cursor = str(self.workspace.event_cursor)
        thread = threading.Thread(
            target=self._consume_events,
            args=(generation, client, cursor),
            daemon=True,
        )
        thread.start()

    def _consume_events(self, generation: int, client, cursor: str) -> None:
        try:
            for event in client.events(cursor):
                with self._lock:
                    if self._stopping.is_set() or generation != self._event_generation:
                        return
                    self.workspace.apply_event(event)
                    self._render_locked()
            if not self._stopping.is_set() and generation == self._event_generation:
                self.connection.disconnected("event stream ended")
        except TerminalConnectionError as error:
            if not self._stopping.is_set() and generation == self._event_generation:
                with self._lock:
                    self.workspace.handle_event_error(error)
                    if (
                        isinstance(error, ServiceError)
                        and error.code == "event_cursor_unavailable"
                    ):
                        self._start_events_locked()
                        self._render_locked()
                        return
                    self.connection.disconnected(str(error))
                    self._render_locked()

    def _render(self) -> None:
        with self._lock:
            self._render_locked()

    def _render_locked(self) -> None:
        size = get_terminal_size((100, 30))
        rendered = self.renderer.render(
            self.workspace, TerminalSize(size.columns, size.lines)
        )
        if getattr(self.output, "isatty", lambda: False)():
            # Leave the cursor right after the prompt text, where typing appears.
            self.output.write("\x1b[2J\x1b[H" + rendered)
            up = self.renderer.trailing_lines
            if up:
                self.output.write(f"\x1b[{up}A\r\x1b[{self.renderer.prompt_column}C")
            self._cursor_at_prompt = True
            self._lines_below_prompt = up
        else:
            self.output.write(rendered + "\n")
        self.output.flush()

    def _write(self, message: str) -> None:
        if self._cursor_at_prompt:
            if self._lines_below_prompt:
                self.output.write(f"\x1b[{self._lines_below_prompt}B")
            self.output.write("\n")
            self._cursor_at_prompt = False
        self.output.write(message + "\n")
        self.output.flush()


@contextmanager
def _terminal_input(stream: TextIO):
    if not getattr(stream, "isatty", lambda: False)():
        yield
        return
    descriptor = stream.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


ESCAPE_WAIT_SECONDS = 0.05


class _Characters:
    """Read characters one at a time, telling a lone Escape from a key sequence."""

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream
        self.terminal = getattr(stream, "isatty", lambda: False)()
        self.pending = ""
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")

    def _fill(self, count: int) -> bool:
        if not self.terminal:
            text = self.stream.read(count)
            self.pending += text
            return bool(text)
        data = os.read(self.stream.fileno(), 4096)
        if not data:
            return False
        self.pending += self.decoder.decode(data)
        return True

    def read(self, count: int = 1) -> str:
        while len(self.pending) < count:
            if not self._fill(count - len(self.pending)):
                break
        text, self.pending = self.pending[:count], self.pending[count:]
        return text

    def unread(self, text: str) -> None:
        self.pending = text + self.pending

    def ready(self) -> bool:
        """Whether more input is already waiting, or arrives at once."""
        if not self.terminal or self.pending:
            return True
        return bool(select.select([self.stream], [], [], ESCAPE_WAIT_SECONDS)[0])


def _keys(stream: TextIO):
    stream = _Characters(stream)
    while True:
        character = stream.read(1)
        if character == "":
            return
        if character in {"\r", "\n"}:
            yield "ENTER"
        elif character == "\t":
            yield "TAB"
        elif character in {"\x08", "\x7f"}:
            yield "BACKSPACE"
        elif character == "\x1b":
            if not stream.ready():
                yield "ESCAPE"
                continue
            opener = stream.read(1)
            if opener != "[":
                stream.unread(opener)
                yield "ESCAPE"
                continue
            suffix = opener + stream.read(1)
            if suffix == "[2":
                remainder = stream.read(3)
                if remainder == "00~":
                    yield from _paste_keys(stream)
                else:
                    yield "ESCAPE"
            elif suffix == "[1" and stream.read(4) == "3;2u":
                yield "SHIFT+ENTER"
            else:
                yield {
                    "[A": "UP",
                    "[B": "DOWN",
                    "[Z": "SHIFT+TAB",
                }.get(suffix, "ESCAPE")
        else:
            yield character


def _paste_keys(stream: _Characters):
    terminator = "\x1b[201~"
    content = ""
    while True:
        character = stream.read(1)
        if character == "":
            break
        content += character
        if content.endswith(terminator):
            content = content[: -len(terminator)]
            break
    index = 0
    while index < len(content):
        value = content[index]
        if value == "\r":
            if index + 1 < len(content) and content[index + 1] == "\n":
                index += 1
            yield "SHIFT+ENTER"
        elif value == "\n":
            yield "SHIFT+ENTER"
        else:
            yield value
        index += 1
    yield "PASTE_END"


def main(
    argv: Sequence[str] | None = None,
    *,
    connection_factory: Callable[[], TerminalConnection] = TerminalConnection,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> int:
    arguments = sys.argv[1:] if argv is None else list(argv)
    if arguments:
        raise SystemExit("the connected terminal accepts no command-line arguments")
    application = TerminalApplication(
        connection_factory(),
        input_stream=sys.stdin if input_stream is None else input_stream,
        output_stream=sys.stdout if output_stream is None else output_stream,
    )
    return application.run()


if __name__ == "__main__":
    raise SystemExit(main())
