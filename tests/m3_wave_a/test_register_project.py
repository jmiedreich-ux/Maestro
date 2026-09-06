from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))

from support import RuntimeDirectory, TemporaryProjectRepository  # noqa: E402

from maestro.config import RuntimeConfig  # noqa: E402
from maestro.operational_state import Actor, OperationalStateStore  # noqa: E402
from maestro.project_authority import ProjectAuthorityLoader  # noqa: E402
from maestro.storage import SQLiteFoundation  # noqa: E402

ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")


class RegisterProjectTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository()  # project_id="example-project"
        self.runtime = RuntimeDirectory()
        self.foundation = self.runtime.foundation()
        self.config = RuntimeConfig(self.runtime.path)

        # A2: run the real authority loader for real, producing a real
        # Candidate `projects` row plus a real source_commit/manifest_digest
        # to chain into the binding below, instead of fabricating them.
        loader = ProjectAuthorityLoader(self.foundation)
        self.load_result = loader.load(
            self.repository.path, self.repository.commit, "owner/example-project"
        )
        self.assertEqual(self.load_result.disposition, "Reviewable")

    def tearDown(self):
        self.runtime.close()
        self.repository.close()

    def _record_candidate_binding(self, *, binding_id: str = "binding-1") -> None:
        store = OperationalStateStore(self.config)
        store.record_binding(
            {
                "binding_id": binding_id,
                "project_id": "example-project",
                "binding_revision": "revision-1",
                "source_commit": self.load_result.source_commit,
                "manifest_digest": self.load_result.manifest_digest,
                "adapter_version": "maestro-project-v1",
                "process_version": "maestro-m1",
                "authority_reference": self.load_result.request_id,
                "merge_policy": "no-automatic-merge",
                "acceptance_authority": "ProjectArchitect",
                "merge_execution_authority": "OwnerPerformed",
                "merge_delegation_reference": None,
                "binding_json": {"binding": "candidate"},
                "state": "Candidate",
                "activated_at": None,
                "superseded_at": None,
            },
            "command-binding-1",
            ACTOR,
            "2026-09-06T12:00:00.000000Z",
        )

    def test_registers_a_reviewable_project_with_a_matching_candidate_binding(self):
        self._record_candidate_binding()
        result = self.foundation.register_project("example-project", "binding-1")
        self.assertTrue(result.applied)
        self.assertEqual(result.registration_state, "Registered")

    def test_registration_is_durable_and_sets_active_binding_revision(self):
        self._record_candidate_binding()
        self.foundation.register_project("example-project", "binding-1")

        import sqlite3

        with sqlite3.connect(self.runtime.path / "maestro.sqlite3") as connection:
            row = connection.execute(
                "SELECT registration_state, active_binding_revision FROM projects "
                "WHERE project_id = 'example-project'"
            ).fetchone()
        self.assertEqual(row, ("Registered", "revision-1"))

    def test_a_project_that_is_not_candidate_is_a_real_no_op(self):
        self._record_candidate_binding()
        first = self.foundation.register_project("example-project", "binding-1")
        self.assertTrue(first.applied)

        second = self.foundation.register_project("example-project", "binding-1")
        self.assertFalse(second.applied)
        self.assertEqual(second.registration_state, "Registered")

    def test_an_unknown_project_raises_rather_than_silently_creating_one(self):
        with self.assertRaises(ValueError):
            self.foundation.register_project("does-not-exist", "binding-1")

    def test_a_binding_for_a_different_project_is_rejected(self):
        # A second, real project + Candidate binding under a different
        # project_id, to prove cross-project binding misuse is rejected.
        other_repository = TemporaryProjectRepository(manifest=_manifest_for("other-project"))
        try:
            other_load = ProjectAuthorityLoader(self.foundation).load(
                other_repository.path, other_repository.commit, "owner/other-project"
            )
            self.assertEqual(other_load.disposition, "Reviewable")
            store = OperationalStateStore(self.config)
            store.record_binding(
                {
                    "binding_id": "binding-other",
                    "project_id": "other-project",
                    "binding_revision": "revision-1",
                    "source_commit": other_load.source_commit,
                    "manifest_digest": other_load.manifest_digest,
                    "adapter_version": "maestro-project-v1",
                    "process_version": "maestro-m1",
                    "authority_reference": other_load.request_id,
                    "merge_policy": "no-automatic-merge",
                    "acceptance_authority": "ProjectArchitect",
                    "merge_execution_authority": "OwnerPerformed",
                    "merge_delegation_reference": None,
                    "binding_json": {"binding": "candidate"},
                    "state": "Candidate",
                    "activated_at": None,
                    "superseded_at": None,
                },
                "command-binding-other",
                ACTOR,
                "2026-09-06T12:00:00.000000Z",
            )
            with self.assertRaises(ValueError):
                self.foundation.register_project("example-project", "binding-other")
        finally:
            other_repository.close()

    def test_a_non_candidate_binding_is_a_real_no_op(self):
        self._record_candidate_binding()
        # Force the binding to a non-Candidate state directly (simulating
        # a Blocked binding) to prove register_project honors real
        # binding state, not just its existence.
        import sqlite3

        with sqlite3.connect(self.runtime.path / "maestro.sqlite3") as connection:
            connection.execute("UPDATE project_bindings SET state = 'Blocked' WHERE binding_id = 'binding-1'")
            connection.commit()

        result = self.foundation.register_project("example-project", "binding-1")
        self.assertFalse(result.applied)
        self.assertEqual(result.registration_state, "Candidate")


def _manifest_for(project_id: str) -> dict:
    from support import complete_manifest

    manifest = complete_manifest()
    manifest["identity"]["project_id"] = project_id
    manifest["identity"]["repository"] = f"owner/{project_id}"
    return manifest


if __name__ == "__main__":
    unittest.main()
