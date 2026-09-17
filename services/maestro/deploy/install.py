#!/usr/bin/env python3
"""Install Maestro's Linux service files and separated local credentials."""

from __future__ import annotations

import argparse
import grp
import hashlib
import importlib.metadata
import os
import pwd
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


SERVICE_USER = "maestro"
AGENT_USER = "maestro-agent"
WORKSPACE_GROUP = "maestro-workspace"
OWNER_TOKEN_NAME = "owner.token"
UNIT_NAME = "maestro.service"


class InstallationError(RuntimeError):
    """Installation cannot proceed without risking an incomplete setup."""


@dataclass(frozen=True)
class Account:
    name: str
    uid: int
    gid: int


@dataclass(frozen=True)
class InstallationPaths:
    """Every filesystem target, including safe relocated test targets."""

    root: Path
    config_dir: Path
    config_file: Path
    data_dir: Path
    workspace_dir: Path
    schema_dir: Path
    unit_file: Path
    operator_config_dir: Path
    owner_token: Path
    cli_config: Path

    @classmethod
    def build(cls, root: Path, operator_home: Path) -> "InstallationPaths":
        supplied_root = root.absolute()
        supplied_operator_home = operator_home.absolute()
        if supplied_root.is_symlink() or supplied_operator_home.is_symlink():
            raise InstallationError("installation root and operator home must not be links")
        root = supplied_root.resolve(strict=True)
        operator_home = supplied_operator_home.resolve(strict=True)
        if not root.is_dir() or root.is_symlink():
            raise InstallationError("installation root must be a real directory")
        if not operator_home.is_dir() or operator_home.is_symlink():
            raise InstallationError("operator home must be a real directory")
        if root != Path("/") and not operator_home.is_relative_to(root):
            raise InstallationError("staged operator home must be below the isolated root")

        def under(absolute: str) -> Path:
            relative = Path(absolute).relative_to("/")
            return Path("/") / relative if root == Path("/") else root / relative

        config_dir = under("/etc/maestro")
        data_dir = under("/var/lib/maestro")
        install_dir = under("/opt/maestro")
        operator_config_dir = operator_home / ".config" / "maestro"
        return cls(
            root=root,
            config_dir=config_dir,
            config_file=config_dir / "agents.toml",
            data_dir=data_dir,
            workspace_dir=data_dir / "workspaces",
            schema_dir=install_dir / "schemas",
            unit_file=under("/etc/systemd/system/maestro.service"),
            operator_config_dir=operator_config_dir,
            owner_token=operator_config_dir / OWNER_TOKEN_NAME,
            cli_config=operator_config_dir / "cli.toml",
        )


@dataclass(frozen=True)
class Installation:
    paths: InstallationPaths
    operator: Account
    service: Account
    agent: Account
    service_executable: Path
    owner_id: str
    port: int
    schema_sources: tuple[Path, ...] = ()
    production: bool = False

    def validate(self) -> None:
        accounts = {self.operator.name, self.service.name, self.agent.name}
        if len(accounts) != 3:
            raise InstallationError("operator, service, and agent accounts must be distinct")
        if self.operator.uid in {self.service.uid, self.agent.uid}:
            raise InstallationError("operator, service, and agent user IDs must be distinct")
        if self.service.uid == self.agent.uid:
            raise InstallationError("service and agent user IDs must be distinct")
        if self.service.gid == self.agent.gid:
            raise InstallationError("service and agent primary groups must be distinct")
        if not self.service_executable.is_absolute():
            raise InstallationError("service executable path must be absolute")
        if self.production and (
            not self.service_executable.is_file()
            or not os.access(self.service_executable, os.X_OK)
        ):
            raise InstallationError("installed service executable is missing or not executable")
        if not _identifier(self.owner_id):
            raise InstallationError("Owner identity is invalid")
        if isinstance(self.port, bool) or not 1 <= self.port <= 65535:
            raise InstallationError("service port must be between 1 and 65535")
        for source in self.schema_sources:
            _validate_schema_source(source)


