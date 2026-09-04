from __future__ import annotations

import importlib.metadata
import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from maestro.project_authority import _manifest_facts
from maestro.project_manifest import (
    ProjectManifestError,
    manifest_leaf_paths,
    parse_project_manifest,
)
from support import complete_manifest, dump_manifest, without_leaf


class ProjectManifestTests(unittest.TestCase):
    @staticmethod
    def schema() -> dict:
        schema_path = Path(__file__).resolve().parents[2] / "docs/schemas/maestro-project-v1.schema.json"
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def test_complete_manifest_matches_python_and_json_schema_carriers(self) -> None:
        manifest = complete_manifest()
        parsed = parse_project_manifest(dump_manifest(manifest))
        schema = self.schema()

        self.assertEqual(parsed, manifest)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(parsed)

    def test_python_and_json_schema_agree_on_shared_closed_shape_examples(self) -> None:
        validator = Draft202012Validator(self.schema())
        rejected = []
        manifest = complete_manifest()
        manifest["unknown"] = "field"
        rejected.append(manifest)
        manifest = complete_manifest()
        manifest["schema_version"] = "1"
        rejected.append(manifest)
        manifest = complete_manifest()
        manifest["authority"]["architecture_paths"] = []
        rejected.append(manifest)
        manifest = complete_manifest()
        manifest["routing"]["worker_routes"] = ["cloud", "cloud"]
        rejected.append(manifest)
        manifest = complete_manifest()
        manifest["operations"]["secret_references"] = ["ghp_payload"]
        rejected.append(manifest)
        manifest = complete_manifest()
        manifest["exceptions"] = {"disposition": "declared", "items": []}
        rejected.append(manifest)

        for index, value in enumerate(rejected):
            with self.subTest(index=index):
                with self.assertRaises(ProjectManifestError):
                    parse_project_manifest(dump_manifest(value))
                self.assertTrue(list(validator.iter_errors(value)))

    def test_schema_carrier_matches_python_for_utf8_paths_and_work_graph_membership(self) -> None:
        schema = self.schema()
        validator = Draft202012Validator(schema)
        rejected: dict[str, dict] = {}

        manifest = complete_manifest()
        manifest["identity"]["name"] = "é" * 257
        rejected["over_512_utf8_bytes"] = manifest
        for name, path in (
            ("absolute_path", "/absolute"),
            ("traversal_path", "../escape"),
            ("dot_git_component", ".git/config"),
        ):
            manifest = complete_manifest()
            manifest["authority"]["handoff_path"] = path
            rejected[name] = manifest
        manifest = complete_manifest()
        manifest["authority"]["work_graph_path"] = "docs/planning/not-declared.yaml"
        rejected["work_graph_not_in_plan_paths"] = manifest

        for name, value in rejected.items():
            with self.subTest(name=name):
                with self.assertRaises(ProjectManifestError):
                    parse_project_manifest(dump_manifest(value))

        # These two constraints are Python semantic rules because plain Draft
        # 2020-12 cannot express them faithfully. The repository-path rules
        # are schema-expressible and must agree across both carriers.
        self.assertTrue(validator.is_valid(rejected["over_512_utf8_bytes"]))
        self.assertTrue(validator.is_valid(rejected["work_graph_not_in_plan_paths"]))
        self.assertFalse(validator.is_valid(rejected["absolute_path"]))
        self.assertFalse(validator.is_valid(rejected["traversal_path"]))
        self.assertFalse(validator.is_valid(rejected["dot_git_component"]))

        accepted = []
        manifest = complete_manifest()
        manifest["identity"]["name"] = "a" * 512
        accepted.append(manifest)
        manifest = complete_manifest()
        manifest["identity"]["name"] = "é" * 256
        accepted.append(manifest)
        manifest = complete_manifest()
        manifest["identity"]["name"] = "a" * 510 + "é"
        accepted.append(manifest)
        manifest = complete_manifest()
        manifest["authority"]["handoff_path"] = "docs/.hidden/current.md"
        accepted.append(manifest)

        for index, value in enumerate(accepted):
            with self.subTest(accepted=index):
                parsed = parse_project_manifest(dump_manifest(value))
                validator.validate(parsed)

    def test_imported_pyyaml_version_satisfies_packet_range(self) -> None:
        imported_version = yaml.__version__
        distribution_version = importlib.metadata.version("PyYAML")
        self.assertEqual(imported_version, distribution_version)
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[^0-9].*)?", imported_version)
        self.assertIsNotNone(match, f"cannot evaluate imported PyYAML version {imported_version!r}")
        numeric = tuple(int(part) for part in match.groups())
        self.assertGreaterEqual(
            numeric,
            (6, 0, 2),
            f"imported PyYAML {imported_version} does not satisfy required range >=6.0.2,<7",
        )
        self.assertLess(
            numeric,
            (7, 0, 0),
            f"imported PyYAML {imported_version} does not satisfy required range >=6.0.2,<7",
        )

    def test_acceptance_authority_enum_agrees_across_schema_and_python(self) -> None:
        schema = self.schema()
        validator = Draft202012Validator(schema)
        authority_schema = schema["properties"]["delivery"]["properties"]["acceptance_authority"]
        self.assertEqual(authority_schema, {"enum": ["project-architect", "owner"]})

        for authority in ("project-architect", "owner"):
            manifest = complete_manifest()
            manifest["delivery"]["acceptance_authority"] = authority
            with self.subTest(accepted=authority):
                self.assertEqual(
                    parse_project_manifest(dump_manifest(manifest))["delivery"]["acceptance_authority"],
                    authority,
                )
                validator.validate(manifest)

        rejected = (
            "unrecognized-approver",
            "",
            "Project-Architect",
            " project-architect",
            "project-architect ",
            None,
            False,
            1,
            ["project-architect"],
            {"authority": "project-architect"},
        )
        for authority in rejected:
            manifest = complete_manifest()
            manifest["delivery"]["acceptance_authority"] = authority
            with self.subTest(rejected=authority):
                with self.assertRaises(ProjectManifestError):
                    parse_project_manifest(dump_manifest(manifest))
                self.assertFalse(validator.is_valid(manifest))

    def test_every_missing_required_leaf_has_one_exact_missing_fact(self) -> None:
        for dotted in manifest_leaf_paths():
            with self.subTest(dotted=dotted):
                parsed = parse_project_manifest(dump_manifest(without_leaf(complete_manifest(), dotted)))
                facts = _manifest_facts(parsed, "owner/example-project")
                matching = [fact for fact in facts if fact.dotted_path == dotted]
                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0].status, "missing")
                self.assertIn("absent", matching[0].reason)

    def test_unknown_duplicate_alias_anchor_merge_tag_and_invalid_type_are_rejected(self) -> None:
        samples = {
            "unknown": dump_manifest({**complete_manifest(), "unknown": "x"}),
            "duplicate": b"schema_version: 1\nschema_version: 1\n",
            "anchor_alias": b"schema_version: 1\nidentity: &identity {}\nauthority: *identity\n",
            "merge": b"schema_version: 1\nidentity: &identity {}\nauthority:\n  <<: *identity\n",
            "tag": b"schema_version: !custom 1\n",
            "invalid_type": dump_manifest({**complete_manifest(), "schema_version": "1"}),
            "multiple_documents": b"schema_version: 1\n---\nschema_version: 1\n",
            "non_string_key": b"schema_version: 1\nidentity:\n  1: value\n",
        }
        for name, raw in samples.items():
            with self.subTest(name=name), self.assertRaises(ProjectManifestError):
                parse_project_manifest(raw)

    def test_paths_empty_required_lists_duplicates_and_exceptions_are_rejected(self) -> None:
        cases = []
        for value in ("/absolute", "../escape", ".git/config", "a\\b", "a//b", "a/./b"):
            manifest = complete_manifest()
            manifest["authority"]["handoff_path"] = value
            cases.append(manifest)
        for field in ("architecture_paths", "plan_paths"):
            manifest = complete_manifest()
            manifest["authority"][field] = []
            cases.append(manifest)
        manifest = complete_manifest()
        manifest["routing"]["worker_routes"] = ["cloud", "cloud"]
        cases.append(manifest)
        manifest = complete_manifest()
        manifest["authority"]["work_graph_path"] = "docs/planning/other.yaml"
        cases.append(manifest)
        manifest = complete_manifest()
        manifest["exceptions"] = {"disposition": "none", "items": ["unexpected"]}
        cases.append(manifest)
        manifest = complete_manifest()
        manifest["exceptions"] = {"disposition": "declared", "items": []}
        cases.append(manifest)

        for index, manifest in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ProjectManifestError):
                parse_project_manifest(dump_manifest(manifest))

    def test_secret_reference_grammar_accepts_identifiers_and_rejects_payloads(self) -> None:
        accepted = complete_manifest()
        accepted["operations"]["secret_references"] = ["GITHUB_APP_PRIVATE_KEY", "SLACK_BOT_TOKEN"]
        self.assertEqual(
            parse_project_manifest(dump_manifest(accepted))["operations"]["secret_references"],
            ["GITHUB_APP_PRIVATE_KEY", "SLACK_BOT_TOKEN"],
        )

        rejected = [
            ["ghp_0123456789abcdef"],
            ["xoxb-0123456789"],
            ["-----BEGIN PRIVATE KEY-----"],
            ["AB"],
            ["A" * 129],
            ["line\nbreak"],
            ["CONTROL\x07VALUE"],
            [{"name": "TOKEN"}],
        ]
        for references in rejected:
            manifest = complete_manifest()
            manifest["operations"]["secret_references"] = references
            with self.subTest(references=references), self.assertRaises(ProjectManifestError):
                parse_project_manifest(dump_manifest(manifest))

        manifest = complete_manifest()
        manifest["operations"]["secret_values"] = ["anything"]
        with self.assertRaises(ProjectManifestError):
            parse_project_manifest(dump_manifest(manifest))

    def test_surrounding_whitespace_control_and_overlength_scalars_are_rejected(self) -> None:
        for value in (" padded", "padded ", "bad\x00value", "é" * 257):
            manifest = complete_manifest()
            manifest["identity"]["name"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ProjectManifestError):
                parse_project_manifest(dump_manifest(manifest))


if __name__ == "__main__":
    unittest.main()
