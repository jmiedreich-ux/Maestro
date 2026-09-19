"""Exact-source agent workspaces and Linux mount-isolation plans."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

from maestro.foundation import ContractError, canonical_identifier
from maestro.git_repository import GitRepositoryError, ReadOnlyGitRepository


_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_INPUT_SET_BYTES = 64 * 1024 * 1024
_BWRAP = Path("/usr/bin/bwrap")
_EGRESS_LAUNCHER = Path("/usr/local/libexec/maestro-agent-egress")
_SUDO = Path("/usr/bin/sudo")


class WorkspaceError(ValueError):
    """A typed workspace preparation or integrity failure."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    source: Path
    input: Path
    output: Path
    scratch: Path
    assignment: Path


@dataclass(frozen=True)
class ServiceProfileBinding:
    """Selected route profile mapped to the supported tool's minimal auth files."""

    tool: str
    credential_profile: str
    settings_profile: str
    service_home: Path

    def __post_init__(self) -> None:
        if self.tool not in {"codex", "claude_code"}:
            raise WorkspaceError("invalid_profile", "profile tool is unsupported")
        canonical_identifier(self.credential_profile, "credential_profile")
        canonical_identifier(self.settings_profile, "settings_profile")
        root = Path(self.service_home)
        if not root.is_absolute() or not root.is_dir() or root.is_symlink():
            raise WorkspaceError("invalid_profile", "service profile home is unsafe or unavailable")
        object.__setattr__(self, "service_home", root)

    def validate_selection(
        self, tool: str, credential_profile: str, settings_profile: str
    ) -> None:
        if (
            tool != self.tool
            or credential_profile != self.credential_profile
            or settings_profile != self.settings_profile
        ):
            raise WorkspaceError("profile_mismatch", "runtime profile does not match selected route")

    def mounts(self) -> tuple[tuple[Path, PurePosixPath], ...]:
        layouts = {
            "codex": ((".codex/auth.json", ".codex/auth.json"),),
            "claude_code": (
                (".claude.json", ".claude.json"),
                (".claude/.credentials.json", ".claude/.credentials.json"),
            ),
        }
        owner = self.service_home.stat().st_uid
        result: list[tuple[Path, PurePosixPath]] = []
        for source_name, target_name in layouts[self.tool]:
            source = self.service_home / source_name
            current = self.service_home
            for part in PurePosixPath(source_name).parent.parts:
                current /= part
                try:
                    directory = current.lstat()
                except FileNotFoundError as error:
                    raise WorkspaceError(
                        "profile_unavailable", f"required {self.tool} profile directory is unavailable"
                    ) from error
                if (
                    not stat.S_ISDIR(directory.st_mode)
                    or current.is_symlink()
                    or directory.st_uid != owner
                    or stat.S_IMODE(directory.st_mode) & 0o002
                ):
                    raise WorkspaceError(
                        "unsafe_profile", f"required {self.tool} profile directory is unsafe"
                    )
            try:
                metadata = source.lstat()
            except FileNotFoundError as error:
                raise WorkspaceError(
                    "profile_unavailable", f"required {self.tool} credential file is unavailable"
                ) from error
            if (
                not stat.S_ISREG(metadata.st_mode)
                or source.is_symlink()
                or metadata.st_uid != owner
                or stat.S_IMODE(metadata.st_mode) & 0o077
            ):
                raise WorkspaceError(
                    "unsafe_profile", f"required {self.tool} credential file is unsafe"
                )
            result.append((source, PurePosixPath(target_name)))
        return tuple(result)