def install(configuration: Installation, *, replace: bool = False) -> str:
    """Install files only after all supplied paths and resources validate."""
    configuration.validate()
    paths = configuration.paths
    guarded = (
        paths.config_file,
        paths.owner_token,
        paths.cli_config,
        paths.unit_file,
    )
    if not replace:
        existing = [str(path) for path in guarded if path.exists() or path.is_symlink()]
        if existing:
            raise InstallationError(
                "refusing to replace an existing installation: " + ", ".join(existing)
            )
    for path in guarded:
        if path.is_symlink():
            raise InstallationError(f"refusing linked installation target: {path}")
        _reject_linked_components(path, paths.root)
    for source in configuration.schema_sources:
        target = paths.schema_dir / source.parent.name / source.name
        if target.exists() or target.is_symlink():
            raise InstallationError(
                f"schema bundle already exists: {source.parent.name}@{source.name}"
            )

    token = secrets.token_hex(32)
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    unit_template = Path(__file__).with_name(UNIT_NAME).read_text(encoding="utf-8")
    unit = (
        unit_template.replace("@SERVICE_USER@", configuration.service.name)
        .replace("@SERVICE_GROUP@", configuration.service.name)
        .replace("@SERVICE_EXECUTABLE@", str(configuration.service_executable))
        .replace("@CONFIG_FILE@", str(paths.config_file))
        .replace("@DATA_DIR@", str(paths.data_dir))
    )
    if "@" in unit:
        raise InstallationError("systemd unit contains an unresolved installation value")

    _secure_directory(paths.config_dir, 0o750, 0, configuration.service.gid)
    _secure_directory(paths.data_dir, 0o711, configuration.service.uid, configuration.service.gid)
    _secure_directory(
        paths.workspace_dir,
        0o770,
        configuration.service.uid,
        _group_gid(WORKSPACE_GROUP, fallback=configuration.agent.gid),
    )
    _secure_directory(paths.schema_dir, 0o755, 0, 0)
    _secure_directory(
        paths.operator_config_dir,
        0o700,
        configuration.operator.uid,
        configuration.operator.gid,
    )
    paths.unit_file.parent.mkdir(parents=True, exist_ok=True)

    storage_path = paths.data_dir / "maestro.sqlite3"
    service_config = _service_configuration(
        owner_id=configuration.owner_id,
        digest=digest,
        storage_path=storage_path,
        workspace_root=paths.workspace_dir,
        agent_user=configuration.agent.name,
        port=configuration.port,
    )
    cli_config = (
        f'service_url = "http://localhost:{configuration.port}"\n'
        f'owner_credential_file = "{paths.owner_token}"\n'
    )
    _atomic_write(paths.config_file, service_config, 0o640, 0, configuration.service.gid)
    _atomic_write(
        paths.owner_token,
        token,
        0o600,
        configuration.operator.uid,
        configuration.operator.gid,
    )
    _atomic_write(
        paths.cli_config,
        cli_config,
        0o600,
        configuration.operator.uid,
        configuration.operator.gid,
    )
    _atomic_write(paths.unit_file, unit, 0o644, 0, 0)
    _copy_schema_bundles(configuration.schema_sources, paths.schema_dir)
    return digest


def discover_installed_schema_sources() -> tuple[Path, ...]:
    """Discover immutable bundles declared in the installed distribution."""
    try:
        distribution = importlib.metadata.distribution("maestro")
    except importlib.metadata.PackageNotFoundError:
        return ()
    sources: list[Path] = []
    for entry in distribution.files or ():
        parts = PurePosixPath(str(entry)).parts
        for index, part in enumerate(parts):
            if part == "schemas":
                candidate = Path(distribution.locate_file(entry))
                relative = parts[index + 1 :]
                if len(relative) >= 3 and relative[-1] == "schema.json":
                    sources.append(candidate.parent)
                break
    return tuple(sorted(set(sources)))


