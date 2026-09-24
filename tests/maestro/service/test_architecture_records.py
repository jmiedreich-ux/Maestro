import json
import unittest
from pathlib import Path

import jsonschema

from maestro.service import architecture_records as records

SCHEMA = json.loads((Path(__file__).resolve().parents[3] / "docs/schemas/architecture-loop.schema.json").read_text())
COMMIT = "a" * 40
PACKAGE_COMMIT = "b" * 40


def _record(kind, record_id, version=1):
    return {"schema_version": 1, "record_type": kind, "record_id": record_id, "subject": f"{kind} {record_id}", "record_version": version, "data": {}}


def _package():
    base = ".maestro/registrations/versions/1/candidates/cand-1"
    files, entries = {}, []
    for kind, folder, record_id in (("milestone", "milestones", "pm-1"), ("requirement", "requirements", "pm-1-req-1"), ("summary", "", "summary")):
        relative = f"{folder}/{record_id}.json" if folder else "summary.json"
        data = records.encode(_record(kind, record_id))
        files[f"{base}/{relative}"] = data
        entries.append({"path": relative, "record_id": record_id, "record_type": kind, "record_version": 1, "subject": f"{kind} {record_id}", "sha256": records.sha256(data)})
    manifest = records.encode({"files": entries})
    files[f"{base}/manifest.json"] = manifest
    ref = {"repository": "o/r", "commit": PACKAGE_COMMIT, "registration_version": 1, "candidate_id": "cand-1", "manifest_path": f"{base}/manifest.json", "manifest_sha256": records.sha256(manifest)}
    return ref, files


class OutcomeMappingTests(unittest.TestCase):
    def test_maps_milestones_and_requirements_at_the_package_commit(self):
        ref, files = _package()
        outcomes, _ = records.map_outcomes(ref, files.get)
        self.assertEqual([o["id"] for o in outcomes], ["pm-1", "pm-1-req-1"])
        self.assertTrue(all(o["commit"] == PACKAGE_COMMIT and len(o["sha256"]) == 64 for o in outcomes))
        self.assertEqual(records.milestone_ids(outcomes), ["pm-1"])

    def test_a_changed_record_is_rejected(self):
        ref, files = _package()
        path = next(p for p in files if p.endswith("pm-1.json"))
        files[path] = files[path] + b" "
        with self.assertRaises(records.FoundationError):
            records.map_outcomes(ref, files.get)

    def test_a_changed_manifest_is_rejected(self):
        ref, files = _package()
        with self.assertRaises(records.FoundationError):
            records.map_outcomes({**ref, "manifest_sha256": "0" * 64}, files.get)


def _investigation(**over):
    decision = {"local_key": "d1", "subject": "Reuse the store", "disposition": "reuse", "rationale": "It works.", "code_paths": ["src/store.py"],
                "evidence": [{"path": "src/store.py", "commit": COMMIT, "locator": "Store"}], "outcome_ids": ["pm-1"], "finding_keys": ["f1"]}
    decision.update(over)
    return {"schema": records.INVESTIGATION_SCHEMA, "summary": "Looked.", "decisions": [decision]}


class ValidationTests(unittest.TestCase):
    exists = staticmethod(lambda path: path in {"src", "src/store.py"})

    def check(self, document, required=frozenset({"pm-1"})):
        return records.validate_investigation(document, {"f1"}, {"pm-1", "pm-1-req-1"}, set(required), COMMIT, self.exists)

    def test_valid_investigation_passes(self):
        self.check(_investigation())

    def test_a_missing_source_path_is_named(self):
        with self.assertRaisesRegex(records.FoundationError, "src/none.py"):
            self.check(_investigation(code_paths=["src/none.py"]))

    def test_evidence_must_use_the_assigned_commit(self):
        with self.assertRaisesRegex(records.FoundationError, "assigned source commit"):
            self.check(_investigation(evidence=[{"path": "src/store.py", "commit": "c" * 40, "locator": "x"}]))

    def test_every_milestone_outcome_must_be_covered(self):
        with self.assertRaisesRegex(records.FoundationError, "pm-2"):
            self.check(_investigation(), required={"pm-1", "pm-2"})

    def test_unknown_outcome_and_finding_are_rejected(self):
        with self.assertRaises(records.FoundationError):
            self.check(_investigation(outcome_ids=["nope"]))
        with self.assertRaises(records.FoundationError):
            self.check(_investigation(finding_keys=["zz"]))

    def test_missing_disposition_may_have_no_code(self):
        self.check(_investigation(disposition="missing", code_paths=[], evidence=[]))
        with self.assertRaises(records.FoundationError):
            self.check(_investigation(code_paths=[]))

    def _structure(self, **over):
        value = {"schema": records.STRUCTURE_SCHEMA, "summary": "s", "locations": [{"current_path": "src/store.py", "intended_path": "src/store.py", "responsibility": "state", "owner": "shared", "shared_boundaries": [], "planned_move": False}],
                 "specialists": [{"local_key": "s1", "subject": "Storage", "source_area": "src", "role_title": "Storage Specialist", "owner": "Storage Specialist"}]}
        value.update(over)
        return value

    def test_structure_and_specialist_files(self):
        structure = records.validate_structure(self._structure(), COMMIT, lambda p: p in {"src"})
        files = {
            "specialists/src/.maestro/role-storage-specialist.md": b"# Storage Specialist\n## Responsibility\nx\n## Authority\nx\n## Source area\nx\n## Inputs and outputs\nx\n",
            "specialists/src/.maestro/context.md": b"# Context\n## Verified facts\nx\n## Source references\nx\n## Knowledge gaps\nx\n",
        }
        found = records.validate_specialist_files(structure, files)
        self.assertEqual(found[0]["area"], "src")
        self.assertIsNone(found[0]["memory"])
        self.assertEqual(records.repo_path("specialists/src/.maestro/context.md"), "src/.maestro/context.md")

    def test_structure_rejections(self):
        with self.assertRaisesRegex(records.FoundationError, "not a directory"):
            records.validate_structure(self._structure(), COMMIT, lambda p: False)
        two = self._structure(specialists=self._structure()["specialists"] * 2)
        with self.assertRaises(records.FoundationError):
            records.validate_structure(two, COMMIT, lambda p: True)
        moved = self._structure(locations=[{**self._structure()["locations"][0], "intended_path": "src/new.py"}])
        with self.assertRaisesRegex(records.FoundationError, "planned move"):
            records.validate_structure(moved, COMMIT, lambda p: True)

    def test_specialist_file_problems_are_named(self):
        structure = records.validate_structure(self._structure(), COMMIT, lambda p: True)
        with self.assertRaisesRegex(records.FoundationError, "role-storage-specialist.md"):
            records.validate_specialist_files(structure, {"specialists/src/.maestro/context.md": b"x"})
        files = {
            "specialists/src/.maestro/role-storage-specialist.md": b"# Storage Specialist\n## Responsibility\n",
            "specialists/src/.maestro/context.md": b"# C\n## Verified facts\n## Source references\n## Knowledge gaps\n",
        }
        with self.assertRaisesRegex(records.FoundationError, "Authority"):
            records.validate_specialist_files(structure, files)


