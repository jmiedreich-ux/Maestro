from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

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

        self.assertEqual(parsed, manifest)
        Draft202012Validator(self.schema()).validate(parsed)

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