def create_system_accounts() -> None:
    """Create the fixed service, agent, and shared-workspace identities."""
    if os.geteuid() != 0:
        raise InstallationError("production installation must run as root")
    _ensure_group(SERVICE_USER)
    _ensure_group(AGENT_USER)
    _ensure_group(WORKSPACE_GROUP)
    _ensure_user(SERVICE_USER, SERVICE_USER, "/var/lib/maestro")
    _ensure_user(AGENT_USER, AGENT_USER, "/nonexistent")
    for user in (SERVICE_USER, AGENT_USER):
        subprocess.run(
            ["usermod", "--append", "--groups", WORKSPACE_GROUP, user],
            check=True,
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the Maestro systemd service")
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--operator-home", type=Path)
    parser.add_argument("--operator-user")
    parser.add_argument(
        "--service-executable",
        type=Path,
        default=Path("/opt/maestro/bin/maestro-service"),
    )
    parser.add_argument("--owner-id", default="owner-local")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "--staged-test",
        action="store_true",
        help="write only below --root using supplied numeric test identities",
    )
    parser.add_argument("--operator-uid", type=int)
    parser.add_argument("--operator-gid", type=int)
    parser.add_argument("--service-uid", type=int)
    parser.add_argument("--service-gid", type=int)
    parser.add_argument("--agent-uid", type=int)
    parser.add_argument("--agent-gid", type=int)
    arguments = parser.parse_args(argv)
    try:
        if arguments.staged_test:
            if arguments.root == Path("/"):
                raise InstallationError("staged tests require an isolated --root")
            required = (
                arguments.operator_uid,
                arguments.operator_gid,
                arguments.service_uid,
                arguments.service_gid,
                arguments.agent_uid,
                arguments.agent_gid,
            )
            if any(value is None or value < 0 for value in required):
                raise InstallationError("staged tests require all numeric test identities")
            operator_name = arguments.operator_user or "test-operator"
            operator = Account(operator_name, arguments.operator_uid, arguments.operator_gid)
            service = Account(SERVICE_USER, arguments.service_uid, arguments.service_gid)
            agent = Account(AGENT_USER, arguments.agent_uid, arguments.agent_gid)
        else:
            if arguments.root != Path("/"):
                raise InstallationError("a relocated root requires --staged-test")
            if os.geteuid() != 0:
                raise InstallationError("production installation must run as root")
            operator_name = arguments.operator_user or os.environ.get("SUDO_USER")
            if not operator_name or operator_name == "root":
                raise InstallationError("identify the non-root operator with --operator-user")
            if operator_name in {SERVICE_USER, AGENT_USER}:
                raise InstallationError("operator, service, and agent accounts must be distinct")
            operator = _account(operator_name)
            if not arguments.service_executable.is_absolute():
                raise InstallationError("service executable path must be absolute")
            if (
                not arguments.service_executable.is_file()
                or not os.access(arguments.service_executable, os.X_OK)
            ):
                raise InstallationError(
                    "installed service executable is missing or not executable"
                )
            if not _identifier(arguments.owner_id):
                raise InstallationError("Owner identity is invalid")
            if not 1 <= arguments.port <= 65535:
                raise InstallationError("service port must be between 1 and 65535")
            create_system_accounts()
            service = _account(SERVICE_USER)
            agent = _account(AGENT_USER)
        operator_home = arguments.operator_home or Path(pwd.getpwnam(operator.name).pw_dir)
        paths = InstallationPaths.build(arguments.root, operator_home)
        sources = discover_installed_schema_sources()
        configuration = Installation(
            paths=paths,
            operator=operator,
            service=service,
            agent=agent,
            service_executable=arguments.service_executable,
            owner_id=arguments.owner_id,
            port=arguments.port,
            schema_sources=sources,
            production=not arguments.staged_test,
        )
        install(configuration, replace=arguments.replace)
        if not arguments.staged_test:
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "--now", UNIT_NAME], check=True)
        print(f"Maestro installed; Owner credential: {paths.owner_token}")
        print(f"Service configuration: {paths.config_file}")
        print(f"Service unit: {paths.unit_file}")
        return 0
    except (InstallationError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Maestro installation failed: {error}", file=sys.stderr)
        return 1


def _service_configuration(
    *,
    owner_id: str,
    digest: str,
    storage_path: Path,
    workspace_root: Path,
    agent_user: str,
    port: int,
) -> str:
    return (
        f'workspace_root = "{workspace_root}"\n\n'
        "[service]\n"
        'host = "127.0.0.1"\n'
        f"port = {port}\n"
        f'agent_user = "{agent_user}"\n\n'
        "[storage]\n"
        'engine = "sqlite"\n'
        f'path = "{storage_path}"\n\n'
        "[owner]\n"
        f'id = "{owner_id}"\n'
        f'token_sha256 = "{digest}"\n'
    )


def _atomic_write(path: Path, content: str, mode: int, uid: int, gid: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        _fchown(descriptor, uid, gid)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _secure_directory(path: Path, mode: int, uid: int, gid: int) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise InstallationError(f"installation directory is not a real directory: {path}")
    os.chmod(path, mode)
    _chown(path, uid, gid)


def _reject_linked_components(path: Path, root: Path) -> None:
    if root != Path("/") and not path.is_relative_to(root):
        raise InstallationError(f"installation target escapes the isolated root: {path}")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            details = os.lstat(current)
        except FileNotFoundError:
            return
        if stat.S_ISLNK(details.st_mode):
            raise InstallationError(f"installation path contains a symbolic link: {current}")


def _copy_schema_bundles(sources: Iterable[Path], destination: Path) -> None:
    for source in sources:
        _validate_schema_source(source)
        name = source.parent.name
        version = source.name
        target = destination / name / version
        if target.exists():
            raise InstallationError(f"schema bundle already exists: {name}@{version}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=False)
        for item in target.rglob("*"):
            if item.is_symlink():
                raise InstallationError(f"schema bundle contains a symbolic link: {source}")
            os.chmod(item, 0o755 if item.is_dir() else 0o644)


def _validate_schema_source(source: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        raise InstallationError(f"schema bundle is not a real directory: {source}")
    if not source.name.isdigit() or int(source.name) < 1 or not _identifier(source.parent.name):
        raise InstallationError(f"schema bundle path must end in <name>/<version>: {source}")
    schema = source / "schema.json"
    if schema.is_symlink() or not schema.is_file():
        raise InstallationError(f"schema bundle has no regular schema.json: {source}")
    for item in source.rglob("*"):
        if item.is_symlink():
            raise InstallationError(f"schema bundle contains a symbolic link: {source}")


def _identifier(value: str) -> bool:
    return bool(value) and len(value) <= 128 and all(
        character.isalnum() or character in "._-" for character in value
    )


def _account(name: str) -> Account:
    entry = pwd.getpwnam(name)
    return Account(name, entry.pw_uid, entry.pw_gid)


def _group_gid(name: str, *, fallback: int) -> int:
    try:
        return grp.getgrnam(name).gr_gid
    except KeyError:
        return fallback


def _ensure_group(name: str) -> None:
    try:
        grp.getgrnam(name)
    except KeyError:
        subprocess.run(["groupadd", "--system", name], check=True)


def _ensure_user(name: str, group: str, home: str) -> None:
    try:
        entry = pwd.getpwnam(name)
    except KeyError:
        subprocess.run(
            [
                "useradd",
                "--system",
                "--gid",
                group,
                "--home-dir",
                home,
                "--shell",
                "/usr/sbin/nologin",
                name,
            ],
            check=True,
        )
        return
    expected_gid = grp.getgrnam(group).gr_gid
    if entry.pw_gid != expected_gid:
        raise InstallationError(f"existing account {name} has the wrong primary group")
    if entry.pw_shell not in {"/usr/sbin/nologin", "/sbin/nologin", "/bin/false"}:
        raise InstallationError(f"existing account {name} has an interactive shell")
    if entry.pw_dir != home:
        raise InstallationError(f"existing account {name} has the wrong home directory")


def _chown(path: Path, uid: int, gid: int) -> None:
    if os.geteuid() == 0:
        os.chown(path, uid, gid, follow_symlinks=False)


def _fchown(descriptor: int, uid: int, gid: int) -> None:
    if os.geteuid() == 0:
        os.fchown(descriptor, uid, gid)


if __name__ == "__main__":
    raise SystemExit(main())