@dataclass(frozen=True)
class PreparedWorkspace:
    project_id: str
    activity_id: str
    run_id: str
    source_commit: str
    paths: WorkspacePaths
    assignment_sha256: str
    immutable_hashes: tuple[tuple[str, str], ...]
    isolation_executable: Path
    workspace_root: Path

    def isolated_command(
        self,
        tool_arguments: Sequence[str],
        *,
        profile: ServiceProfileBinding | None = None,
    ) -> tuple[str, ...]:
        if (
            not isinstance(tool_arguments, (tuple, list))
            or not tool_arguments
            or any(not isinstance(value, str) or not value for value in tool_arguments)
        ):
            raise WorkspaceError("invalid_launch", "tool arguments must be nonempty text")
        executable = Path(tool_arguments[0])
        if not executable.is_absolute() or not executable.is_file():
            raise WorkspaceError("invalid_launch", "tool executable must be an installed absolute path")
        try:
            executable = executable.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise WorkspaceError("invalid_launch", "tool executable cannot be resolved") from error
        canonical_arguments = (str(executable), *tool_arguments[1:])
        run = self.paths.root
        home = self.paths.scratch / "home"
        config_home = home / ".config"
        home.mkdir(mode=0o700, exist_ok=True)
        config_home.mkdir(mode=0o700, exist_ok=True)
        if home.is_symlink() or config_home.is_symlink():
            raise WorkspaceError("unsafe_profile", "isolated profile home is unsafe")
        profile_mounts = () if profile is None else profile.mounts()
        for _, target in profile_mounts:
            home.joinpath(*target.parent.parts).mkdir(parents=True, exist_ok=True, mode=0o700)
        directories = _path_chain(self.workspace_root, run)
        arguments: list[str] = [
            str(self.isolation_executable),
            "--die-with-parent",
            "--new-session",
            "--unshare-user",
            "--unshare-pid",
            "--unshare-uts",
            "--unshare-ipc",
            "--unshare-cgroup",
            "--cap-drop",
            "ALL",
            "--clearenv",
            "--tmpfs",
            "/",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
        ]
        for runtime_path in _runtime_paths(executable):
            for directory in _path_chain(Path("/"), runtime_path.parent):
                arguments.extend(("--dir", str(directory)))
            arguments.extend(("--ro-bind", str(runtime_path), str(runtime_path)))
        for directory in _path_chain(Path("/"), self.workspace_root):
            arguments.extend(("--dir", str(directory)))
        for directory in directories:
            arguments.extend(("--dir", str(directory)))
        arguments.extend(
            (
                "--ro-bind",
                str(self.paths.source),
                str(self.paths.source),
                "--ro-bind",
                str(self.paths.input),
                str(self.paths.input),
                "--ro-bind",
                str(self.paths.assignment),
                str(self.paths.assignment),
                "--bind",
                str(self.paths.output),
                str(self.paths.output),
                "--bind",
                str(self.paths.scratch),
                str(self.paths.scratch),
                "--setenv",
                "HOME",
                str(home),
                "--setenv",
                "XDG_CONFIG_HOME",
                str(config_home),
                "--setenv",
                "PATH",
                "/usr/bin:/bin",
            )
        )
        for source, target in profile_mounts:
            arguments.extend(
                (
                    "--ro-bind",
                    str(source),
                    str(home.joinpath(*target.parts)),
                )
            )
        arguments.extend(
            (
                "--chdir",
                str(run),
                "--",
                *canonical_arguments,
            )
        )
        return tuple(arguments)

    def egress_command(
        self, route_tool: str, isolated_arguments: Sequence[str]
    ) -> tuple[str, ...]:
        """Bind an isolated launch to the installed root-supervised egress guard."""
        if route_tool not in {"codex", "claude_code"}:
            raise WorkspaceError("invalid_launch", "agent route tool is unsupported")
        try:
            canonical_identifier(self.run_id, "run_id")
            isolation_executable = self.isolation_executable.resolve(strict=True)
        except (ContractError, OSError, RuntimeError) as error:
            raise WorkspaceError("invalid_launch", "isolated launch identity is invalid") from error
        if isolation_executable != _BWRAP:
            raise WorkspaceError(
                "isolation_unavailable",
                "root-supervised egress requires the installed Bubblewrap executable",
            )
        if (
            not isinstance(isolated_arguments, (tuple, list))
            or not isolated_arguments
            or any(not isinstance(value, str) or not value for value in isolated_arguments)
            or isolated_arguments[0] != str(_BWRAP)
            or "--" not in isolated_arguments
        ):
            raise WorkspaceError("invalid_launch", "isolated command is invalid for egress control")
        if not _SUDO.is_file() or not os.access(_SUDO, os.X_OK):
            raise WorkspaceError("isolation_unavailable", "noninteractive service elevation is unavailable")
        if not _EGRESS_LAUNCHER.is_file() or not os.access(_EGRESS_LAUNCHER, os.X_OK):
            raise WorkspaceError("isolation_unavailable", "root-supervised egress launcher is unavailable")
        return (
            str(_SUDO),
            "-n",
            str(_EGRESS_LAUNCHER),
            route_tool,
            self.run_id,
            *isolated_arguments,
        )

    def verify_restrictions(self) -> None:
        """Detect any mutation of immutable paths before accepting a response."""
        observed = _hash_tree(self.paths.root, ("source", "input", "assignment.json"))
        if tuple(sorted(observed.items())) != self.immutable_hashes:
            raise WorkspaceError(
                "forbidden_write", "source, input, or assignment content changed during the run"
            )
        for writable in (self.paths.output, self.paths.scratch):
            _verify_writable_tree(writable)

    def resolve_artifact(self, relative_path: str, *, allow_input: bool = False) -> Path:
        relative = _relative_path(relative_path, "artifact path")
        first = relative.parts[0]
        allowed = {"output"}
        if allow_input:
            allowed.add("input")
        if first not in allowed:
            raise WorkspaceError(
                "artifact_out_of_scope", "artifact is outside its assigned artifact roots"
            )
        path = self.paths.root.joinpath(*relative.parts)
        if path.is_symlink() or not path.is_file():
            raise WorkspaceError("artifact_missing", f"artifact is unavailable: {relative_path}")
        try:
            path.relative_to(self.paths.root)
        except ValueError as error:  # pragma: no cover - defensive after lexical validation
            raise WorkspaceError("artifact_out_of_scope", "artifact escapes the workspace") from error
        return path


