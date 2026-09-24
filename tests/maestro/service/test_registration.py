"""Registration state machine against a scripted GitHub destination and scripted agent runs.

The scripted destination and runs stand in for network and agent tools only so the
step machine's own decisions can be exercised quickly and repeatably. Real GitHub,
real agents and the installed service are proven separately (var/qa/registration-live).
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import ActivityRepository
from maestro.service.authentication import OwnerAuthenticationSettings, OwnerAuthenticator, token_digest
from maestro.service.process_definitions import ProcessDefinitions, process_registry
from maestro.service.processes import ProcessPolicyService
from maestro.service.questions import QuestionRequestService, QuestionService
from maestro.service.registration import RegistrationService
from maestro.service.registration_github import DestinationError, RepositoryProfile, parse_repository_configuration
from maestro.service.registration_source import SourceError, interpret_scope, validate_sources
from maestro.service.registry import OperationRegistry
from maestro.service.requests import RequestRejection, RequestService
from maestro.service.reservations import ProjectReservations
from maestro.service.resources import InstalledSchemaResources

ROOT = Path(__file__).resolve().parents[3]
PACKAGED = ROOT / "services/maestro/schemas"
TOKEN = "b" * 64
COMMIT = "1" * 40
NEW_COMMIT = "2" * 40
REPO = "acme/tideline"
OVERVIEW = """# Tideline — Project Overview

## Project identity

| Field | Value |
|---|---|
| Project name | Tideline |
| Repository | https://github.com/acme/tideline |
| Responsible architect | A person |
| Document version | 1 |

## Purpose

A small notebook.

## Overall scope

| Boundary | Description |
|---|---|
| Included | Notes. |
| Excluded | Sync. |

## Current state

| Capability or area | Current condition | Evidence level | Evidence or authoritative source | Known missing prerequisites |
|---|---|---|---|---|
| Notes | Not built | Not applicable for unbuilt work | docs/architecture.md | None |

## Authoritative sources

| Source type | Subject or designation | Repository-relative location |
|---|---|---|
| Architecture | Tideline architecture | docs/architecture.md |
| Milestone declaration | NOTES — Tideline notebook | docs/milestones.md |
"""
ARCHITECTURE = """# Tideline — Architecture

| Field | Value |
|---|---|
| Document version | 1 |

## Components and responsibilities

| Component | Responsibility |
|---|---|
| Store | Keeps notes. |

## Journeys and interactions

### Capture a note

Text.
"""
MILESTONES = """# NOTES — Milestones

## Declaration identity

| Field | Value |
|---|---|
| Declaration | NOTES — Tideline notebook |
| Declaration version | 1 |
| Architecture source | docs/architecture.md |

## Milestones and order

| Position | Qualified milestone reference and plain subject | Milestone version | Milestone section |
|---|---|---|---|
| 1 | NOTES-PM1 — Capture a note | 1 | docs/milestones.md#notes-pm1--capture-a-note |

## NOTES-PM1 — Capture a note

**Outcome:** A person saves a note.

**Included:** The add command.

**Excluded:** Search.

### Architecture and journeys

| Required behavior or journey | Architecture section |
|---|---|
| Capture | docs/architecture.md#capture-a-note |

### Dependencies

| Required dependency | Reference | Current state or delivery responsibility |
|---|---|---|
| Python | docs/architecture.md | Assumed present |

### Acceptance criteria

| Expected result and conditions | Pass boundary | Verification and evidence | Accepted exception |
|---|---|---|---|
| Add saves | Prints Saved | Run it | None |

### Definition of done