class BuildTests(unittest.TestCase):
    def test_built_records_satisfy_the_schema_and_bind_references(self):
        ref, package_files = _package()
        outcomes, _ = records.map_outcomes(ref, package_files.get)
        finding = {"local_key": "f1", "subject": "Store", "severity": "non_blocking", "explanation": "e", "impact": "i", "requested_correction": "c",
                   "source_refs": [{"path": "src/store.py", "commit": COMMIT, "locator": "Store"}], "missing_information": None, "affected_items": []}
        files_out = {"specialists/src/.maestro/role-storage-specialist.md": b"# Storage Specialist\n", "specialists/src/.maestro/context.md": b"# Context\n"}
        entry = {"specialist": {"local_key": "s1", "subject": "Storage", "source_area": "src", "role_title": "Storage Specialist", "owner": "Storage Specialist"},
                 "area": "src", "role": "specialists/src/.maestro/role-storage-specialist.md", "context": "specialists/src/.maestro/context.md", "memory": None}
        files, manifest, manifest_path = records.build_foundation_set(
            project_id="p", activity_id="a", version=1, registration_ref=ref, source_commit=COMMIT, decision_version=2, outcomes=outcomes, findings=[finding],
            finding_identities={"f1": ("finding-1", 1)}, investigation=_investigation(), structure={"locations": [{"current_path": "src/store.py", "intended_path": "src/store.py", "responsibility": "r", "owner": "shared", "shared_boundaries": [], "planned_move": False}]},
            specialists=[entry], specialist_files=files_out, specialist_commit="d" * 40,
            owner_decisions=[{"subject": "Q", "question_id": "q1", "answer": "yes", "rationale": "Owner answered: yes"}], owner_id="owner",
        )
        base = manifest_path.rsplit("/", 1)[0]
        for name, definition in (("investigation.json", "investigation"), ("decisions.json", "decisions"), ("project-structure.json", "projectStructure"), ("manifest.json", "manifest")):
            jsonschema.Draft202012Validator({"$ref": f"#/$defs/{definition}", "$defs": SCHEMA["$defs"]}).validate(json.loads(files[f"{base}/{name}"]))
        investigation = json.loads(files[f"{base}/investigation.json"])
        self.assertEqual(investigation["findings"][0]["id"], "finding-1")
        self.assertEqual(investigation["decisions"][0]["outcome_refs"][0]["commit"], PACKAGE_COMMIT)
        self.assertEqual({e["record_type"] for e in manifest["inventory"]}, {"investigation", "decisions", "project_structure", "specialist_role", "specialist_context"})
        self.assertEqual([e["commit"] for e in manifest["inventory"] if e["record_type"].startswith("specialist")], ["d" * 40] * 2)
        self.assertEqual(manifest["version"], 1)
        index = records.discovery_index("p", None, 1, "e" * 40, manifest_path, records.sha256(files[manifest_path]), manifest["reviewed_content_hash"])
        jsonschema.Draft202012Validator({"$ref": "#/$defs/index", "$defs": SCHEMA["$defs"]}).validate(index)
        again = records.discovery_index("p", index, 2, "f" * 40, manifest_path, "0" * 64, "1" * 64)
        self.assertEqual([v["version"] for v in again["versions"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