class WorkspaceManager:
    """Materialize a fresh run workspace from an exact Git commit."""

    def __init__(self, root: Path, *, isolation_executable: Path = Path("/usr/bin/bwrap")) -> None:
        self.root = Path(root)
        self.isolation_executable = Path(isolation_executable)
        if not self.root.is_absolute() or not self.root.is_dir() or self.root.is_symlink():
            raise WorkspaceError("invalid_workspace_root", "workspace root must be an existing absolute directory")
        if (
            not self.isolation_executable.is_absolute()
            or not self.isolation_executable.is_file()
            or not os.access(self.isolation_executable, os.X_OK)
        ):
            raise WorkspaceError(
                "isolation_unavailable", "configured Linux workspace isolation is unavailable"
            )

    def prepare(
        self,
        *,
        project_id: str,
        activity_id: str,
        run_id: str,
        source_repository: Path,
        source_commit: str,
        assignment_bytes: bytes,
        inputs: Mapping[str, bytes] | None = None,
    ) -> PreparedWorkspace:
        for value, field in (
            (project_id, "project_id"),
            (activity_id, "activity_id"),
            (run_id, "run_id"),
        ):
            canonical_identifier(value, field)
        if not isinstance(source_commit, str) or _COMMIT.fullmatch(source_commit) is None:
            raise WorkspaceError("invalid_source", "source_commit must be one lowercase full commit")
        if not isinstance(assignment_bytes, bytes) or not assignment_bytes:
            raise WorkspaceError("invalid_assignment", "assignment must be nonempty UTF-8 bytes")
        try:
            assignment_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WorkspaceError("invalid_assignment", "assignment must be UTF-8") from error
        normalized_inputs = _validate_inputs({} if inputs is None else inputs)
        run = self.root / project_id / activity_id / "runs" / run_id
        if run.exists() or run.is_symlink():
            raise WorkspaceError("workspace_exists", "run workspace already exists")
        run.mkdir(parents=True, mode=0o700)
        paths = WorkspacePaths(
            run,
            run / "source",
            run / "input",
            run / "output",
            run / "scratch",
            run / "assignment.json",
        )
        try:
            self._checkout(source_repository, source_commit, paths.source)
            paths.input.mkdir(mode=0o700)
            paths.output.mkdir(mode=0o700)
            paths.scratch.mkdir(mode=0o700)
            for relative, content in normalized_inputs.items():
                target = paths.input.joinpath(*PurePosixPath(relative).parts)
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                target.write_bytes(content)
            paths.assignment.write_bytes(assignment_bytes)
            _make_read_only(paths.source)
            _make_read_only(paths.input)
            paths.assignment.chmod(0o440)
            immutable = _hash_tree(paths.root, ("source", "input", "assignment.json"))
            return PreparedWorkspace(
                project_id,
                activity_id,
                run_id,
                source_commit,
                paths,
                hashlib.sha256(assignment_bytes).hexdigest(),
                tuple(sorted(immutable.items())),
                self.isolation_executable,
                self.root,
            )
        except BaseException:
            # Preserve an interrupted/failed workspace for diagnosis; callers choose cleanup.
            raise

    @staticmethod
    def _checkout(repository: Path, commit: str, destination: Path) -> None:
        try:
            exact = ReadOnlyGitRepository(repository).exact_commit(commit)
        except GitRepositoryError as error:
            raise WorkspaceError("invalid_source", str(error)) from error
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_OPTIONAL_LOCKS": "0",
            }
        )
        commands = (
            ("git", "clone", "--quiet", "--local", "--no-hardlinks", "--no-checkout", str(repository), str(destination)),
            ("git", "-C", str(destination), "checkout", "--quiet", "--detach", exact),
            ("git", "-C", str(destination), "remote", "remove", "origin"),
        )
        for command in commands:
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
                check=False,
            )
            if result.returncode != 0:
                message = result.stderr.decode("utf-8", errors="replace").strip()
                raise WorkspaceError("source_checkout_failed", f"cannot prepare exact source: {message}")


