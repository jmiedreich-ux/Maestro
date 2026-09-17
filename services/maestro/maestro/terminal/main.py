"""Minimal connected terminal entry point and offline command boundary."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from .connection import ConnectionStatus, TerminalConnection, TerminalConnectionError


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
        self.connection.subscribe(self._show_status)

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
            self.connection.connect()
        except TerminalConnectionError:
            self._write(
                "Retry connection with /retry. Local /help and /exit remain available."
            )

        for raw_line in self.input:
            command = raw_line.strip()
            if command == "/exit":
                self._write("Exiting Maestro; service work continues.")
                return 0
            if command == "/help":
                self.output.write(OFFLINE_HELP)
                self.output.flush()
                continue
            if command == "/retry":
                try:
                    self.connection.retry_now()
                except TerminalConnectionError:
                    self._write("Retry failed; no previous command or answer was replayed.")
                continue
            if not command:
                continue
            self._write(
                "That command is unavailable in the connection workspace. Use /help."
            )
        return 0

    def _show_status(self, status: ConnectionStatus) -> None:
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

    def _write(self, message: str) -> None:
        self.output.write(message + "\n")
        self.output.flush()


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
