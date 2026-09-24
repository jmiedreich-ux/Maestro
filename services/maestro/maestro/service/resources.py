"""Resolution of immutable, installation-owned process schema bundles."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


_REFERENCE = re.compile(r"[a-z][a-z0-9-]*@[1-9][0-9]*\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class ProcessResourceError(ValueError):
    """A typed failure to resolve or verify an installed process resource."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class BundleSnapshot:
    reference: str
    definition: str
    hashes: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "reference": self.reference,
            "definition": self.definition,
            "hashes": dict(self.hashes),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BundleSnapshot":
        try:
            reference = value["reference"]
            definition = value["definition"]
            hashes = value["hashes"]
        except (KeyError, TypeError) as error:
            raise ProcessResourceError("invalid_snapshot", "bundle snapshot is invalid") from error
        if not isinstance(reference, str) or _REFERENCE.fullmatch(reference) is None:
            raise ProcessResourceError("invalid_snapshot", "bundle snapshot reference is invalid")
        if not isinstance(definition, str) or not definition:
            raise ProcessResourceError("invalid_snapshot", "bundle definition is invalid")
        if not isinstance(hashes, Mapping) or not hashes:
            raise ProcessResourceError("invalid_snapshot", "bundle hashes are invalid")
        normalized: list[tuple[str, str]] = []
        for path, digest in hashes.items():
            if not isinstance(path, str) or not _safe_relative(path):
                raise ProcessResourceError("invalid_snapshot", "bundle hash path is invalid")
            if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
                raise ProcessResourceError("invalid_snapshot", "bundle hash is invalid")
            normalized.append((path, digest))
        return cls(reference, definition, tuple(sorted(normalized)))


@dataclass(frozen=True)
class ResolvedBundle:
    snapshot: BundleSnapshot
    schema: Mapping[str, Any]