Run it and review it.
"""
FILES = {"docs/project-overview.md": OVERVIEW, "docs/architecture.md": ARCHITECTURE, "docs/milestones.md": MILESTONES}
REGISTRATION = {
    "schema_version": 1, "architect": {}, "fidelity_reviewer": {},
    "initiation": {"policy": "registration_intake_or_idle_update", "start_operation": "registration.start"},
    "agent_session": {"policy": "fixed_assignment_followups", "architect_role": "project_architect", "reviewer_role": "fidelity_reviewer"},
    "saved_outputs": {"policy": "versioned_registration_package", "contract": "registration_package_v1", "root": ".maestro/registrations"},
    "review": {"policy": "bounded_independent_fidelity"},
    "confirmation": {"policy": "explicit_exact_candidate_activation", "on_complete": "stop"},
    "recovery": {"policy": "reconcile_preserved_registration"},
}


class ScriptedDestination:
    def __init__(self) -> None:
        self.files = {COMMIT: {p: t.encode() for p, t in FILES.items()}}
        self.branches = {"publish": "9" * 40}
        self.trees = {"9" * 40: {}}
        self.published: list[dict[str, bytes]] = []
        self.blocked_branch: set[str] = set()

    def default_branch(self, repository): return "main"

    def check_publication_branch(self, repository, branch):
        if branch in self.blocked_branch:
            raise DestinationError("branch_protected", f"branch {branch} is protected")
        if branch not in self.branches:
            raise DestinationError("branch_missing", f"publication branch {branch} does not exist")
        return {"decision": "allowed"}

    def resolve_source(self, repository, ref):
        if ref is None:
            return "refs/heads/main", COMMIT, "defaulted"
        if not ref.startswith(("refs/heads/", "refs/tags/")) and len(ref) != 40:
            raise DestinationError("invalid_source_ref", "source_ref must be a full ref or commit")
        if ref == "refs/heads/gone":
            raise DestinationError("source_unresolved", "refs/heads/gone does not exist")
        return ref, self.branches.get("source-head", COMMIT), "supplied"

    def read_file(self, repository, commit, path):
        return self.files.get(commit, {}).get(path) or self.trees.get(commit, {}).get(path)

    def head(self, repository, branch): return self.branches[branch]

    def publish(self, repository, branch, files, message):
        if getattr(self, "refuse_receipts", False) and any("/confirmations/" in path for path in files):
            raise DestinationError("publication_conflict", "a target path already holds different content", paths=list(files))
        commit = f"{len(self.published) + 3:040x}"
        self.trees[commit] = {**self.trees.get(self.branches[branch], {}), **files}
        self.branches[branch] = commit
        self.published.append(dict(files))
        return commit

    def verify_files(self, repository, commit, files):
        for path, data in files.items():
            if self.trees[commit].get(path) != data:
                raise DestinationError("publication_unverified", path)

    def fetch_source(self, repository, commit, mirror): pass


def response(role, assignment_id, run_id, **overrides):
    value = {
        "contract_version": 1, "assignment_id": assignment_id, "run_id": run_id, "project_id": "p", "activity_id": "a", "role": role,
        "source_commit": COMMIT, "decision_version": "d1", "result": "completed", "summary": "done", "findings": [], "questions": [],
        "candidate": None, "assessment": None, "reviewed_assessment": None, "review_outcome": None, "failure": None,
    }
    value.update(overrides)
    return value


class ScriptedRuns:
    """Stands in for the agent run layer: each started run finishes with the next scripted outcome."""

    def __init__(self, directory: Path, database: Database) -> None:
        self.directory, self.database, self.script, self.started = directory, database, [], []
        self.state: dict[str, dict] = {}
        self.route_resolver = self._route
        self.stopped: list[str] = []

    @staticmethod
    def _route(role, tool, model):
        from maestro.agents.routes import AgentRouteError
        if model == "nope":
            raise AgentRouteError("model_not_allowed", "model is not allowed")

    def create_assignment_from_terms(self, terms, assignment_id, project_id, activity_id, tool, model):
        self.state.setdefault(assignment_id, {"state": "ready", "tool": tool, "model_id": model, "runs": []})

    def run_count(self, assignment_id):
        return len(self.state[assignment_id]["runs"])

    def run_evidence(self, run_id):
        return {"tool_version": "1.0", "model_id": "m"}

    def assignment_state(self, assignment_id):
        if assignment_id not in self.state:
            from maestro.service.agent_runs import AgentRunError
            raise AgentRunError("assignment_not_found", "no")
        return self.state[assignment_id]

    def start_run(self, assignment_id, run_id, kind, build):
        spec = build(run_id)
        self.started.append((assignment_id, run_id, kind, spec))
        outcome = self.script.pop(0)
        self.state[assignment_id]["runs"].append(run_id)
        self.state[assignment_id]["state"] = "running"
        self.state[run_id] = {"outcome": outcome, "spec": spec, "polled": 0}

    def poll(self, run_id):
        entry = self.state[run_id]
        entry["polled"] += 1
        return self.view(run_id)

    def view(self, run_id):
        entry = self.state[run_id]
        kind = entry["outcome"]["kind"]
        state = "completed" if kind in {"completed", "clarify"} else "failed"
        assignment = next(a for a, v in self.state.items() if isinstance(v, dict) and run_id in v.get("runs", []))
        self.state[assignment]["state"] = "waiting_for_answers" if kind == "clarify" else ("completed" if kind == "completed" else "needs_recovery")
        return SimpleNamespace(run_id=run_id, state=state, failure_code=None if state == "completed" else "malformed_output", terminal_reason="script")

    def response(self, run_id):
        return self.state[run_id]["outcome"]["response"](self.state[run_id]["spec"].assignment)

    def artifacts(self, run_id):
        out = {}
        for name, text in self.state[run_id]["outcome"].get("files", {}).items():
            path = self.directory / f"{run_id}-{name}"
            path.write_text(text)
            import hashlib
            out[name] = (f"output/{name}.json", hashlib.sha256(text.encode()).hexdigest(), str(path))
        return out

    def reject_result(self, run_id, code, reason):
        self.state[run_id]["outcome"] = {"kind": "failed"}

    def stop(self, run_id, reason):
        self.stopped.append(run_id)
        return SimpleNamespace(state="cancelled")


def candidate_text(references=("NOTES-PM1",)):
    return json.dumps({
        "schema": "registration_candidate_v1",
        "summary": {"purpose": "Notes", "priorities": ["Capture first"], "assessment_outcome": "ready"},
        "milestones": [{"reference": r, "usage_walkthrough": "Run add", "dependencies": [
            {"subject": "Python", "required_outcome": "Runs", "state": "existing", "evidence_level": "reported", "evidence": "Stated"}]} for r in references],
    })


ASSESSMENT = json.dumps({"schema": "registration_assessment_v1", "summary": "Clear.", "evidence": [{"claim": "Sources are clear", "level": "source_inspection", "source": "docs/milestones.md#notes-pm1--capture-a-note"}]})
FINDING = {"local_key": "f1", "subject": "Gap", "severity": "blocking", "explanation": "Missing", "impact": "Cannot proceed", "requested_correction": "Add it",
           "source_refs": [{"path": "docs/milestones.md", "commit": COMMIT, "line": 5}], "affected_items": []}


def architect_done(a):
    return response("project_architect", a.assignment_id, a.run_id, candidate={"path": "output/candidate.json", "sha256": "x", "version": "1"}, assessment={"path": "output/assessment.json", "sha256": "y", "version": "1"})


def reviewer_done(outcome, findings=()):
    def build(a):
        return response("fidelity_reviewer", a.assignment_id, a.run_id, candidate={"path": "input/candidate.json", "sha256": "x", "version": "1"},
                        reviewed_assessment={"path": "input/assessment.json", "sha256": "y", "version": "1"}, review_outcome=outcome, findings=list(findings))
    return {"kind": "completed", "response": build}


ARCH_OK = {"kind": "completed", "response": architect_done, "files": {"candidate": candidate_text(), "assessment": ASSESSMENT}}


class RegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        installation = root / "installed"
        for name in ("registration-process", "architecture-loop"):
            target = installation / "schemas" / name / "1"
            target.mkdir(parents=True)
            (target / "schema.json").write_bytes((PACKAGED / name / "1/schema.json").read_bytes())
        self.database = Database(StorageSettings(path=root / "m.sqlite3"))
        records = ActivityRepository(self.database)
        self.questions = QuestionService(self.database)
        policy = ProcessPolicyService(self.database, InstalledSchemaResources(installation), process_registry())
        self.tables = {"registration": json.loads(json.dumps(REGISTRATION))}
        definitions = ProcessDefinitions(policy, lambda: self.tables)
        self.destination = ScriptedDestination()
        self.runs = ScriptedRuns(root, self.database)
        profiles, bindings = parse_repository_configuration({
            "repositories": {"qa": {"credential_profile": "k", "allowed_repositories": [REPO], "allowed_branch_patterns": ["publish"], "github": {"app_id": 1, "installation_id": 2, "app_slug": "app"}}},
            "repository_bindings": {"qa": {"repository": REPO, "profile": "qa"}},
        })
        self.service = RegistrationService(
            self.database, records=records, questions=self.questions, reservations=ProjectReservations(self.database), definitions=definitions,
            runs=self.runs, profiles=profiles, bindings=bindings, destination=lambda profile: self.destination,
            role_choices=(("codex", "m1"), ("claude_code", "m2")), state_dir=root / "state", owner_id="owner",
        )
        for identity, recipient in self.service.recipients.items():
            self.questions.register_recipient(identity, recipient)
        authenticator = OwnerAuthenticator(OwnerAuthenticationSettings("owner", token_digest(TOKEN)))
        self.requests = RequestService(self.database, authenticator, OperationRegistry(self.questions.operation_handlers + self.service.operation_handlers))
        self.auth = f"Bearer {TOKEN}"
        self.counter = 0
        self.rejected = (RequestRejection, ValueError)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def submit(self, operation, project_id=None, activity_id=None, question_id=None, expected=None, payload=None):
        self.counter += 1
        return self.requests.submit(self.auth, {"request_id": f"req-{self.counter}", "operation": operation, "project_id": project_id, "activity_id": activity_id,
                                                "question_id": question_id, "expected_version": expected, "payload": payload or {}})

    def start(self, **payload):
        body = {"repository": REPO, "overview_path": "docs/project-overview.md", "source_ref": None, "publication_branch": "publish", "scope": {"kind": "whole"},
                "architect": {"tool": "codex", "model": "m1"}, "reviewer": {"tool": "claude_code", "model": "m2"}}
        body.update(payload)
        return self.submit("registration.start", payload=body)

    def open_questions(self, activity_id):
        with self.database.read_connection() as connection:
            return [tuple(r) for r in connection.execute("SELECT question_id, status, version FROM service_questions WHERE activity_id = ? AND status IN ('awaiting_answer','clarification_required') ORDER BY question_id", (activity_id,))]

    def answer(self, receipt, choice=None, text="ok"):
        (question_id, _status, version), = self.open_questions(receipt.activity_id)
        self.submit("question.answer", receipt.project_id, receipt.activity_id, question_id, version, {"text": text, "choice_id": choice})
        self.service.tick()

    def row(self, activity_id):
        return self.service._read("SELECT * FROM service_registrations WHERE activity_id = ?", (activity_id,))

    def run_until(self, activity_id, state, limit=12):
        for _ in range(limit):
            self.service.tick()
            if self.row(activity_id)["state"] == state:
                return
        self.fail(f"registration stayed {self.row(activity_id)['state']} ({self.row(activity_id)['note']}), wanted {state}")

    def drive_to_ready(self):
        self.runs.script = [ARCH_OK, reviewer_done("APPROVE")]
        receipt = self.start()
        self.answer(receipt, "confirm-scope")
        self.run_until(receipt.activity_id, "ready")
        return receipt

    def test_source_validation_reports_every_gap(self) -> None:
        def read(path):
            text = FILES.get(path)
            if path == "docs/project-overview.md":
                text = text.replace("| Responsible architect | A person |\n", "")
            if path == "docs/milestones.md":
                text = text.replace("### Definition of done\n\nRun it and review it.\n", "")
            return None if text is None else text.encode()
        with self.assertRaises(SourceError) as caught:
            validate_sources("docs/project-overview.md", read)
        text = str(caught.exception)
        self.assertIn("Responsible architect", text)
        self.assertIn("Definition of done", text)
        with self.assertRaises(SourceError):
            validate_sources("docs/missing.md", read)

    def test_intake_rejections_name_the_problem(self) -> None:
        for payload, needle in (
            ({"repository": "other/repo"}, "binding_missing"),
            ({"source_ref": "main"}, "invalid_source_ref"),
            ({"source_ref": "refs/heads/gone"}, "source_unresolved"),
            ({"publication_branch": "nope"}, "branch_missing"),
            ({"publication_branch": "protected"}, "branch_protected"),
            ({"overview_path": "docs/absent.md"}, "not present"),
            ({"architect": {"tool": "codex", "model": "nope"}}, "cannot be used"),
        ):
            self.destination.blocked_branch = {"protected"}
            self.destination.branches["protected"] = "8" * 40
            try:
                self.start(**payload)
            except RequestRejection as caught_error:
                caught = SimpleNamespace(exception=caught_error)
            else:
                self.fail(f"accepted {payload}")
            self.assertIn(needle, str(caught.exception.as_body()), payload)
        with self.database.read_connection() as connection:
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM service_projects").fetchone()[0])

    def test_missing_choices_become_intake_questions_and_scope_confirmation_precedes_assessment(self) -> None:
        self.runs.script = [ARCH_OK, reviewer_done("APPROVE")]
        receipt = self.start(publication_branch=None, reviewer=None)
        activity = receipt.activity_id
        self.assertEqual("intake", self.row(activity)["state"])
        self.answer(receipt, "default-branch")  # main is not authorized by the profile: follow-up
        self.assertEqual("intake", self.row(activity)["state"])
        self.answer(receipt, None, "publish")
        self.answer(receipt, None, "claude_code:m2")
        self.assertEqual("scope", self.row(activity)["state"])
        self.answer(receipt, None, "just do it")  # a written reply cannot change the scope
        self.assertEqual("scope", self.row(activity)["state"])
        self.assertEqual([], self.runs.started)
        self.answer(receipt, "confirm-scope")
        self.assertEqual("architect", self.row(activity)["state"])
        row = self.row(activity)
        self.assertEqual(("publish", "claude_code", "m2"), (row["publication_branch"], row["reviewer_tool"], row["reviewer_model"]))

    def test_full_journey_to_registered(self) -> None:
        receipt = self.drive_to_ready()
        activity = receipt.activity_id
        row = self.row(activity)
        package = json.loads(row["package_json"])
        self.assertEqual(1, row["reviews_used"])
        self.assertEqual(1, package["registration_version"])
        self.assertIn(f".maestro/registrations/versions/1/candidates/{package['candidate_id']}/manifest.json", self.destination.published[0])
        # architect and reviewer were distinct assignments with the saved selections
        self.assertEqual(["codex", "claude_code"], [self.runs.state[a]["tool"] for a, *_ in self.runs.started])
        # a stale package reference is refused; nothing is confirmed
        with self.assertRaises(RequestRejection) as caught:
            self.submit("registration.confirm", receipt.project_id, activity, None, self.version(activity), {"package_ref": {**package, "commit": "0" * 40}})
        self.assertEqual(409, caught.exception.status_code)
        confirm_id = f"req-{self.counter + 1}"
        self.submit("registration.confirm", receipt.project_id, activity, None, self.version(activity), {"package_ref": package})
        self.assertEqual("confirming", self.row(activity)["state"])
        with self.assertRaises(RequestRejection):
            self.submit("registration.cancel", receipt.project_id, activity, None, self.version(activity))
        self.service.tick()
        self.assertEqual("confirmed", self.row(activity)["state"])
        with self.database.read_connection() as connection:
            self.assertEqual("registered", connection.execute("SELECT registration_status FROM service_projects").fetchone()[0])
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM service_project_reservations").fetchone()[0])
            self.assertEqual("completed", connection.execute("SELECT status FROM service_request_results WHERE request_id = ?", (confirm_id,)).fetchone()[0])
        receipt_path = next(p for p in self.destination.published[-1] if "/confirmations/" in p)
        self.assertEqual(package, json.loads(self.destination.published[-1][receipt_path])["package_ref"])
        index = json.loads(self.destination.published[-1][".maestro/registrations/index.json"])
        self.assertEqual(index["current_confirmation_ref"]["path"], receipt_path)

    def test_refused_confirmation_pauses_with_a_reason_and_can_be_cancelled(self) -> None:
        receipt = self.drive_to_ready()
        activity = receipt.activity_id
        package = json.loads(self.row(activity)["package_json"])
        self.destination.refuse_receipts = True
        self.submit("registration.confirm", receipt.project_id, activity, None, self.version(activity), {"package_ref": package})
        self.service.tick()
        row = self.row(activity)
        self.assertEqual("paused", row["state"])
        self.assertIn("publication_conflict", row["note"])
        self.service.tick()
        self.assertEqual("paused", self.row(activity)["state"])
        self.submit("registration.cancel", receipt.project_id, activity, None, self.version(activity))
        self.service.tick()
        self.assertEqual("cancelled", self.row(activity)["state"])

    def version(self, activity_id):
        with self.database.read_connection() as connection:
            return connection.execute("SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,)).fetchone()[0]

    def test_duplicate_start_returns_the_existing_activity(self) -> None:
        first = self.start()
        second = self.start()
        self.assertEqual(first.activity_id, second.activity_id)
        self.assertTrue(second.result["duplicate"])
        with self.database.read_connection() as connection:
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM service_registrations").fetchone()[0])

    def test_reviewer_changes_amend_within_the_limit_and_pause_at_it(self) -> None:
        self.runs.script = [ARCH_OK, reviewer_done("REQUEST_CHANGES", [FINDING]), ARCH_OK, reviewer_done("REQUEST_CHANGES", [FINDING])]
        receipt = self.start()
        self.answer(receipt, "confirm-scope")
        self.run_until(receipt.activity_id, "limit_paused")
        row = self.row(receipt.activity_id)
        self.assertEqual((2, 2), (row["reviews_used"], row["review_limit"]))
        self.assertEqual(4, len(self.runs.started))
        with self.assertRaises(Exception):  # the shared allowance is exhausted; a third review cannot be consumed
            self.service.definitions.policy.consume(receipt.activity_id, "fidelity_reviews")
        with self.database.read_connection() as connection:
            statuses = sorted(r[0] for r in connection.execute("SELECT DISTINCT status FROM service_findings WHERE activity_id = ?", (receipt.activity_id,)))
        self.assertIn("superseded", statuses)
        # amendment pass carries the reviewer's findings as immutable input
        self.assertIn("review-findings.json", self.runs.started[2][3].inputs)
        self.assertEqual([], [r for r in self.destination.published])

    def test_invalid_architect_output_enters_recovery_without_consuming_a_review(self) -> None:
        bad = {"kind": "completed", "response": architect_done, "files": {"candidate": candidate_text(("NOTES-PM9",)), "assessment": ASSESSMENT}}
        self.runs.script = [bad, ARCH_OK, reviewer_done("APPROVE")]
        receipt = self.start()
        self.answer(receipt, "confirm-scope")
        self.run_until(receipt.activity_id, "ready")
        self.assertEqual(1, self.row(receipt.activity_id)["reviews_used"])
        self.assertEqual(["initial", "recovery", "initial"], [k for _, _, k, _ in self.runs.started])

    def test_architect_questions_reach_the_owner_and_resume(self) -> None:
        ask = {"kind": "clarify", "response": lambda a: response("project_architect", a.assignment_id, a.run_id, result="clarification_required", findings=[FINDING],
               questions=[{"local_key": "q1", "subject": "Which platform", "question": "Which?", "reason": "Needed", "recipient": "owner", "finding_keys": ["f1"], "options": []}])}
        self.runs.script = [ask, ARCH_OK, reviewer_done("APPROVE")]
        receipt = self.start()
        self.answer(receipt, "confirm-scope")
        self.run_until(receipt.activity_id, "architect_waiting")
        self.assertEqual(0, self.row(receipt.activity_id)["reviews_used"])
        self.answer(receipt, None, "Linux only")
        self.run_until(receipt.activity_id, "ready")
        decisions = self.service._decisions(receipt.activity_id)
        self.assertIn("Linux only", [d["answer_text"] for d in decisions])

    def test_cancel_stops_the_run_and_releases_the_project(self) -> None:
        self.runs.script = [{"kind": "running"}]
        original = self.runs.view
        receipt = self.start()
        self.answer(receipt, "confirm-scope")
        self.submit("registration.cancel", receipt.project_id, receipt.activity_id, None, self.version(receipt.activity_id))
        self.run_until(receipt.activity_id, "cancelled")
        with self.database.read_connection() as connection:
            self.assertEqual("not_registered", connection.execute("SELECT registration_status FROM service_projects").fetchone()[0])
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM service_project_reservations").fetchone()[0])
        # a new attempt is allowed and gets the next registration version
        self.runs.script = [ARCH_OK, reviewer_done("APPROVE")]
        again = self.start()
        self.assertNotEqual(receipt.activity_id, again.activity_id)
        self.assertEqual(2, self.row(again.activity_id)["registration_version"])

    def test_source_change_before_confirmation_asks_the_owner(self) -> None:
        receipt = self.drive_to_ready()
        self.destination.branches["source-head"] = NEW_COMMIT
        self.destination.files[NEW_COMMIT] = {**self.destination.files[COMMIT], "docs/architecture.md": ARCHITECTURE.replace("Keeps notes.", "Keeps notes safely.").encode()}
        pending = json.loads(self.row(receipt.activity_id)["pending_json"])
        pending["source_checked_at"] = 0
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_registrations SET pending_json = ? WHERE activity_id = ?", (json.dumps(pending), receipt.activity_id))
        self.service.tick()
        self.assertEqual("source_changed", self.row(receipt.activity_id)["state"])
        self.answer(receipt, "retain-source")
        self.assertEqual("ready", self.row(receipt.activity_id)["state"])
        self.assertEqual(1, self.row(receipt.activity_id)["reviews_used"])

    def test_blocking_assessment_is_never_offered_for_confirmation(self) -> None:
        blocked = json.loads(candidate_text())
        blocked["summary"]["assessment_outcome"] = "blocked"
        arch = {"kind": "completed", "response": lambda a: {**architect_done(a), "findings": [FINDING]}, "files": {"candidate": json.dumps(blocked), "assessment": ASSESSMENT}}
        self.runs.script = [arch, reviewer_done("APPROVE")]
        receipt = self.start()
        self.answer(receipt, "confirm-scope")
        self.run_until(receipt.activity_id, "blocked")
        self.assertEqual([], self.destination.published)
        with self.database.read_connection() as connection:
            labels = [r[0] for r in connection.execute("SELECT label FROM service_activity_actions WHERE activity_id = ?", (receipt.activity_id,))]
        self.assertEqual(["Cancel registration"], labels)
        with self.assertRaises(RequestRejection):
            self.submit("registration.confirm", receipt.project_id, receipt.activity_id, None, self.version(receipt.activity_id), {"package_ref": {}})

    def test_binding_must_match_exactly_one_configured_profile(self) -> None:
        from maestro.service.registration_github import bind_repository
        profiles, bindings = parse_repository_configuration({
            "repositories": {"a": {"credential_profile": "k", "allowed_repositories": [REPO], "allowed_branch_patterns": ["x"], "github": {"app_id": 1, "installation_id": 2, "app_slug": "s"}}},
            "repository_bindings": {"one": {"repository": REPO, "profile": "a"}, "two": {"repository": REPO.upper(), "profile": "a"}, "three": {"repository": "acme/other", "profile": "missing"}},
        })
        with self.assertRaises(DestinationError) as ambiguous:
            bind_repository(REPO, profiles, bindings)
        self.assertEqual("binding_ambiguous", ambiguous.exception.code)
        with self.assertRaises(DestinationError) as unknown:
            bind_repository("acme/other", profiles, bindings)
        self.assertEqual("binding_profile_unknown", unknown.exception.code)
        with self.assertRaises(DestinationError) as missing:
            bind_repository("acme/none", profiles, bindings)
        self.assertEqual("binding_missing", missing.exception.code)

    def test_scope_interpretation_never_expands_a_selection(self) -> None:
        model = validate_sources("docs/project-overview.md", lambda p: FILES[p].encode() if p in FILES else None)
        scope = interpret_scope(model, {"kind": "milestones", "milestones": ["NOTES-PM1"]})
        self.assertEqual(["NOTES-PM1"], [i["reference"] for i in scope["included"]])
        with self.assertRaises(SourceError):
            interpret_scope(model, {"kind": "milestones", "milestones": ["NOTES-PM7"]})


if __name__ == "__main__":
    unittest.main()
