"""Service-owned GitHub destination provider for registration.

The provider alone holds the App private key and installation tokens. It
verifies the bound App and repository, resolves the selected source, reads
project sources at an exact commit, and publishes a candidate or receipt in one
commit with an expected-head check. It never force-pushes, creates a branch,
changes protection, or hands a token to an agent.
"""

from __future__ import annotations

import base64
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
_TOKEN_LIFETIME = 45 * 60


class DestinationError(ValueError):
    """A specific intake or publication problem; never carries a credential."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class RepositoryProfile:
    """The non-secret operator configuration for one repository binding."""

    name: str
    repositories: tuple[str, ...]
    branch_patterns: tuple[str, ...]
    credential_profile: str
    app_id: int
    installation_id: int
    app_slug: str
    api_base_url: str = "https://api.github.com"

    def snapshot(self, binding: str) -> dict[str, object]:
        """The immutable effective-profile snapshot saved with an attempt."""
        content = {
            "binding": binding,
            "profile": self.name,
            "api_base_url": self.api_base_url,
            "app_id": self.app_id,
            "installation_id": self.installation_id,
            "app_slug": self.app_slug,
            "repositories": list(self.repositories),
            "branch_patterns": list(self.branch_patterns),
            "credential_profile": self.credential_profile,
        }
        digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
        return {**content, "configuration_sha256": digest}


def parse_repository_configuration(tables: Mapping[str, object]) -> tuple[dict[str, RepositoryProfile], dict[str, tuple[str, str]]]:
    """Profiles by name and bindings (repository, profile) by binding name."""
    profiles: dict[str, RepositoryProfile] = {}
    raw_profiles = tables.get("repositories", {})
    raw_bindings = tables.get("repository_bindings", {})
    if not isinstance(raw_profiles, Mapping) or not isinstance(raw_bindings, Mapping):
        raise DestinationError("repository_configuration_invalid", "repositories and repository_bindings must be tables")
    for name, value in raw_profiles.items():
        if not isinstance(value, Mapping):
            raise DestinationError("repository_configuration_invalid", f"repositories.{name} must be a table")
        github = value.get("github")
        if not isinstance(github, Mapping):
            raise DestinationError("repository_configuration_invalid", f"repositories.{name}.github is required")
        try:
            app_id, installation_id = github["app_id"], github["installation_id"]
            slug = github["app_slug"]
            repositories = tuple(value["allowed_repositories"])
            patterns = tuple(value["allowed_branch_patterns"])
            credential = value["credential_profile"]
        except KeyError as error:
            raise DestinationError("repository_configuration_invalid", f"repositories.{name} is missing {error.args[0]}") from error
        if (
            isinstance(app_id, bool) or not isinstance(app_id, int) or app_id <= 0
            or isinstance(installation_id, bool) or not isinstance(installation_id, int) or installation_id <= 0
            or not isinstance(slug, str) or not slug
            or not repositories or not patterns
            or not all(isinstance(r, str) and _REPOSITORY.match(r) for r in repositories)
            or not all(isinstance(p, str) and p for p in patterns)
            or not isinstance(credential, str) or not credential
        ):
            raise DestinationError("repository_configuration_invalid", f"repositories.{name} has an invalid value")
        profiles[name] = RepositoryProfile(
            name, repositories, patterns, credential, app_id, installation_id, slug,
            str(github.get("api_base_url", "https://api.github.com")).rstrip("/"),
        )
    bindings: dict[str, tuple[str, str]] = {}
    for name, value in raw_bindings.items():
        if not isinstance(value, Mapping) or not isinstance(value.get("repository"), str) or not isinstance(value.get("profile"), str):
            raise DestinationError("repository_configuration_invalid", f"repository_bindings.{name} needs repository and profile")
        bindings[name] = (value["repository"], value["profile"])
    return profiles, bindings


def bind_repository(repository: str, profiles: Mapping[str, RepositoryProfile], bindings: Mapping[str, tuple[str, str]]) -> tuple[str, RepositoryProfile]:
    """Exactly one configured binding for the normalized repository, or a setup error."""
    if not isinstance(repository, str) or not _REPOSITORY.match(repository):
        raise DestinationError("invalid_repository", "the repository must be written as owner/name")
    matches = [(name, profile) for name, (bound, profile) in bindings.items() if bound.lower() == repository.lower()]
    if not matches:
        raise DestinationError("binding_missing", f"no repository binding is configured for {repository}")
    if len(matches) > 1:
        raise DestinationError("binding_ambiguous", f"more than one repository binding is configured for {repository}")
    name, profile_name = matches[0][0], bindings[matches[0][0]][1]
    profile = profiles.get(profile_name)
    if profile is None:
        raise DestinationError("binding_profile_unknown", f"binding {name} names an unknown repository profile")
    if not any(repository.lower() == r.lower() for r in profile.repositories):
        raise DestinationError("repository_not_allowed", f"{repository} is not in the profile's repository allowlist")
    return name, profile


Transport = Callable[[str, str, Mapping[str, str], "bytes | None"], "tuple[int, bytes]"]


def _urllib_transport(method: str, url: str, headers: Mapping[str, str], body: bytes | None) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, method=method, headers=dict(headers))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise DestinationError("github_unreachable", "GitHub could not be reached") from error


class GitHubDestination:
    """Authorized reads and writes for one repository profile."""

    def __init__(self, profile: RepositoryProfile, private_key_pem: str, transport: Transport = _urllib_transport, clock: Callable[[], float] = time.time) -> None:
        self.profile = profile
        self._key = private_key_pem
        self._transport = transport
        self._clock = clock
        self._token: tuple[str, float] | None = None

    # -- authorization --------------------------------------------------------

    def _jwt(self) -> str:
        import jwt

        now = int(self._clock())
        return jwt.encode({"iat": now - 60, "exp": now + 300, "iss": str(self.profile.app_id)}, self._key, algorithm="RS256")

    def _call(self, method: str, path: str, *, bearer: str, body: object | None = None, accept: str = "application/vnd.github+json") -> tuple[int, Any]:
        headers = {"Authorization": f"Bearer {bearer}", "Accept": accept, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "maestro-registration"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        status, raw = self._transport(method, f"{self.profile.api_base_url}{path}", headers, data)
        if accept != "application/vnd.github+json" and status == 200:
            return status, raw
        try:
            return status, json.loads(raw) if raw else None
        except ValueError:
            return status, None

    def token(self) -> str:
        if self._token is not None and self._clock() < self._token[1]:
            return self._token[0]
        status, value = self._call("POST", f"/app/installations/{self.profile.installation_id}/access_tokens", bearer=self._jwt())
        if status != 201 or not isinstance(value, Mapping) or not isinstance(value.get("token"), str):
            raise DestinationError("github_authorization_failed", "the GitHub App installation token could not be created", status=status)
        self._token = (value["token"], self._clock() + _TOKEN_LIFETIME)
        return self._token[0]

    def _api(self, method: str, path: str, body: object | None = None, accept: str = "application/vnd.github+json") -> tuple[int, Any]:
        return self._call(method, path, bearer=self.token(), body=body, accept=accept)

    # -- destination checks ---------------------------------------------------

    def verify_identity(self) -> dict[str, object]:
        status, app = self._call("GET", "/app", bearer=self._jwt())
        if status != 200 or not isinstance(app, Mapping) or app.get("id") != self.profile.app_id or app.get("slug") != self.profile.app_slug:
            raise DestinationError("app_identity_mismatch", "the authenticated GitHub App does not match the configured App")
        status, installation = self._call("GET", f"/app/installations/{self.profile.installation_id}", bearer=self._jwt())
        if status != 200 or not isinstance(installation, Mapping) or installation.get("app_id") != self.profile.app_id:
            raise DestinationError("installation_mismatch", "the configured installation does not belong to the configured App")
        permissions = installation.get("permissions")
        permissions = permissions if isinstance(permissions, Mapping) else {}
        if permissions.get("contents") != "write":
            raise DestinationError("permission_missing", "the App installation lacks contents write permission")
        if permissions.get("administration") not in {"read", "write"}:
            raise DestinationError("permission_missing", "the App installation lacks administration read permission needed to check branch rules")
        return {"app_id": app["id"], "app_slug": app["slug"], "installation_id": self.profile.installation_id, "contents": permissions["contents"], "administration": permissions["administration"]}

    def default_branch(self, repository: str) -> str:
        status, value = self._api("GET", f"/repos/{repository}")
        if status == 404 or status == 403:
            raise DestinationError("repository_inaccessible", f"{repository} cannot be read with the configured App")
        if status != 200 or not isinstance(value, Mapping) or not isinstance(value.get("default_branch"), str) or not value["default_branch"]:
            raise DestinationError("repository_unverifiable", f"{repository} could not be read", status=status)
        return value["default_branch"]

    def check_publication_branch(self, repository: str, branch: str) -> dict[str, object]:
        """Direct write is allowed only to an existing, allowlisted, unprotected branch with no rules."""
        if not isinstance(branch, str) or not branch or branch.startswith(("refs/", "/")) or ".." in branch:
            raise DestinationError("invalid_publication_branch", "the publication branch must be an existing branch name without refs/heads/")
        if not any(fnmatch.fnmatchcase(branch, pattern) for pattern in self.profile.branch_patterns):
            raise DestinationError("branch_not_allowed", f"branch {branch} is not in the profile's branch allowlist")
        identity = self.verify_identity()
        quoted = urllib.parse.quote(branch, safe="")
        status, value = self._api("GET", f"/repos/{repository}/branches/{quoted}")
        if status == 404:
            raise DestinationError("branch_missing", f"publication branch {branch} does not exist; no branch is created")
        if status != 200 or not isinstance(value, Mapping):
            raise DestinationError("branch_unverifiable", "the publication branch could not be read", status=status)
        if value.get("protected"):
            raise DestinationError("branch_protected", f"branch {branch} is protected; direct writes are not authorized")
        status, rules = self._api("GET", f"/repos/{repository}/rules/branches/{quoted}")
        if status != 200 or not isinstance(rules, list):
            raise DestinationError("branch_rules_unverifiable", "the rules for the publication branch could not be read", status=status)
        if rules:
            raise DestinationError("branch_ruleset", f"branch {branch} has active repository or organization rules; direct writes are not authorized")
        head = value.get("commit", {}).get("sha") if isinstance(value.get("commit"), Mapping) else None
        if not isinstance(head, str) or not _SHA.match(head):
            raise DestinationError("branch_unverifiable", "the publication branch head could not be read")
        evidence = json.dumps({"identity": identity, "branch": branch, "head": head, "rules": len(rules)}, sort_keys=True)
        return {"decision": "allowed", "branch": branch, "head": head, "observed_at": _now(), "evidence_sha256": hashlib.sha256(evidence.encode()).hexdigest(), **identity}

    # -- source ---------------------------------------------------------------

    def resolve_source(self, repository: str, source_ref: str | None) -> tuple[str, str, str]:
        """Return (normalized ref or commit, commit, provenance) or raise a specific error."""
        provenance = "supplied"
        if source_ref is None:
            source_ref = f"refs/heads/{self.default_branch(repository)}"
            provenance = "defaulted"
        if not isinstance(source_ref, str):
            raise DestinationError("invalid_source_ref", "source_ref must be text")
        if _SHA.match(source_ref):
            status, value = self._api("GET", f"/repos/{repository}/commits/{source_ref}")
            if status != 200 or not isinstance(value, Mapping) or value.get("sha") != source_ref:
                raise DestinationError("source_unresolved", f"commit {source_ref} was not found in {repository}")
            return source_ref, source_ref, provenance
        if not (source_ref.startswith("refs/heads/") or source_ref.startswith("refs/tags/")) or ".." in source_ref:
            raise DestinationError("invalid_source_ref", "source_ref must be a full refs/heads/ or refs/tags/ name or a 40-character commit")
        status, value = self._api("GET", f"/repos/{repository}/git/ref/{urllib.parse.quote(source_ref[5:], safe='/')}")
        if status == 404:
            raise DestinationError("source_unresolved", f"{source_ref} does not exist in {repository}")
        if status != 200 or not isinstance(value, Mapping) or not isinstance(value.get("object"), Mapping):
            raise DestinationError("source_unverifiable", f"{source_ref} could not be resolved", status=status)
        target = value["object"]
        sha, kind = target.get("sha"), target.get("type")
        for _ in range(3):
            if kind != "tag":
                break
            status, tag = self._api("GET", f"/repos/{repository}/git/tags/{sha}")
            if status != 200 or not isinstance(tag, Mapping) or not isinstance(tag.get("object"), Mapping):
                raise DestinationError("source_unverifiable", f"tag {source_ref} could not be resolved")
            sha, kind = tag["object"].get("sha"), tag["object"].get("type")
        if kind != "commit" or not isinstance(sha, str) or not _SHA.match(sha):
            raise DestinationError("source_unresolved", f"{source_ref} does not point to a commit")
        return source_ref, sha, provenance

    def read_file(self, repository: str, commit: str, path: str) -> bytes | None:
        status, value = self._api("GET", f"/repos/{repository}/contents/{urllib.parse.quote(path, safe='/')}?ref={commit}", accept="application/vnd.github.raw")
        if status == 404:
            return None
        if status != 200:
            raise DestinationError("source_unreadable", f"{path} could not be read at {commit[:12]}", status=status)
        return value if isinstance(value, bytes) else None

    def head(self, repository: str, branch: str) -> str:
        status, value = self._api("GET", f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(branch, safe='/')}")
        if status != 200 or not isinstance(value, Mapping) or not isinstance(value.get("object"), Mapping):
            raise DestinationError("branch_unverifiable", f"the head of {branch} could not be read", status=status)
        return str(value["object"]["sha"])

    def fetch_source(self, repository: str, commit: str, mirror: Path) -> None:
        """Make the exact commit available in a local repository for isolated agent checkouts."""
        mirror.parent.mkdir(parents=True, exist_ok=True)
        environment = _git_environment(self.token())
        if not (mirror / ".git" / "HEAD").exists():
            _git(["init", "-q", str(mirror)], environment)
        have = subprocess.run(["git", "-C", str(mirror), "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True, env=environment)
        if have.returncode != 0:
            _git(["-C", str(mirror), "fetch", "-q", "--no-tags", f"https://github.com/{repository}.git", commit], environment)

    # -- publication ----------------------------------------------------------

    def publish(self, repository: str, branch: str, files: Mapping[str, bytes], message: str, replaceable: frozenset[str] = frozenset()) -> str:
        """Write all files in one commit on top of the current head; refuse different content at a target path
        unless the path is listed as replaceable (the confirmation index, which each confirmation extends).

        Returns the new commit, or the head that already holds exactly these bytes.
        """
        quoted = urllib.parse.quote(branch, safe="/")
        for attempt in range(4):
            head = self.head(repository, branch)
            existing = {path: self.read_file(repository, head, path) for path in files}
            if all(existing[path] == data for path, data in files.items()):
                return head
            conflicts = [path for path, data in files.items() if existing[path] is not None and existing[path] != data and path not in replaceable]
            if conflicts:
                raise DestinationError("publication_conflict", "a target path already holds different content", paths=conflicts)
            status, commit = self._api("GET", f"/repos/{repository}/git/commits/{head}")
            if status != 200 or not isinstance(commit, Mapping):
                raise DestinationError("branch_unverifiable", "the branch head commit could not be read")
            entries = []
            for path, data in sorted(files.items()):
                status, blob = self._api("POST", f"/repos/{repository}/git/blobs", {"content": base64.b64encode(data).decode(), "encoding": "base64"})
                if status != 201 or not isinstance(blob, Mapping):
                    raise DestinationError("publication_failed", f"content for {path} could not be written", status=status)
                entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
            status, tree = self._api("POST", f"/repos/{repository}/git/trees", {"base_tree": commit["tree"]["sha"], "tree": entries})
            if status != 201 or not isinstance(tree, Mapping):
                raise DestinationError("publication_failed", "the tree could not be written", status=status)
            status, created = self._api("POST", f"/repos/{repository}/git/commits", {"message": message, "tree": tree["sha"], "parents": [head]})
            if status != 201 or not isinstance(created, Mapping):
                raise DestinationError("publication_failed", "the commit could not be written", status=status)
            status, ref = self._api("PATCH", f"/repos/{repository}/git/refs/heads/{quoted}", {"sha": created["sha"], "force": False})
            if status == 200:
                return str(created["sha"])
            if status == 422:
                time.sleep(1 + attempt)
                continue  # the branch moved: rebuild on the new head, never force
            raise DestinationError("publication_failed", "the branch could not be updated", status=status)
        raise DestinationError("publication_conflict", "the branch kept moving; publication paused")

    # -- code branches --------------------------------------------------------

    def branch_head(self, repository: str, branch: str) -> str | None:
        """The head of a branch, or None when the branch does not exist."""
        status, value = self._api("GET", f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(branch, safe='/')}")
        if status == 404:
            return None
        if status != 200 or not isinstance(value, Mapping) or not isinstance(value.get("object"), Mapping):
            raise DestinationError("branch_unverifiable", f"the head of {branch} could not be read", status=status)
        return str(value["object"]["sha"])

    def check_code_branch(self, repository: str, branch: str) -> None:
        """A work branch is created or extended only when its name is allowlisted; no force, no protected branch."""
        if not isinstance(branch, str) or not branch or branch.startswith(("refs/", "/")) or ".." in branch:
            raise DestinationError("invalid_work_branch", "the work branch name is invalid")
        if not any(fnmatch.fnmatchcase(branch, pattern) for pattern in self.profile.branch_patterns):
            raise DestinationError("branch_not_allowed", f"branch {branch} is not in the profile's branch allowlist")
        if not any(repository.lower() == r.lower() for r in self.profile.repositories):
            raise DestinationError("repository_not_allowed", f"{repository} is not in the profile's repository allowlist")

    def contains(self, repository: str, ancestor: str, descendant: str) -> bool:
        """Whether ``descendant`` is ``ancestor`` or has it in its history, as the remote reports it."""
        status, value = self._api("GET", f"/repos/{repository}/compare/{ancestor}...{descendant}")
        if status == 404:
            return False
        if status != 200 or not isinstance(value, Mapping):
            raise DestinationError("branch_unverifiable", "the remote history could not be compared", status=status)
        return value.get("status") in {"ahead", "identical"}

    def push_branch(self, repository: str, workdir: Path, branch: str, commit: str, expected_before: str | None = None) -> str:
        """Push exactly one local commit to a work branch without force and return the remote head read afterwards.

        A branch that already holds the commit is a lost acknowledgment and succeeds; a branch at some other
        commit that is not an ancestor of it is refused. When ``expected_before`` is given, the branch must still
        be at that head (a changed target is reported, never overwritten).
        """
        self.check_code_branch(repository, branch)
        remote = self.branch_head(repository, branch)
        if remote == commit:
            return commit
        if expected_before is not None and remote != expected_before:
            raise DestinationError("target_changed", f"the branch {branch} moved from {expected_before[:12]} to {(remote or 'nothing')[:12]}", remote=remote)
        environment = _git_environment(self.token())
        done = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", str(workdir), "push", "--quiet", f"https://github.com/{repository}.git", f"{commit}:refs/heads/{branch}"],
            capture_output=True, text=True, env=environment,
        )
        if done.returncode != 0:
            raise DestinationError("push_failed", "the work branch could not be pushed", detail=(done.stderr.strip().splitlines() or [""])[-1][:300])
        head = self.branch_head(repository, branch)
        if head != commit:
            raise DestinationError("push_unverified", "the remote branch does not hold the pushed commit", remote=head)
        return head

    def verify_files(self, repository: str, commit: str, files: Mapping[str, bytes]) -> None:
        status, value = self._api("GET", f"/repos/{repository}/commits/{commit}")
        if status != 200:
            raise DestinationError("publication_unverified", "the published commit was not found on GitHub")
        for path, data in files.items():
            remote = self.read_file(repository, commit, path)
            if remote != data:
                raise DestinationError("publication_unverified", f"{path} does not match the published bytes")

    def commit_paths(self, repository: str, commit: str) -> tuple[str, ...]:
        status, value = self._api("GET", f"/repos/{repository}/commits/{commit}")
        if status != 200 or not isinstance(value, Mapping):
            raise DestinationError("publication_unverified", "the published commit was not found on GitHub")
        return tuple(str(f["filename"]) for f in value.get("files", []) if isinstance(f, Mapping))


def _git_environment(token: str) -> dict[str, str]:
    header = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": os.environ.get("HOME", "/tmp"),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
        "GIT_CONFIG_VALUE_0": f"Authorization: Basic {header}",
    }


def _git(arguments: list[str], environment: Mapping[str, str]) -> None:
    done = subprocess.run(["git", *arguments], capture_output=True, text=True, env=dict(environment))
    if done.returncode != 0:
        raise DestinationError("source_fetch_failed", "the source commit could not be fetched", detail=done.stderr.strip().splitlines()[-1:] or [""])


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