class InstalledSchemaResources:
    """Resolve only bundles declared by Maestro's packaged registry."""

    def __init__(self, installation_root: Path | None = None) -> None:
        # The active virtual environment is the installed Maestro root
        # (`/opt/maestro` in production). Tests pass an isolated installed root.
        self.installation_root = Path(installation_root or os.environ.get("MAESTRO_INSTALLATION_ROOT") or sys.prefix)
        self._registry = self._load_registry()

    def resolve(self, reference: str) -> ResolvedBundle:
        if not isinstance(reference, str) or _REFERENCE.fullmatch(reference) is None:
            raise ProcessResourceError("unsupported_bundle", "schema bundle reference is invalid")
        entry = self._registry.get(reference)
        if entry is None:
            raise ProcessResourceError(
                "unsupported_bundle", f"schema bundle is not supported: {reference}", reference=reference
            )
        bundle_dir = self.installation_root.joinpath(*PurePosixPath(entry["path"]).parts)
        hashes: list[tuple[str, str]] = []
        documents: dict[str, Mapping[str, Any]] = {}
        for relative in entry["files"]:
            path = bundle_dir.joinpath(*PurePosixPath(relative).parts)
            data = self._read_regular_file(path, reference)
            hashes.append((relative, hashlib.sha256(data).hexdigest()))
            try:
                decoded = json.loads(data)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ProcessResourceError(
                    "invalid_bundle", f"installed schema is not valid JSON: {reference}", reference=reference
                ) from error
            if not isinstance(decoded, Mapping):
                raise ProcessResourceError("invalid_bundle", "installed schema must be an object")
            documents[relative] = decoded
        for relative, document in documents.items():
            self._validate_references(document, relative, documents, reference)
        schema = documents[entry["schema"]]
        definition = entry["definition"]
        definitions = schema.get("$defs")
        if not isinstance(definitions, Mapping) or not isinstance(definitions.get(definition), Mapping):
            raise ProcessResourceError(
                "missing_definition",
                f"installed bundle lacks required definition: {definition}",
                reference=reference,
            )
        return ResolvedBundle(
            BundleSnapshot(reference, definition, tuple(sorted(hashes))), schema
        )

    @classmethod
    def _validate_references(
        cls,
        value: Any,
        document_path: str,
        documents: Mapping[str, Mapping[str, Any]],
        reference: str,
    ) -> None:
        if isinstance(value, Mapping):
            schema_ref = value.get("$ref")
            if schema_ref is not None:
                if not isinstance(schema_ref, str):
                    cls._unresolved_reference(reference)
                target_path, separator, fragment = schema_ref.partition("#")
                target_path = target_path or document_path
                if not _safe_relative(target_path) or target_path not in documents:
                    cls._unresolved_reference(reference)
                target: Any = documents[target_path]
                if separator:
                    if fragment and not fragment.startswith("/"):
                        cls._unresolved_reference(reference)
                    for token in filter(None, fragment.split("/")):
                        token = token.replace("~1", "/").replace("~0", "~")
                        if not isinstance(target, Mapping) or token not in target:
                            cls._unresolved_reference(reference)
                        target = target[token]
            for child in value.values():
                cls._validate_references(child, document_path, documents, reference)
        elif isinstance(value, list):
            for child in value:
                cls._validate_references(child, document_path, documents, reference)

    @staticmethod
    def _unresolved_reference(reference: str) -> None:
        raise ProcessResourceError(
            "unresolved_bundle_reference",
            f"installed schema bundle has an unresolved reference: {reference}",
            reference=reference,
        )

    def verify(self, snapshot: BundleSnapshot) -> ResolvedBundle:
        current = self.resolve(snapshot.reference)
        if current.snapshot != snapshot:
            raise ProcessResourceError(
                "bundle_changed",
                f"installed schema bundle does not match saved activity: {snapshot.reference}",
                reference=snapshot.reference,
            )
        return current

    @staticmethod
    def _read_regular_file(path: Path, reference: str) -> bytes:
        try:
            if path.is_symlink() or not path.is_file():
                raise OSError("not a regular file")
            return path.read_bytes()
        except OSError as error:
            raise ProcessResourceError(
                "missing_bundle", f"installed schema bundle is unavailable: {reference}", reference=reference
            ) from error

    @staticmethod
    def _load_registry() -> dict[str, dict[str, Any]]:
        try:
            value = json.loads(
                resources.files("maestro.service").joinpath("schema_registry.json").read_text("utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ProcessResourceError("invalid_registry", "installed schema registry is invalid") from error
        if not isinstance(value, Mapping) or set(value) != {"schema_version", "bundles"}:
            raise ProcessResourceError("invalid_registry", "installed schema registry has unknown fields")
        if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
            raise ProcessResourceError("invalid_registry", "installed schema registry version is unsupported")
        bundles = value["bundles"]
        if not isinstance(bundles, Mapping):
            raise ProcessResourceError("invalid_registry", "installed schema registry bundles are invalid")
        result: dict[str, dict[str, Any]] = {}
        for reference, entry in bundles.items():
            if not isinstance(reference, str) or _REFERENCE.fullmatch(reference) is None:
                raise ProcessResourceError("invalid_registry", "installed bundle reference is invalid")
            if not isinstance(entry, Mapping) or set(entry) != {"path", "schema", "definition", "files"}:
                raise ProcessResourceError("invalid_registry", "installed bundle entry is invalid")
            path, schema, definition, files = (
                entry["path"], entry["schema"], entry["definition"], entry["files"]
            )
            if not isinstance(path, str) or not _safe_relative(path):
                raise ProcessResourceError("invalid_registry", "installed bundle path is invalid")
            if not isinstance(schema, str) or not _safe_relative(schema):
                raise ProcessResourceError("invalid_registry", "installed schema path is invalid")
            if not isinstance(definition, str) or not definition:
                raise ProcessResourceError("invalid_registry", "installed definition is invalid")
            if (
                not isinstance(files, list)
                or not files
                or any(not isinstance(item, str) or not _safe_relative(item) for item in files)
                or schema not in files
                or len(set(files)) != len(files)
            ):
                raise ProcessResourceError("invalid_registry", "installed bundle files are invalid")
            result[reference] = dict(entry)
        return result


def _safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value
