#!/usr/bin/env python3
"""Automatic upgrade of the installed Maestro service to an exact passed revision.

A revision is installable only when it is a full commit on ``master`` that
carries a ``passed/*`` tag. The upgrade backs up the installed package,
launchers, deployment files, configuration and database, replaces only code,
runs post-install smoke checks and restores the backup if any check fails.
Configuration and credentials are never rewritten.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

PASSED_TAG_PREFIX = "passed/"
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_HELPER_VALUE = re.compile(r'^(CONFIG|PROFILE_ROOT|SERVICE_USER) = (?:Path\()?"([^"]+)"\)?$', re.MULTILINE)


class UpgradeError(RuntimeError):
    pass


@dataclass(frozen=True)
class UpgradeTarget:
    """Installed locations, relative to ``root`` so tests can use an isolated tree."""

    root: Path = Path("/")
    venv: Path = Path("/opt/maestro")
    config: Path = Path("/etc/maestro/agents.toml")
    launcher: Path = Path("/usr/local/libexec/maestro-agent-egress")
    runner: Path = Path("/usr/local/libexec/maestro-agent-egress-run")
    data_dir: Path = Path("/var/lib/maestro")
    owner_token: Path | None = None
    service_unit: str = "maestro.service"
    port: int = 8787

    def under(self, path: Path) -> Path:
        return self.root / path.relative_to("/") if self.root != Path("/") else path

    @property
    def deploy_dir(self) -> Path:
        return self.under(self.venv / "share/maestro/deploy")

    @property
    def revision_file(self) -> Path:
        return self.under(self.venv / "share/maestro/INSTALLED_REVISION")

    @property
    def backup_root(self) -> Path:
        return self.under(self.data_dir / "upgrades")

    def database_files(self) -> tuple[Path, ...]:
        base = self.under(self.data_dir / "maestro.sqlite3")
        return tuple(base.with_name(base.name + suffix) for suffix in ("", "-wal", "-shm"))


@dataclass
class Effects:
    """Every host action, injectable so the upgrade can be proved on an isolated tree."""

    run: Callable[[Sequence[str]], tuple[int, str]]
    install_package: Callable[[Path], None]
    package_dir: Callable[[], Path]
    http_status: Callable[[str, str | None], int]
    now: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep


@dataclass
class Receipt:
    revision: str
    previous_revision: str | None
    outcome: str = "started"
    checks: list[dict[str, str]] = field(default_factory=list)
    backup: str = ""
    started: str = ""
    finished: str = ""

    def check(self, name: str, ok: bool, detail: str) -> bool:
        self.checks.append({"check": name, "status": "pass" if ok else "fail", "detail": detail})
        return ok


def _git(repository: Path, *arguments: str) -> tuple[int, str]:
    done = subprocess.run(
        ["git", "-C", str(repository), *arguments], capture_output=True, text=True, check=False
    )
    return done.returncode, (done.stdout or done.stderr).strip()


def verify_passed_revision(repository: Path, revision: str, *, branch: str = "master") -> None:
    """Refuse anything that is not an exact commit on master carrying a passed tag."""
    if not _COMMIT.fullmatch(revision):
        raise UpgradeError("revision must be one full lowercase commit hash")
    code, resolved = _git(repository, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if code != 0 or resolved != revision:
        raise UpgradeError("revision does not resolve to that exact commit")
    code, _ = _git(repository, "merge-base", "--is-ancestor", revision, f"refs/remotes/origin/{branch}")
    if code != 0:
        code, _ = _git(repository, "merge-base", "--is-ancestor", revision, f"refs/heads/{branch}")
    if code != 0:
        raise UpgradeError(f"revision is not on {branch}")
    code, tags = _git(repository, "tag", "--points-at", revision, "--list", f"{PASSED_TAG_PREFIX}*")
    if code != 0 or not tags.strip():
        raise UpgradeError(f"revision carries no {PASSED_TAG_PREFIX}* tag; it has not passed")


def latest_passed_revision(repository: Path, *, branch: str = "master") -> str | None:
    """Newest passed revision by ancestry on master; the timer installs this one."""
    code, listing = _git(
        repository, "tag", "--list", f"{PASSED_TAG_PREFIX}*", "--format=%(objectname) %(*objectname)"
    )
    if code != 0:
        return None
    valid: set[str] = set()
    for line in listing.splitlines():
        names = line.split()
        commit = names[-1] if names else ""
        try:
            verify_passed_revision(repository, commit, branch=branch)
        except UpgradeError:
            continue
        valid.add(commit)
    if not valid:
        return None
    for ref in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        code, order = _git(repository, "rev-list", "--topo-order", ref)
        if code == 0:
            for commit in order.splitlines():
                if commit in valid:
                    return commit
    return None


def installed_revision(target: UpgradeTarget) -> str | None:
    try:
        value = target.revision_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value if _COMMIT.fullmatch(value) else None


def _export(repository: Path, revision: str, destination: Path) -> Path:
    archive = subprocess.run(
        ["git", "-C", str(repository), "archive", revision, "services/maestro"],
        capture_output=True, check=False,
    )
    if archive.returncode != 0:
        raise UpgradeError("cannot export the exact revision")
    unpacked = subprocess.run(
        ["tar", "-x", "-C", str(destination)], input=archive.stdout, capture_output=True, check=False
    )
    if unpacked.returncode != 0:
        raise UpgradeError("cannot unpack the exported revision")
    return destination / "services/maestro"


def _backup(target: UpgradeTarget, effects: Effects, backup: Path) -> None:
    backup.mkdir(parents=True, mode=0o700)
    package = effects.package_dir()
    shutil.copytree(package, backup / "package", symlinks=True)
    if target.deploy_dir.is_dir():
        shutil.copytree(target.deploy_dir, backup / "deploy", symlinks=True)
    for name, path in (
        ("config", target.under(target.config)),
        ("launcher", target.under(target.launcher)),
        ("runner", target.under(target.runner)),
    ):
        if path.is_file():
            shutil.copy2(path, backup / name)
    for path in target.database_files():
        if path.is_file():
            shutil.copy2(path, backup / path.name)


def _restore(target: UpgradeTarget, effects: Effects, backup: Path) -> None:
    package = effects.package_dir()
    if (backup / "package").is_dir():
        shutil.rmtree(package, ignore_errors=True)
        shutil.copytree(backup / "package", package, symlinks=True)
    if (backup / "deploy").is_dir():
        shutil.rmtree(target.deploy_dir, ignore_errors=True)
        shutil.copytree(backup / "deploy", target.deploy_dir, symlinks=True)
    for name, path in (
        ("config", target.under(target.config)),
        ("launcher", target.under(target.launcher)),
        ("runner", target.under(target.runner)),
    ):
        if (backup / name).is_file():
            shutil.copy2(backup / name, path)
    for path in target.database_files():
        if (backup / path.name).is_file():
            shutil.copy2(backup / path.name, path)


def _render_launchers(target: UpgradeTarget) -> None:
    """Re-render both egress helpers from the new template, keeping installed values."""
    template_path = target.deploy_dir / "maestro-agent-egress"
    launcher = target.under(target.launcher)
    if not template_path.is_file() or not launcher.is_file():
        return
    installed = dict(_HELPER_VALUE.findall(launcher.read_text(encoding="utf-8")))
    if set(installed) != {"CONFIG", "PROFILE_ROOT", "SERVICE_USER"}:
        raise UpgradeError("installed launcher values could not be read; refusing to guess")
    text = (
        template_path.read_text(encoding="utf-8")
        .replace("@CONFIG_FILE@", installed["CONFIG"])
        .replace("@DATA_DIR@", installed["PROFILE_ROOT"])
        .replace("@SERVICE_USER@", installed["SERVICE_USER"])
    )
    if "@" in text.replace("@dataclass", ""):
        raise UpgradeError("launcher template has an unresolved value")
    for path in (launcher, target.under(target.runner)):
        temporary = path.with_name(path.name + ".new")
        temporary.write_text(text, encoding="utf-8")
        temporary.chmod(0o755)
        temporary.replace(path)


def _smoke(target: UpgradeTarget, effects: Effects, receipt: Receipt, extra: Sequence[Sequence[str]]) -> bool:
    ok = True
    deadline = effects.now() + 60
    active = False
    while effects.now() < deadline:
        code, state = effects.run(["systemctl", "is-active", target.service_unit])
        if code == 0 and state.strip() == "active":
            active = True
            break
        effects.sleep(2)
    ok &= receipt.check("service_active", active, target.service_unit)
    token = None
    if target.owner_token is not None:
        try:
            token = target.owner_token.read_text(encoding="utf-8").strip()
        except OSError:
            ok &= receipt.check("owner_token", False, "Owner credential unreadable")
    url = f"http://127.0.0.1:{target.port}/api/v1/workspace"

    def answer(credential: str | None) -> int:
        """Wait for the service to listen; an active unit is not yet an answering service."""
        deadline = effects.now() + 60
        status = effects.http_status(url, credential)
        while status == 0 and effects.now() < deadline:
            effects.sleep(2)
            status = effects.http_status(url, credential)
        return status

    if token is not None:
        status = answer(token)
        ok &= receipt.check("authenticated_read", status == 200, f"HTTP {status}")
    refused = answer(None)
    ok &= receipt.check("unauthenticated_refused", refused == 401, f"HTTP {refused}")
    for command in extra:
        code, output = effects.run(command)
        ok &= receipt.check("smoke:" + Path(command[0]).name, code == 0, output.strip().splitlines()[-1][:120] if output.strip() else f"exit {code}")
    return ok


def upgrade(
    repository: Path,
    revision: str,
    target: UpgradeTarget,
    effects: Effects,
    *,
    smoke_commands: Sequence[Sequence[str]] = (),
) -> Receipt:
    verify_passed_revision(repository, revision)
    receipt = Receipt(revision, installed_revision(target))
    receipt.started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if receipt.previous_revision == revision:
        receipt.outcome = "already_installed"
        return receipt
    backup = target.backup_root / time.strftime("%Y%m%dT%H%M%S")
    receipt.backup = str(backup)
    workspace = Path(tempfile.mkdtemp(prefix="maestro-upgrade-"))
    try:
        exported = _export(repository, revision, workspace)
        _backup(target, effects, backup)
        effects.run(["systemctl", "stop", target.service_unit])
        try:
            effects.install_package(exported)
            _render_launchers(target)
            code, output = effects.run(["systemctl", "start", target.service_unit])
            healthy = receipt.check("service_start", code == 0, output.strip()[:120] or "started")
            healthy = _smoke(target, effects, receipt, smoke_commands) and healthy
        except (UpgradeError, OSError) as error:
            receipt.check("install", False, str(error)[:200])
            healthy = False
        if healthy:
            target.revision_file.parent.mkdir(parents=True, exist_ok=True)
            target.revision_file.write_text(revision + "\n", encoding="utf-8")
            receipt.outcome = "upgraded"
        else:
            effects.run(["systemctl", "stop", target.service_unit])
            _restore(target, effects, backup)
            effects.run(["systemctl", "start", target.service_unit])
            restored = _smoke(target, effects, Receipt(revision, None), ())
            receipt.outcome = "rolled_back" if restored else "rollback_failed"
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
        receipt.finished = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if backup.is_dir():
            (backup / "receipt.json").write_text(json.dumps(receipt.__dict__, indent=2), encoding="utf-8")
    return receipt


def host_effects(target: UpgradeTarget) -> Effects:
    def run(command: Sequence[str]) -> tuple[int, str]:
        try:
            done = subprocess.run(list(command), capture_output=True, text=True, timeout=300, check=False)
        except (OSError, subprocess.SubprocessError) as error:
            return 127, str(error)
        return done.returncode, done.stdout or done.stderr

    def install_package(source: Path) -> None:
        code, output = run([str(target.venv / "bin/python"), "-m", "pip", "install", "--no-deps", "--force-reinstall", str(source)])
        if code != 0:
            raise UpgradeError("package install failed: " + output.strip().splitlines()[-1][:160])

    def package_dir() -> Path:
        code, output = run([str(target.venv / "bin/python"), "-c", "import maestro,os;print(os.path.dirname(maestro.__file__))"])
        if code != 0:
            raise UpgradeError("cannot locate the installed package")
        return Path(output.strip().splitlines()[-1])

    def http_status(url: str, token: str | None) -> int:
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"} if token else {})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code
        except OSError:
            return 0

    return Effects(run, install_package, package_dir, http_status)


def install_trigger(target: UpgradeTarget, repository: Path, url: str | None) -> int:
    """Mirror the source repository and enable the timer that installs passed revisions."""
    if not url:
        raise UpgradeError("--source-url is required")
    if target.owner_token is None:
        raise UpgradeError("--owner-token is required")
    if not repository.exists():
        done = subprocess.run(["git", "clone", "--quiet", "--mirror", url, str(repository)], check=False)
        if done.returncode != 0:
            raise UpgradeError("cannot mirror the source repository")
    deploy = Path(__file__).resolve().parent
    values = {
        "@PYTHON@": str(target.venv / "bin/python"),
        "@DEPLOY_DIR@": str(deploy),
        "@SOURCE@": str(repository),
        "@OWNER_TOKEN@": str(target.owner_token),
        "@PORT@": str(target.port),
    }
    for name in ("maestro-upgrade.service", "maestro-upgrade.timer"):
        text = (deploy / name).read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace(key, value)
        if "@" in text:
            raise UpgradeError(f"{name} has an unresolved value")
        Path("/etc/systemd/system", name).write_text(text, encoding="utf-8")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "--now", "maestro-upgrade.timer"], check=True)
    print("Maestro upgrade timer enabled")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upgrade the installed Maestro service to a passed revision")
    parser.add_argument("command", choices=("upgrade", "watch", "install-trigger"))
    parser.add_argument("--source-repository", type=Path, required=True)
    parser.add_argument("--source-url", help="repository to mirror; install-trigger only")
    parser.add_argument("--revision", help="full commit; required for upgrade")
    parser.add_argument("--owner-token", type=Path)
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--smoke", action="append", default=[], metavar="COMMAND", help="extra smoke command (space separated)")
    arguments = parser.parse_args(argv)
    target = UpgradeTarget(owner_token=arguments.owner_token, port=arguments.port)
    try:
        repository = arguments.source_repository
        if arguments.command == "install-trigger":
            return install_trigger(target, repository, arguments.source_url)
        if arguments.command == "watch":
            _git(
                repository, "fetch", "--quiet", "--force", "origin",
                "+refs/heads/master:refs/heads/master", "+refs/tags/*:refs/tags/*",
            )
            revision = latest_passed_revision(repository)
            if revision is None:
                print("no passed revision to install")
                return 0
        else:
            if not arguments.revision:
                raise UpgradeError("--revision is required")
            revision = arguments.revision
        receipt = upgrade(
            repository, revision, target, host_effects(target),
            smoke_commands=[command.split() for command in arguments.smoke],
        )
    except UpgradeError as error:
        print(f"Maestro upgrade refused: {error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt.__dict__, indent=2))
    return {"upgraded": 0, "already_installed": 0, "rolled_back": 1}.get(receipt.outcome, 2)


if __name__ == "__main__":
    raise SystemExit(main())
