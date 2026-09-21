"""Minimal connected terminal entry point and offline command boundary."""

from __future__ import annotations

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
from .questions import QuestionsExtension
from .registration import RegistrationExtension
from .rendering import TerminalRenderer, TerminalSize
from .workspace import Workspace, WorkspaceError


OFFLINE_HELP = """Available commands:
  /help   Show commands available in the current terminal.
  /retry  Reload connection configuration and retry immediately.
  /exit   Exit the terminal without stopping service work.
"""


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
        RegistrationExtension().install(extensions)
        self.workspace = Workspace(self.connection.client, extensions=extensions)
        self.renderer = TerminalRenderer()
        self._lock = threading.RLock()
        self._stopping = threading.Event()
        self._event_generation = 0
        self._explicit_connect = False
        self._exit_warning_text: str | None = None
        self.connection.subscribe(self._handle_status)

    def run(self) -> int:
        configuration = self.connection.configuration
        self._write(f"Maestro service: {configuration.service_url}")
        if configuration.fallback_reason:
            self._write(
                f"Configuration fallback: {configuration.fallback_reason}; "
                f"using {configuration.service_url}"
            )
        self._write(f"Authentication: {self.connection.credential_status()}")
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
                if bracketed_paste:
                    self.output.write("\x1b[?2004l")
                    self.output.flush()
            return 0
        finally:
            self._stopping.set()
            self._event_generation += 1
            self.connection.close()

    def _local_command(self, command: str) -> bool:
        command = command.strip()
        if command not in {"/exit", "/help", "/retry"}:
            return False
        self._remove_local_command(command)
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
        if command == "/help":
            self.output.write(OFFLINE_HELP)
            self.output.flush()
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
            self.output.write("\x1b[2J\x1b[H")
        self.output.write(rendered + "\n")
        self.output.flush()

    def _write(self, message: str) -> None:
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


def _keys(stream: TextIO):
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
            suffix = stream.read(2)
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


def _paste_keys(stream: TextIO):
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