def _validate_inputs(inputs: Mapping[str, bytes]) -> dict[str, bytes]:
    if not isinstance(inputs, Mapping):
        raise WorkspaceError("invalid_input", "assigned inputs must be a mapping")
    result: dict[str, bytes] = {}
    total = 0
    for relative, content in inputs.items():
        path = _relative_path(relative, "input path")
        if not isinstance(content, bytes) or len(content) > MAX_INPUT_BYTES:
            raise WorkspaceError("invalid_input", "assigned input is not bounded bytes")
        normalized = path.as_posix()
        if normalized in result:
            raise WorkspaceError("invalid_input", "assigned input path is duplicated")
        result[normalized] = content
        total += len(content)
    if total > MAX_INPUT_SET_BYTES:
        raise WorkspaceError("invalid_input", "assigned input set is too large")
    return result


def _relative_path(value: object, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise WorkspaceError("invalid_path", f"{field} is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts or not path.parts:
        raise WorkspaceError("invalid_path", f"{field} is invalid")
    return path


def _make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            raise WorkspaceError("unsafe_source", "workspace immutable inputs contain a symbolic link")
        path.chmod(0o550 if path.is_dir() else 0o440)
    root.chmod(0o550)


def _hash_tree(root: Path, names: Sequence[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in names:
        path = root / name
        if path.is_symlink() or not path.exists():
            raise WorkspaceError("forbidden_write", f"immutable workspace path is unavailable: {name}")
        candidates = (path,) if path.is_file() else tuple(path.rglob("*"))
        for candidate in candidates:
            if candidate.is_symlink():
                raise WorkspaceError("forbidden_write", "immutable workspace contains a symbolic link")
            if candidate.is_file():
                relative = candidate.relative_to(root).as_posix()
                hashes[relative] = hashlib.sha256(candidate.read_bytes()).hexdigest()
    return hashes


def _verify_writable_tree(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise WorkspaceError("unsafe_output", "writable workspace contains an unsafe entry")


def _path_chain(root: Path, leaf: Path) -> tuple[Path, ...]:
    try:
        relative = leaf.relative_to(root)
    except ValueError as error:
        raise WorkspaceError("invalid_workspace", "run workspace escapes its configured root") from error
    current = root
    values: list[Path] = []
    for part in relative.parts:
        current /= part
        values.append(current)
    return tuple(values)


def _runtime_paths(executable: Path) -> tuple[Path, ...]:
    tool_companions: tuple[Path, ...] = ()
    if executable.name == "codex":
        companion = executable.with_name("codex-code-mode-host")
        if companion.is_file() and os.access(companion, os.X_OK):
            tool_companions = (companion,)
    candidates = (
        Path("/usr"),
        Path("/bin"),
        Path("/lib"),
        Path("/lib64"),
        Path("/etc/ssl"),
        Path("/etc/resolv.conf"),
        Path("/etc/nsswitch.conf"),
        Path("/etc/passwd"),
        executable,
        *tool_companions,
    )
    result: list[Path] = []
    for path in candidates:
        if path.exists() and not any(path == existing or path.is_relative_to(existing) for existing in result):
            result.append(path)
    return tuple(result)
