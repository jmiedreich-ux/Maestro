from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maestro.foundation import Database, DomainMigration, StorageSettings
from maestro.service.processes import (
    ProcessHandlerRegistry,
    ProcessPolicyError,
    ProcessPolicyService,
    ProcessProvider,
)
from maestro.service.resources import InstalledSchemaResources


PROVIDER_MIGRATION = DomainMigration(
    domain="test_process_provider",
    version=1,
    identity="test-process-provider-v1",
    statements=(
        "CREATE TABLE test_created_activities(activity_id TEXT PRIMARY KEY, policy_hash TEXT NOT NULL)",
    ),
)


def registration_definition() -> dict[str, object]:
    return {
        "schema_version": 1,
        "architect": {},
        "fidelity_reviewer": {},
        "initiation": {
            "policy": "registration_intake_or_idle_update",
            "start_operation": "registration.start",
        },
        "agent_session": {
            "policy": "fixed_assignment_followups",
            "architect_role": "project_architect",
            "reviewer_role": "fidelity_reviewer",
        },
        "saved_outputs": {
            "policy": "versioned_registration_package",
            "contract": "registration_package_v1",
            "root": ".maestro/registrations",
        },
        "review": {"policy": "bounded_independent_fidelity"},
        "confirmation": {
            "policy": "explicit_exact_candidate_activation",
            "on_complete": "stop",
        },
        "recovery": {"policy": "reconcile_preserved_registration"},
    }


def architecture_definition() -> dict[str, object]:
    return {
        "schema_version": 1,
        "maximum_fidelity_reviews": 1,
        "architect": {"run_timeout_seconds": 25},
        "fidelity_reviewer": {"run_timeout_seconds": 30},
        "initiation": {
            "policy": "confirmed_registration_idle_project",
            "start_operation": "architecture.start",
        },
        "agent_session": {
            "policy": "persistent_exact_session",
            "architect_role": "project_architect",
            "reviewer_role": "fidelity_reviewer",
        },
        "saved_outputs": {
            "policy": "versioned_architecture_set",
            "schema": "architecture-loop@1",
            "root": ".maestro/architecture",
        },
        "review": {"policy": "bounded_independent_fidelity"},
        "confirmation": {
            "policy": "exact_reviewed_working_version",
            "on_complete": "stop",
        },
        "recovery": {
            "policy": "reconcile_preserved_work",
            "automatic_recovery_attempts": 1,
            "maximum_output_corrections": 1,
        },
    }


def installed_process_schema(name: str) -> dict[str, object]:
    definition = registration_definition() if name == "registration-process" else architecture_definition()
    if name == "registration-process":
        definition["maximum_fidelity_reviews"] = 2
        definition["architect"]["run_timeout_seconds"] = 1800
        definition["fidelity_reviewer"]["run_timeout_seconds"] = 1800
        definition["recovery"]["automatic_recovery_attempts"] = 2
    optional_numbers = {
        "maximum_fidelity_reviews",
        "architect.run_timeout_seconds",
        "fidelity_reviewer.run_timeout_seconds",
        "recovery.automatic_recovery_attempts",
        "recovery.maximum_output_corrections",
    }

    def schema_for(value, path):
        if isinstance(value, dict):
            properties = {
                key: schema_for(child, f"{path}.{key}" if path else key)
                for key, child in value.items()
            }
            return {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": [key for key in value if f"{path}.{key}".strip(".") not in optional_numbers],
            }
        if isinstance(value, int):
            return {"type": "integer", "minimum": 0 if path.endswith("attempts") or path.endswith("corrections") else 1}
        return {"const": value}

    return {"$defs": {"processDefinition": schema_for(definition, "")}}


class ProcessPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.installation = self.root / "installed"
        for name in ("registration-process", "architecture-loop"):
            destination = self.installation / "schemas" / name / "1" / "schema.json"
            destination.parent.mkdir(parents=True)
            destination.write_text(json.dumps(installed_process_schema(name)), encoding="utf-8")
        self.database = Database(StorageSettings(path=self.root / "maestro.sqlite3"))
        self.resources = InstalledSchemaResources(self.installation)
        self.calls: list[tuple[str, str]] = []
        self.validators: list[str] = []
        self.registry = ProcessHandlerRegistry()
        self.registry.register(self._provider("registration", "registration-process@1"))
        self.registry.register(self._provider("architecture_loop", "architecture-loop@1"))
        self.service = ProcessPolicyService(self.database, self.resources, self.registry)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _provider(self, name: str, reference: str) -> ProcessProvider:
        policies = {
            "registration": {
                "initiation": "registration_intake_or_idle_update",
                "agent_session": "fixed_assignment_followups",
                "saved_outputs": "versioned_registration_package",
                "review": "bounded_independent_fidelity",
                "confirmation": "explicit_exact_candidate_activation",
                "recovery": "reconcile_preserved_registration",
            },
            "architecture_loop": {
                "initiation": "confirmed_registration_idle_project",
                "agent_session": "persistent_exact_session",
                "saved_outputs": "versioned_architecture_set",
                "review": "bounded_independent_fidelity",
                "confirmation": "exact_reviewed_working_version",
                "recovery": "reconcile_preserved_work",
            },
        }[name]

        def validator(definition):
            self.validators.append(name)

        def handler(snapshot, marker):
            self.calls.append((snapshot.process_name, marker))
            return "handled"

        return ProcessProvider(
            name=name,
            bundle_reference=reference,
            validator=validator,
            handlers={section: {policy: handler} for section, policy in policies.items()},
            migrations=(PROVIDER_MIGRATION,) if name == "registration" else (),
            routes=(f"{name}.start",),
            required_outputs=("registration_package" if name == "registration" else "architecture_set",),
        )

    def _create(self, activity_id: str, definition: dict[str, object], process="registration"):
        snapshot = self.service.prepare(process, definition)

        def creator(transaction, saved):
            # The provider observes its immutable policy row before activity creation.
            row = transaction.execute(
                "SELECT definition_sha256 FROM service_process_snapshots WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
            self.assertEqual(row[0], saved.definition_sha256)
            transaction.execute(
                "INSERT INTO test_created_activities(activity_id, policy_hash) VALUES (?, ?)",
                (activity_id, saved.definition_sha256),
            )
            return activity_id

        with self.database.transaction() as transaction:
            result = self.service.create_activity(transaction, activity_id, snapshot, creator)
        self.assertEqual(result, activity_id)
        return snapshot

    def test_real_provider_validates_snapshots_before_creation_and_dispatches(self) -> None:
        supplied = registration_definition()
        snapshot = self._create("activity-1", supplied)

        self.assertEqual(supplied["architect"], {})  # caller data was not mutated
        effective = snapshot.definition
        self.assertEqual(effective["maximum_fidelity_reviews"], 2)
        self.assertEqual(effective["architect"]["run_timeout_seconds"], 1800)
        self.assertEqual(effective["recovery"]["automatic_recovery_attempts"], 2)
        self.assertEqual(snapshot.bundle.reference, "registration-process@1")
        self.assertEqual(snapshot.bundle.hashes[0][0], "schema.json")
        self.assertEqual(self.validators, ["registration", "registration"])
        self.assertEqual(
            self.registry.dispatch(snapshot, "initiation", "provider-called"), "handled"
        )
        self.assertEqual(self.calls, [("registration", "provider-called")])
        provider = self.registry.provider("registration")
        self.assertEqual(provider.routes, ("registration.start",))
        self.assertEqual(provider.required_outputs, ("registration_package",))

    def test_rejects_legacy_unknown_missing_unsupported_and_bad_durations(self) -> None:
        cases: list[tuple[str, callable, str]] = []

        legacy = registration_definition()
        legacy["architect_run_timeout_seconds"] = 2
        cases.append(("legacy", lambda: self.service.prepare("registration", legacy), "unknown_field"))

        nested = registration_definition()
        nested["review"]["surprise"] = True
        cases.append(("nested unknown", lambda: self.service.prepare("registration", nested), "unknown_field"))

        missing = registration_definition()
        del missing["saved_outputs"]
        cases.append(("missing", lambda: self.service.prepare("registration", missing), "missing_field"))

        unsupported = registration_definition()
        unsupported["review"]["policy"] = "run_any_command"
        cases.append(("policy", lambda: self.service.prepare("registration", unsupported), "unsupported_policy"))

        duration = registration_definition()
        duration["architect"]["run_timeout_seconds"] = 0
        cases.append(("duration", lambda: self.service.prepare("registration", duration), "invalid_duration"))

        boolean = registration_definition()
        boolean["fidelity_reviewer"]["run_timeout_seconds"] = True
        cases.append(("boolean", lambda: self.service.prepare("registration", boolean), "invalid_type"))

        cases.append(("process", lambda: self.service.prepare("execution", {}), "unsupported_process"))

        for label, action, code in cases:
            with self.subTest(label=label), self.assertRaises(ProcessPolicyError) as caught:
                action()
            self.assertEqual(caught.exception.code, code)

    def test_missing_and_altered_bundle_block_work_but_status_stays_readable(self) -> None:
        missing_path = self.installation / "schemas/registration-process/1/schema.json"
        saved_bytes = missing_path.read_bytes()
        missing_path.unlink()
        with self.assertRaises(ProcessPolicyError) as caught:
            self.service.prepare("registration", registration_definition())
        self.assertEqual(caught.exception.code, "missing_bundle")
        missing_path.write_text(
            json.dumps(
                {"$defs": {"processDefinition": {"$ref": "missing.json#/$defs/value"}}}
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ProcessPolicyError) as caught:
            self.service.prepare("registration", registration_definition())
        self.assertEqual(caught.exception.code, "unresolved_bundle_reference")
        missing_path.write_bytes(saved_bytes)

        snapshot = self._create("activity-2", registration_definition())
        self.assertEqual(self.service.consume("activity-2", "fidelity_reviews"), 1)
        missing_path.write_bytes(saved_bytes + b"\n")

        restarted = ProcessPolicyService(self.database, self.resources, self.registry)
        readable = restarted.status("activity-2")
        self.assertEqual(readable.snapshot.definition_sha256, snapshot.definition_sha256)
        self.assertEqual(readable.counters[("fidelity_reviews", "activity")], 1)
        with self.assertRaises(ProcessPolicyError) as caught:
            restarted.resume("activity-2")
        self.assertEqual(caught.exception.code, "bundle_changed")

    def test_restart_retains_effective_snapshot_and_separate_scoped_counters(self) -> None:
        configured = architecture_definition()
        snapshot = self._create("activity-3", configured, "architecture_loop")
        configured["maximum_fidelity_reviews"] = 99

        self.assertEqual(self.service.consume("activity-3", "fidelity_reviews"), 1)
        self.assertEqual(
            self.service.consume("activity-3", "automatic_recovery_attempts", "architect-run"), 1
        )
        self.assertEqual(
            self.service.consume("activity-3", "automatic_recovery_attempts", "reviewer-run"), 1
        )
        self.assertEqual(self.service.consume("activity-3", "maximum_output_corrections", "assignment"), 1)
        for counter, scope in (
            ("fidelity_reviews", "activity"),
            ("automatic_recovery_attempts", "architect-run"),
            ("maximum_output_corrections", "assignment"),
        ):
            with self.assertRaises(ProcessPolicyError) as caught:
                self.service.consume("activity-3", counter, scope)
            self.assertEqual(caught.exception.code, "allowance_exhausted")

        restarted = ProcessPolicyService(self.database, self.resources, self.registry)
        restored = restarted.resume("activity-3")
        self.assertEqual(restored.snapshot, snapshot)
        self.assertEqual(restored.snapshot.definition["maximum_fidelity_reviews"], 1)
        self.assertEqual(restored.counters[("automatic_recovery_attempts", "reviewer-run")], 1)

    def test_creator_failure_rolls_back_snapshot_and_activity(self) -> None:
        snapshot = self.service.prepare("registration", registration_definition())
        with self.assertRaisesRegex(RuntimeError, "creation failed"):
            with self.database.transaction() as transaction:
                self.service.create_activity(
                    transaction,
                    "activity-4",
                    snapshot,
                    lambda transaction, saved: (_ for _ in ()).throw(RuntimeError("creation failed")),
                )
        with self.assertRaises(ProcessPolicyError) as caught:
            self.service.status("activity-4")
        self.assertEqual(caught.exception.code, "activity_not_found")

    def test_registry_rejects_undeclared_or_incomplete_providers(self) -> None:
        empty = ProcessHandlerRegistry()
        with self.assertRaises(ProcessPolicyError) as caught:
            empty.register(
                ProcessProvider("invented", "architecture-loop@1", lambda value: None, {})
            )
        self.assertEqual(caught.exception.code, "unsupported_process")

        with self.assertRaises(ProcessPolicyError) as caught:
            empty.register(
                ProcessProvider("registration", "registration-process@1", lambda value: None, {})
            )
        self.assertEqual(caught.exception.code, "unsupported_policy")


if __name__ == "__main__":
    unittest.main()
