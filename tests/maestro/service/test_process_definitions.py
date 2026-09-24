from __future__ import annotations

import filecmp
import json
import tempfile
import unittest
from pathlib import Path

from maestro.foundation import Database, StorageSettings
from maestro.service.process_definitions import PROCESS_TABLES, ProcessDefinitions, process_registry
from maestro.service.processes import ProcessPolicyError, ProcessPolicyService
from maestro.service.resources import InstalledSchemaResources

ROOT = Path(__file__).resolve().parents[3]
PACKAGED = ROOT / "services/maestro/schemas"

REGISTRATION = {
    "schema_version": 1,
    "architect": {}, "fidelity_reviewer": {},
    "initiation": {"policy": "registration_intake_or_idle_update", "start_operation": "registration.start"},
    "agent_session": {"policy": "fixed_assignment_followups", "architect_role": "project_architect", "reviewer_role": "fidelity_reviewer"},
    "saved_outputs": {"policy": "versioned_registration_package", "contract": "registration_package_v1", "root": ".maestro/registrations"},
    "review": {"policy": "bounded_independent_fidelity"},
    "confirmation": {"policy": "explicit_exact_candidate_activation", "on_complete": "stop"},
    "recovery": {"policy": "reconcile_preserved_registration"},
}
ARCHITECTURE = {
    "schema_version": 1, "maximum_fidelity_reviews": 1,
    "architect": {"run_timeout_seconds": 25}, "fidelity_reviewer": {"run_timeout_seconds": 30},
    "initiation": {"policy": "confirmed_registration_idle_project", "start_operation": "architecture.start"},
    "agent_session": {"policy": "persistent_exact_session", "architect_role": "project_architect", "reviewer_role": "fidelity_reviewer"},
    "saved_outputs": {"policy": "versioned_architecture_set", "schema": "architecture-loop@1", "root": ".maestro/architecture"},
    "review": {"policy": "bounded_independent_fidelity"},
    "confirmation": {"policy": "exact_reviewed_working_version", "on_complete": "stop"},
    "recovery": {"policy": "reconcile_preserved_work", "automatic_recovery_attempts": 1, "maximum_output_corrections": 1},
}


class PackagedBundleTests(unittest.TestCase):
    def test_packaged_bundles_match_the_documented_schemas(self) -> None:
        for name in ("registration-process", "architecture-loop"):
            self.assertTrue(filecmp.cmp(PACKAGED / name / "1/schema.json", ROOT / f"docs/schemas/{name}.schema.json", shallow=False), name)


class ProcessDefinitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        installation = root / "installed"
        for name in ("registration-process", "architecture-loop"):
            target = installation / "schemas" / name / "1"
            target.mkdir(parents=True)
            (target / "schema.json").write_bytes((PACKAGED / name / "1/schema.json").read_bytes())
        self.installation = installation
        self.tables = {"registration": json.loads(json.dumps(REGISTRATION)), "architecture_loop": json.loads(json.dumps(ARCHITECTURE))}
        database = Database(StorageSettings(path=root / "m.sqlite3"))
        self.policy = ProcessPolicyService(database, InstalledSchemaResources(installation), process_registry())
        self.definitions = ProcessDefinitions(self.policy, lambda: self.tables)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_real_definitions_validate_and_drive_assignment_terms(self) -> None:
        registration = self.definitions.evaluate("registration")
        self.assertEqual(registration.definition["architect"]["run_timeout_seconds"], 1800)
        terms = self.policy.registry.dispatch(registration, "agent_session", "fidelity_reviewer")
        self.assertEqual((terms.duration_seconds, terms.automatic_limit), (1800, 2))
        self.assertEqual((terms.role, terms.process_role), ("fidelity_reviewer", "fidelity_reviewer"))
        architecture = self.definitions.evaluate("architecture_loop")
        terms = self.policy.registry.dispatch(architecture, "agent_session", "architect")
        self.assertEqual((terms.duration_seconds, terms.automatic_limit), (25, 1))
        self.assertEqual((terms.role, terms.process_role), ("architect", "project_architect"))
        self.assertEqual(self.policy.registry.dispatch(architecture, "review"), 1)
        self.assertEqual(self.policy.registry.dispatch(registration, "initiation"), "registration.start")
        self.assertEqual([row["state"] for row in self.definitions.report()], ["valid", "valid"])

    def test_activity_keeps_its_snapshot_while_new_activities_see_the_edit(self) -> None:
        for activity in ("first",):
            with self.policy.database.transaction() as tx:
                self.definitions.start_activity(tx, "architecture_loop", activity, lambda t, snap: None)
        self.tables["architecture_loop"]["architect"]["run_timeout_seconds"] = 99
        with self.policy.database.transaction() as tx:
            self.definitions.start_activity(tx, "architecture_loop", "second", lambda t, snap: None)
        self.assertEqual(self.definitions.assignment_terms("first", "architect").duration_seconds, 25)
        self.assertEqual(self.definitions.assignment_terms("second", "architect").duration_seconds, 99)
        (self.installation / "schemas/architecture-loop/1/schema.json").write_text("{}")
        with self.assertRaises(ProcessPolicyError):
            self.definitions.assignment_terms("first", "architect")
        self.assertEqual(self.policy.status("first").snapshot.definition["architect"]["run_timeout_seconds"], 25)

    def test_invalid_definition_holds_only_its_process(self) -> None:
        self.tables["registration"]["architect_run_timeout_seconds"] = 5  # legacy key
        rows = {row["process"]: row for row in self.definitions.report()}
        self.assertEqual(rows["registration"]["state"], "invalid")
        self.assertEqual(rows["registration"]["error"]["code"], "unknown_field")
        self.assertEqual(rows["architecture_loop"]["state"], "valid")
        with self.assertRaises(ProcessPolicyError):
            self.definitions.evaluate("registration")

    def test_missing_table_and_missing_bundle_are_reported(self) -> None:
        del self.tables["architecture_loop"]
        rows = {row["process"]: row for row in self.definitions.report()}
        self.assertEqual(rows["architecture_loop"]["error"]["code"], "missing_process")
        (self.installation / "schemas/registration-process/1/schema.json").unlink()
        rows = {row["process"]: row for row in self.definitions.report()}
        self.assertEqual(rows["registration"]["error"]["code"], "missing_bundle")


if __name__ == "__main__":
    unittest.main()
