"""Architecture foundations state machine against a scripted GitHub destination and scripted agent runs.

The scripted destination and runs stand in for network and agent tools only so the step machine's own
decisions can be exercised quickly and repeatably. Real agents, real GitHub and the installed tools are
proven separately (var/qa/architecture-live).
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from maestro.service.architecture import ArchitectureService
from maestro.service.requests import RequestRejection
from maestro.service.resources import InstalledSchemaResources

from tests.maestro.service import test_registration as reg
from tests.maestro.service.test_registration import COMMIT

SOURCE_FILES = {"src/store.py", "src/cli.py", "docs/architecture.md"}
SOURCE_DIRS = {"", "src", "docs"}
ROLE = b"# Storage Specialist\n\n## Responsibility\nx\n\n## Authority\nx\n\n## Source area\nx\n\n## Inputs and outputs\nx\n"
CONTEXT = b"# Context\n\n## Verified facts\nx\n\n## Source references\nx\n\n## Knowledge gaps\nx\n"


def investigation(outcome_ids):
    return {"schema": "architecture_investigation_v1", "summary": "Looked.", "decisions": [{
        "local_key": "d1", "subject": "Reuse the store", "disposition": "reuse", "rationale": "It works.", "code_paths": ["src/store.py"],
        "evidence": [{"path": "src/store.py", "commit": COMMIT, "locator": "Store"}], "outcome_ids": outcome_ids, "finding_keys": ["f1"]}]}


STRUCTURE = {"schema": "architecture_structure_v1", "summary": "s", "locations": [{"current_path": "src/store.py", "intended_path": "src/store.py", "responsibility": "state", "owner": "shared", "shared_boundaries": [], "planned_move": False}],
             "specialists": [{"local_key": "s1", "subject": "Storage", "source_area": "src", "role_title": "Storage Specialist", "owner": "Storage Specialist"}]}
FINDING = {"local_key": "f1", "subject": "Store exists", "severity": "non_blocking", "explanation": "e", "impact": "i", "requested_correction": "c",
           "source_refs": [{"path": "src/store.py", "commit": COMMIT, "locator": "Store"}], "missing_information": None, "affected_items": []}


def files_for(outcome_ids, **replace):
    files = {"investigation.json": json.dumps(investigation(outcome_ids)), "project-structure.json": json.dumps(STRUCTURE),
             "specialists/src/.maestro/role-storage-specialist.md": ROLE.decode(), "specialists/src/.maestro/context.md": CONTEXT.decode()}
    files.update(replace)
    return files


def architect_response(files, **over):
    def build(a):
        value = {"contract_version": 1, "assignment_id": a.assignment_id, "run_id": a.run_id, "session_id": a.instructions["session_id"], "project_id": a.project_id,
                 "activity_id": a.activity_id, "role": "project_architect", "source_commit": a.source_commit, "decision_version": a.decision_version, "input_manifest": None,
                 "result": "completed", "summary": "done", "findings": [FINDING], "questions": [], "outputs": [], "reviewed_set": None, "review_outcome": None, "failure": None, "allocations": []}
        value.update(over)
        return value
    return {"kind": "completed", "response": build, "output_files": files}


class ArchitectureRuns(reg.ScriptedRuns):
    def artifacts(self, run_id):
        out = super().artifacts(run_id)
        for name, text in self.state[run_id]["outcome"].get("output_files", {}).items():
            path = self.directory / f"{run_id}-{name.replace('/', '_')}"
            data = text if isinstance(text, bytes) else text.encode()
            path.write_bytes(data)
            out[f"output:output/{name}"] = (f"output/{name}", hashlib.sha256(data).hexdigest(), str(path))
        return out

    def run_evidence(self, run_id):
        return {"tool_version": "1.0", "model_id": "m", "session_id": "provider-conversation-1"}

    def reject_result(self, run_id, code, reason):
        super().reject_result(run_id, code, reason)
        self.state[run_id]["reason"] = reason

    def view(self, run_id):
        view = super().view(run_id)
        view.terminal_reason = self.state[run_id].get("reason", view.terminal_reason)
        return view


class ArchitectureTests(unittest.TestCase):
    # The registration harness (scripted destination and runs, request service) is reused as built.
    tearDown = reg.RegistrationTests.tearDown
    submit = reg.RegistrationTests.submit
    start = reg.RegistrationTests.start
    open_questions = reg.RegistrationTests.open_questions
    answer = reg.RegistrationTests.answer
    row = reg.RegistrationTests.row
    run_until = reg.RegistrationTests.run_until
    drive_to_ready = reg.RegistrationTests.drive_to_ready
    version = reg.RegistrationTests.version

    def setUp(self) -> None:
        reg.RegistrationTests.setUp(self)
        self.runs.__class__ = ArchitectureRuns
        root = Path(self.temporary.name)
        self.tables["architecture_loop"] = {
            "schema_version": 1, "maximum_fidelity_reviews": 2, "architect": {"run_timeout_seconds": 1800}, "fidelity_reviewer": {"run_timeout_seconds": 1200},
            "initiation": {"policy": "confirmed_registration_idle_project", "start_operation": "architecture.start"},
            "agent_session": {"policy": "persistent_exact_session", "architect_role": "project_architect", "reviewer_role": "fidelity_reviewer"},
            "saved_outputs": {"policy": "versioned_architecture_set", "schema": "architecture-loop@1", "root": ".maestro/architecture"},
            "review": {"policy": "bounded_independent_fidelity"}, "confirmation": {"policy": "exact_reviewed_working_version", "on_complete": "stop"},
            "recovery": {"policy": "reconcile_preserved_work", "automatic_recovery_attempts": 2, "maximum_output_corrections": 2},
        }
        schema = InstalledSchemaResources(root / "installed").resolve("architecture-loop@1").schema
        self.architecture = ArchitectureService(
            self.database, records=self.service.records, questions=self.questions, reservations=self.service.reservations, definitions=self.service.definitions,
            runs=self.runs, profiles=self.service.profiles, destination=lambda profile: self.destination, state_dir=root / "architecture-state", owner_id="owner", schema=schema,
        )
        self.architecture._source_paths = lambda row: (SOURCE_FILES, SOURCE_DIRS)
        self.architecture._begin_breakdowns = lambda: None  # the foundations tests stop at saved foundations; test_architecture_breakdown continues
        for identity in ("owner", "project_architect"):
            self.questions.register_recipient(identity, lambda answer: (self.architecture if self.architecture.owns(answer.activity_id) else self.service).receive_answer(answer))
        from maestro.service.authentication import OwnerAuthenticationSettings, OwnerAuthenticator, token_digest
        from maestro.service.registry import OperationRegistry
        from maestro.service.requests import RequestService
        authenticator = OwnerAuthenticator(OwnerAuthenticationSettings("owner", token_digest(reg.TOKEN)))
        self.requests = RequestService(self.database, authenticator, OperationRegistry(
            self.questions.operation_handlers + self.service.operation_handlers + self.architecture.operation_handlers))

    def registered(self):
        receipt = self.drive_to_ready()
        package = json.loads(self.row(receipt.activity_id)["package_json"])
        self.submit("registration.confirm", receipt.project_id, receipt.activity_id, None, self.version(receipt.activity_id), {"package_ref": package})
        self.service.tick()
        return receipt.project_id, package

    def milestone_ids(self, package):
        from maestro.service import architecture_records as records
        outcomes, _ = records.map_outcomes(package, lambda path: self.destination.read_file("x", package["commit"], path))
        return outcomes, records.milestone_ids(outcomes)

    def start_architecture(self, project_id, package, **over):
        body = {"registration_ref": package, "architect": {"tool": "codex", "model_id": "m1"}, "reviewer": {"tool": "claude_code", "model_id": "m2"}}
        body.update(over)
        return self.submit("architecture.start", project_id, None, None, None, body)

    def row_a(self, activity_id):
        return self.architecture._read("SELECT * FROM service_architectures WHERE activity_id = ?", (activity_id,))

    def run_until_a(self, activity_id, state, limit=12):
        for _ in range(limit):
            self.architecture.tick()
            if self.row_a(activity_id)["state"] == state:
                return
        self.fail(f"architecture stayed {self.row_a(activity_id)['state']} ({self.row_a(activity_id)['note']}), wanted {state}")

    def test_start_requires_a_confirmed_registration_and_names_its_reasons(self) -> None:
        with self.assertRaises(RequestRejection) as caught:
            self.submit("architecture.start", "no-project", None, None, None, {"registration_ref": {}, "architect": {"tool": "codex", "model_id": "m1"}, "reviewer": {"tool": "claude_code", "model_id": "m2"}})
        self.assertEqual(404, caught.exception.status_code)
        project_id, package = self.registered()
        with self.assertRaises(RequestRejection) as caught:
            self.start_architecture(project_id, {**package, "manifest_sha256": "0" * 64})
        self.assertEqual("registration_ref_stale", caught.exception.as_body()["error"]["code"])
        with self.assertRaises(RequestRejection) as caught:
            self.start_architecture(project_id, package, architect={"tool": "codex", "model_id": "nope"})
        self.assertIn("cannot be used", str(caught.exception.as_body()))
        self.assertEqual(0, self.database_count("service_architectures"))

    def save_history(self, activity_id):
        """The real run service saves the tool's conversation after each run; the scripted one does not."""
        session = self.architecture._session(activity_id)
        (self.architecture.state_dir / "sessions" / session["session_id"] / "history").mkdir(parents=True, exist_ok=True)

    def database_count(self, table):
        with self.database.read_connection() as connection:
            return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_foundations_journey_from_start_to_published_records(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        self.runs.script = [architect_response(files_for(milestones))]
        receipt = self.start_architecture(project_id, package)
        activity = receipt.activity_id
        # repeated start opens the same activity; re-registration and other starts are refused while reserved
        again = self.start_architecture(project_id, package)
        self.assertEqual(activity, again.activity_id)
        with self.assertRaises(RequestRejection) as caught:
            self.start(publication_branch=None)
        self.assertEqual(409, caught.exception.status_code)
        self.run_until_a(activity, "saved")
        row = self.row_a(activity)
        foundations = json.loads(row["foundations_ref_json"])
        self.assertEqual(1, foundations["version"])
        self.assertEqual(package, json.loads(row["registration_json"]))
        # the architect's session, tool and model come from the request; one conversation is recorded
        session = self.architecture._session(activity)
        self.assertEqual(("codex", "m1", "provider-conversation-1"), (session["tool"], session["model"], session["provider_session_id"]))
        # three journaled commits: specialists, version set, index
        published = self.destination.published[-3:]
        self.assertEqual(["src/.maestro/context.md", "src/.maestro/role-storage-specialist.md"], sorted(published[0]))
        base = ".maestro/architecture/versions/1"
        self.assertEqual({f"{base}/{n}" for n in ("investigation.json", "decisions.json", "project-structure.json", "manifest.json")}, set(published[1]))
        self.assertEqual([".maestro/architecture/index.json"], list(published[2]))
        index = json.loads(published[2][".maestro/architecture/index.json"])
        self.assertEqual(foundations["commit"], index["working_ref"]["commit"])
        investigation_record = json.loads(published[1][f"{base}/investigation.json"])
        self.assertEqual("finding-1", investigation_record["findings"][0]["id"])
        self.assertEqual(package["commit"], investigation_record["decisions"][0]["outcome_refs"][0]["commit"])
        # the activity stays open holding the reservation; nothing else could start; view says so
        view = self.architecture.project_view(project_id)
        self.assertEqual(("running", "foundations_saved"), (view["state"], view["stage"]))
        self.assertEqual(["cancel"], view["available_actions"])
        with self.database.read_connection() as connection:
            self.assertEqual(activity, connection.execute("SELECT holder_id FROM service_project_reservations").fetchone()[0])
        # cancelling ends the activity, keeps the saved work and releases the project
        self.submit("architecture.cancel", project_id, activity, None, view["activity_version"], {"reason": "done with the test"})
        self.architecture.tick()
        self.assertEqual("cancelled", self.row_a(activity)["state"])
        self.assertEqual(0, self.database_count("service_project_reservations"))
        self.assertIsNone(self.architecture.project_view(project_id))
        self.assertEqual(1, self.database_count("service_architecture_outputs") // 4)

    def test_invalid_outputs_are_rejected_with_the_exact_problem_and_recovered_in_the_same_session(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        bad = files_for(milestones, **{"investigation.json": json.dumps({**investigation(milestones), "decisions": [{**investigation(milestones)["decisions"][0], "code_paths": ["src/nope.py"]}]})})
        self.runs.script = [architect_response(bad), architect_response(files_for(milestones))]
        activity = self.start_architecture(project_id, package).activity_id
        self.architecture.tick()
        self.save_history(activity)
        for _ in range(4):
            self.architecture.tick()
        first, second = self.runs.started[-2:]
        self.assertEqual("recovery", second[2])
        self.assertIn("src/nope.py", second[3].assignment.task)
        self.assertEqual(first[3].assignment.instructions["session_id"], second[3].assignment.instructions["session_id"])
        self.run_until_a(activity, "saved")
        self.assertEqual("provider-conversation-1", second[3].session.provider_session_id)

    def test_a_question_reaches_the_owner_and_the_answer_returns_to_the_same_session(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        question = {"local_key": "q1", "subject": "Keep the extra command?", "question": "Keep it?", "reason": "It is outside scope.", "recipient": "owner", "linked_finding_keys": ["f1"],
                    "options": [{"local_key": "keep", "label": "Keep", "tradeoff": "More code", "recommendation_reason": None}]}
        ask = architect_response({}, result="clarification_required", questions=[question])
        ask["kind"] = "clarify"
        self.runs.script = [ask, architect_response(files_for(milestones))]
        activity = self.start_architecture(project_id, package).activity_id
        self.run_until_a(activity, "architect_waiting")
        self.save_history(activity)
        self.assertEqual(1, self.database_count("service_findings"))
        (question_id, _status, version), = self.open_questions(activity)
        self.submit("question.answer", project_id, activity, question_id, version, {"text": "Keep it.", "choice_id": "keep"})
        self.architecture.tick()
        self.assertEqual("architect", self.row_a(activity)["state"])
        self.run_until_a(activity, "saved")
        asked, resumed = self.runs.started[-2:]
        self.assertEqual(asked[3].assignment.instructions["session_id"], resumed[3].assignment.instructions["session_id"])
        self.assertEqual("provider-conversation-1", resumed[3].session.provider_session_id)
        self.assertIn("Keep it.", resumed[3].inputs["answers.json"].decode())
        self.assertIn("do not repeat it from scratch", resumed[3].assignment.task)
        decisions = json.loads(self.destination.published[-2][".maestro/architecture/versions/1/decisions.json"])["decisions"]
        self.assertEqual("owner", decisions[-1]["authority"]["kind"])

    def test_a_publication_that_definitely_conflicts_does_not_block_cancelling(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        self.runs.script = [architect_response(files_for(milestones))]
        activity = self.start_architecture(project_id, package).activity_id
        row = self.row_a(activity)
        path = "src/.maestro/context.md"
        self.destination.trees[self.destination.branches["publish"]] = {path: b"someone else's file"}
        with self.database.transaction() as tx:
            tx.execute("INSERT INTO service_architecture_publications(operation_id, activity_id, kind, repository, branch, files_json, state, profile_json) VALUES ('op1', ?, 'specialists', ?, ?, '{}', 'writing', ?)",
                       (activity, row["repository"], row["publication_branch"], row["profile_json"]))
        self.architecture._frozen("op1", {path: b"our file"})
        view = self.architecture.project_view(project_id)
        self.submit("architecture.cancel", project_id, activity, None, view["activity_version"], {"reason": "stuck"})
        for _ in range(3):
            self.architecture.tick()
        self.assertEqual("cancelled", self.row_a(activity)["state"])
        self.assertEqual("paused", self.architecture._read("SELECT state FROM service_architecture_publications WHERE operation_id = 'op1'")["state"])

    def test_a_missing_saved_conversation_starts_a_linked_replacement_session(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        ask = architect_response({}, result="clarification_required", questions=[{
            "local_key": "q1", "subject": "Q", "question": "Q?", "reason": "R", "recipient": "owner", "linked_finding_keys": [], "options": []}], findings=[])
        ask["kind"] = "clarify"
        self.runs.script = [ask, architect_response(files_for(milestones))]
        activity = self.start_architecture(project_id, package).activity_id
        self.run_until_a(activity, "architect_waiting")
        (question_id, _status, version), = self.open_questions(activity)
        self.submit("question.answer", project_id, activity, question_id, version, {"text": "Yes.", "choice_id": None})
        self.architecture.tick()
        self.run_until_a(activity, "saved")
        sessions = self.architecture._rows("SELECT session_id, prior_session_id, state FROM service_architecture_sessions WHERE activity_id = ? ORDER BY rowid", (activity,))
        self.assertEqual(["lost", "active"], [s["state"] for s in sessions])
        self.assertEqual(sessions[0]["session_id"], sessions[1]["prior_session_id"])
        self.assertIn("replacement session", self.runs.started[-1][3].assignment.task)

if __name__ == "__main__":
    unittest.main()
