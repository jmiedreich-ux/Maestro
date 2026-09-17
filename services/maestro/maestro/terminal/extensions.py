"""Storage-free extension boundary for terminal commands, views, and controls."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeVar


class TerminalClient(Protocol):
    """Authenticated service operations exposed to terminal extensions."""

    def get_json(self, path: str, *, timeout: int = 15) -> Mapping[str, object]: ...

    def submit(self, envelope: Mapping[str, object]) -> Mapping[str, object]: ...


class ProjectedState(Protocol):
    selected_project_id: str | None
    selected_activity_id: str | None


@dataclass(frozen=True)
class ExtensionContext:
    """The only capabilities supplied to an extension callback."""

    client: TerminalClient
    state: ProjectedState


T = TypeVar("T")
ExtensionCallback = Callable[[ExtensionContext, str], T]


class ExtensionRegistry:
    """Register named terminal contributions without granting storage access."""

    def __init__(self) -> None:
        self._commands: dict[str, ExtensionCallback[object]] = {}
        self._views: dict[str, ExtensionCallback[object]] = {}
        self._actions: dict[str, ExtensionCallback[object]] = {}

    def register_command(self, name: str, callback: ExtensionCallback[object]) -> None:
        self._register(self._commands, name, callback, "command")

    def register_view(self, name: str, callback: ExtensionCallback[object]) -> None:
        self._register(self._views, name, callback, "view")

    def register_action(self, name: str, callback: ExtensionCallback[object]) -> None:
        self._register(self._actions, name, callback, "action")

    @property
    def command_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._commands))

    def invoke_command(
        self, name: str, context: ExtensionContext, arguments: str = ""
    ) -> object:
        return self._invoke(self._commands, name, context, arguments, "command")

    def render_view(
        self, name: str, context: ExtensionContext, arguments: str = ""
    ) -> object:
        return self._invoke(self._views, name, context, arguments, "view")

    def invoke_action(
        self, name: str, context: ExtensionContext, arguments: str = ""
    ) -> object:
        return self._invoke(self._actions, name, context, arguments, "action")

    @staticmethod
    def _register(
        target: dict[str, ExtensionCallback[object]],
        name: str,
        callback: ExtensionCallback[object],
        kind: str,
    ) -> None:
        normalized = _name(name)
        if not callable(callback):
            raise TypeError(f"terminal {kind} callback must be callable")
        if normalized in target:
            raise ValueError(f"terminal {kind} already registered: {normalized}")
        target[normalized] = callback

    @staticmethod
    def _invoke(
        target: Mapping[str, ExtensionCallback[object]],
        name: str,
        context: ExtensionContext,
        arguments: str,
        kind: str,
    ) -> object:
        normalized = _name(name)
        try:
            callback = target[normalized]
        except KeyError as error:
            raise KeyError(f"unknown terminal {kind}: {normalized}") from error
        return callback(context, arguments)


def _name(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("terminal extension name must be text")
    normalized = value.strip().casefold().removeprefix("/")
    if not normalized or any(
        not (character.isascii() and (character.isalnum() or character in "-_"))
        for character in normalized
    ):
        raise ValueError("terminal extension name must be a simple name")
    return normalized
