"""The local Linux secret provider (M3 W0.1).

Resolves a durable secret reference to a real value at run time. Per
M0-D03, the operational database stores only a *reference*
(``provider`` + ``reference_name``) via
:meth:`OperationalStateStore.record_secret_reference` — never a value.
This module is the other half: it actually holds the value, as a
permission-locked file under the runtime ``var/`` tree, and resolves it
back on request. It never touches the operational database itself;
callers record the observation separately.
"""

from __future__ import annotations

import errno
import os
import stat

from .config import RuntimeConfig
from .operational_state import _PROVIDER, _REFERENCE_NAME

PROVIDER_NAME = "local-file"

_REQUIRED_FILE_MODE = 0o600


class SecretProviderError(ValueError):
    """Raised when a secret cannot be safely stored or resolved."""


class LocalFileSecretProvider:
    """Stores/resolves real secret values as permission-locked files
    under the runtime ``var/secrets`` directory.

    Reuses :class:`RuntimeConfig`'s own symlink-safe, race-resistant
    directory handling (the same discipline already applied to the
    operational database) rather than re-implementing it.
    """

    def __init__(self, config: RuntimeConfig) -> None:
        if not isinstance(config, RuntimeConfig):
            raise TypeError("LocalFileSecretProvider requires RuntimeConfig")
        self._secrets_config = RuntimeConfig(config.runtime_dir / "secrets")

    def store(self, reference_name: str, value: str) -> None:
        """Persist ``value`` under ``reference_name``, mode 0600.

        Overwrites any existing value for the same reference name
        (rotation is expected to call this again with a fresh value).
        """
        _validate_reference_name(reference_name)
        if not isinstance(value, str) or not value:
            raise SecretProviderError("secret value must be a non-empty string")
        with self._secrets_config.open_runtime_dir_fd() as secrets_fd:
            _write_secret_file(secrets_fd, reference_name, value)

    def resolve(self, reference_name: str) -> str:
        """Return the real value stored for ``reference_name``.

        Refuses to read anything that is not a regular, mode-0600,
        non-symlinked file — a loosened or swapped-out secret file is
        a visible error, never a silent read of unsafe material.
        """
        _validate_reference_name(reference_name)
        with self._secrets_config.open_runtime_dir_fd() as secrets_fd:
            return _read_secret_file(secrets_fd, reference_name)


def _validate_reference_name(reference_name: object) -> None:
    if not isinstance(reference_name, str) or _REFERENCE_NAME.fullmatch(reference_name) is None:
        raise SecretProviderError("reference_name must match the closed non-secret grammar")


def _validate_provider_name(provider: object) -> None:
    if not isinstance(provider, str) or _PROVIDER.fullmatch(provider) is None:
        raise SecretProviderError("provider must match the closed non-secret grammar")


def _write_secret_file(dir_fd: int, reference_name: str, value: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
    try:
        fd = os.open(reference_name, flags, mode=_REQUIRED_FILE_MODE, dir_fd=dir_fd)
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise SecretProviderError(
                f"secret path for {reference_name!r} is a symlink, refusing to write"
            ) from error
        raise
    try:
        os.fchmod(fd, _REQUIRED_FILE_MODE)
        os.write(fd, value.encode("utf-8"))
    finally:
        os.close(fd)


def _read_secret_file(dir_fd: int, reference_name: str) -> str:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    try:
        fd = os.open(reference_name, flags, dir_fd=dir_fd)
    except FileNotFoundError as error:
        raise SecretProviderError(f"no stored secret for reference {reference_name!r}") from error
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise SecretProviderError(
                f"secret path for {reference_name!r} is a symlink, refusing to read"
            ) from error
        raise
    try:
        status = os.fstat(fd)
        if not stat.S_ISREG(status.st_mode):
            raise SecretProviderError(f"secret path for {reference_name!r} is not a regular file")
        mode_bits = stat.S_IMODE(status.st_mode)
        if mode_bits != _REQUIRED_FILE_MODE:
            raise SecretProviderError(
                f"secret file for {reference_name!r} has unsafe permissions "
                f"{oct(mode_bits)}, refusing to read"
            )
        chunks = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks).decode("utf-8")
    finally:
        os.close(fd)


def secret_reference_observation(
    *,
    secret_reference_observation_id: str,
    project_id: str,
    binding_id: str,
    reference_name: str,
    owner_reference: str,
    status: str = "Active",
    rotation_at: str | None = None,
    expires_at: str | None = None,
    observed_at: str,
) -> dict:
    """Build the row shape ``OperationalStateStore.record_secret_reference``
    expects, pinned to this module's own :data:`PROVIDER_NAME`.

    A thin builder, not a new contract — the receiving validation
    (``_secret_reference`` in ``operational_state.py``) remains the
    single source of truth for the shape; this only saves every caller
    from re-typing ``"provider": PROVIDER_NAME`` by hand.
    """
    _validate_provider_name(PROVIDER_NAME)
    return {
        "secret_reference_observation_id": secret_reference_observation_id,
        "project_id": project_id,
        "binding_id": binding_id,
        "provider": PROVIDER_NAME,
        "reference_name": reference_name,
        "owner_reference": owner_reference,
        "rotation_at": rotation_at,
        "expires_at": expires_at,
        "status": status,
        "observed_at": observed_at,
    }
