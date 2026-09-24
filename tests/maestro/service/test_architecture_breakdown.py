"""Architecture breakdown stage: deterministic checks, versioned set building and the service stage against scripted destination and runs.

The scripted destination and runs stand in for network and agent tools only; real agents, real GitHub and the
installed service are proven separately (var/qa/architecture-live).
"""
from __future__ import annotations

import copy
import json
import unittest

from maestro.service import architecture_breakdown as bd
from maestro.service.architecture_records import FoundationError, sha256
from pathlib import Path

from tests.maestro.service import test_architecture as base
from tests.maestro.service.test_registration import COMMIT

PACKAGED = Path(__file__).resolve().parents[3] / "services/maestro/schemas"
CATALOG = {"project_binding_hash": "a" * 64, "environments": {"local": {"classification": "test", "variables": {}, "secret_names": ["token"], "network_dependency_names": ["api"]}},
           "secrets": {"token": {"classification": "test", "environment_variable": "T"}}, "network_dependencies": {"api": {"host": "h", "protocol": "https", "ports": [443]}}}
REGISTRATION = {"repository": "o/r", "commit": "8" * 40, "registration_version": 1, "candidate_id": "c1", "manifest_path": "m.json", "manifest_sha256": "9" * 64}
EMPTY = {"project_binding_hash": None, "environments": {}, "secrets": {}, "network_dependencies": {}}
CRITERION = {"subject": "Works", "expected_result": "It works", "pass_boundary": "Real path", "verification": "Run it"}
EXECUTION = {"required_capabilities": ["code_edit"], "allowed_locations": ["local_ai_box"], "minimum_context_tokens": 20000}


def packet(key, milestone, outcomes, **over):
    value = {"local_key": key, "subject": f"Packet {key}", "purpose": "Deliver it", "milestone_key": milestone, "outcome_ids": outcomes, "included_scope": ["scope"], "exclusions": [],
             "permitted_paths": [f"src/{key}"], "specialist_key": "s1", "finding_ids": ["finding-1"], "dependency_keys": [], "shared_code_constraints": [], "parallel_with_keys": [],
             "execution_requirements": dict(EXECUTION), "completion_criteria": [dict(CRITERION)], "verification": ["run"], "essential_failure_checks": ["bad input"],
             "required_outputs": [{"subject": "Code", "path": f"src/{key}/main.py", "format": "Python", "schema_ref": None}]}
    value.update(over)
    return value


def plan(**over):
    value = {"setup_steps": [], "support_processes": [], "environment_refs": [], "secret_refs": [], "allowed_network_dependencies": [], "project_binding_hash": None, "data_requirements": [],
             "checks": [{"subject": "Journey", "user_journey": "Use it", "failure_cases": ["bad"], "required_artifacts": []}], "artifact_requirements": [], "cleanup_steps": ["remove temp"], "reset_check": "clean"}
    value.update(over)
    return value


def breakdown(outcomes, **over):
    value = {"schema": bd.BREAKDOWN_SCHEMA, "summary": "Plan.", "decisions": [], "milestones": [{
        "local_key": "m1", "subject": "First", "outcome": "Usable", "outcome_ids": outcomes, "included_scope": ["all"], "exclusions": [], "packet_keys": ["a", "b"], "dependency_keys": [],
        "integration_points": ["a feeds b"], "completion_criteria": [dict(CRITERION)], "qa_plan": plan()}],
        "packets": [packet("a", "m1", outcomes), packet("b", "m1", outcomes)]}
    value.update(over)
    return value


def check(document, outcomes=("o1",), required=("o1",), catalog=EMPTY, sha=lambda p: None):
    return bd.validate_breakdown(document, outcome_ids=set(outcomes), required_outcomes=set(required), finding_ids={"finding-1"}, specialist_keys={"s1"}, catalog=catalog, source_sha=sha)


class ValidationTests(unittest.TestCase):
    def rejected(self, document, text, **kw):
        with self.assertRaises(FoundationError) as caught:
            check(document, **kw)
        self.assertIn(text, str(caught.exception))
        return caught.exception

    def test_a_bounded_parallel_breakdown_passes(self) -> None:
        doc = breakdown(["o1"])
        doc["packets"][0]["parallel_with_keys"] = ["b"]
        checked = check(doc)
        self.assertEqual(["a", "b"], [p["local_key"] for p in checked["packets"]])

    def test_unbounded_or_disconnected_work_is_rejected_with_the_exact_rule(self) -> None:
        doc = breakdown(["o1"])
        doc["packets"][0]["permitted_paths"] = [f"src/p{n}" for n in range(bd.MAX_PACKET_PATHS + 1)]
        self.rejected(doc, "Split it into smaller bounded packets")
        doc = breakdown(["o1"], milestones=[{**breakdown(["o1"])["milestones"][0], "packet_keys": ["a"]}])
        self.rejected(doc, "must equal the packets that name it")
        self.rejected(breakdown(["o1"]), "no development milestone covers these confirmed milestone outcomes: o2", outcomes=("o1", "o2"), required=("o1", "o2"))

    def test_dependencies_must_resolve_without_cycles_and_parallel_work_must_be_independent(self) -> None:
        doc = breakdown(["o1"])
        doc["packets"][0]["dependency_keys"] = ["b"]
        doc["packets"][1]["dependency_keys"] = ["a"]
        self.rejected(doc, "form a cycle")
        doc = breakdown(["o1"])
        doc["packets"][0]["dependency_keys"] = ["zzz"]
        self.rejected(doc, "not a local_key in this breakdown")
        doc = breakdown(["o1"])
        doc["packets"][0]["dependency_keys"] = ["b"]
        doc["packets"][0]["parallel_with_keys"] = ["b"]
        self.rejected(doc, "one depends on the other")
        doc = breakdown(["o1"])
        doc["packets"][0].update(parallel_with_keys=["b"], permitted_paths=["src/shared"])
        doc["packets"][1]["permitted_paths"] = ["src/shared/x"]
        doc["packets"][1]["required_outputs"][0]["path"] = "src/shared/x/main.py"
        doc["packets"][0]["required_outputs"][0]["path"] = "src/shared/a.py"
        self.rejected(doc, "state the shared-code boundary")

    def test_a_packet_dependency_across_milestones_needs_the_milestone_dependency_and_decision_keys_stay_distinct(self) -> None:
        doc = breakdown(["o1"])
        m2 = dict(doc["milestones"][0], local_key="m2", packet_keys=["b"], qa_plan=plan())
        doc["milestones"][0]["packet_keys"] = ["a"]
        doc["milestones"].append(m2)
        doc["packets"][1]["milestone_key"] = "m2"
        doc["packets"][1]["dependency_keys"] = ["a"]
        self.rejected(doc, "does not list m1 as a dependency")
        doc["milestones"][1]["dependency_keys"] = ["m1"]
        check(doc)
        doc = breakdown(["o1"])
        one = {"local_key": "same-key", "subject": "S", "answer": "A", "rationale": "R", "affected_keys": ["a"], "finding_ids": []}
        doc["decisions"] = [one, dict(one, local_key="same key")]
        self.rejected(doc, "once normalized")

    def test_execution_inputs_and_findings_are_checked(self) -> None:
        doc = breakdown(["o1"])
        doc["packets"][0]["execution_requirements"]["required_capabilities"] = ["teleport"]
        self.rejected(doc, "required_capabilities must be distinct values of")
        doc = breakdown(["o1"])
        doc["packets"][0]["execution_requirements"]["minimum_context_tokens"] = 0
        self.rejected(doc, "positive integer")
        doc = breakdown(["o1"])
        doc["packets"][0]["finding_ids"] = ["finding-9"]
        self.rejected(doc, "not saved findings")
        doc = breakdown(["o1"])
        doc["packets"][0]["required_outputs"][0]["path"] = "elsewhere/x.py"
        self.rejected(doc, "outside its permitted_paths")

    def test_qa_plan_selections_come_from_the_operator_catalog_and_scripts_are_exact(self) -> None:
        doc = breakdown(["o1"])
        doc["milestones"][0]["qa_plan"] = plan(environment_refs=["prod"], project_binding_hash="a" * 64)
        error = self.rejected(doc, "which the operator's QA catalog does not provide", catalog=CATALOG)
        self.assertIsInstance(error, bd.QaBindingError)
        doc["milestones"][0]["qa_plan"] = plan(environment_refs=["local"], secret_refs=["token"], allowed_network_dependencies=["api"], project_binding_hash=None)
        self.rejected(doc, "project_binding_hash must be", catalog=CATALOG)
        doc["milestones"][0]["qa_plan"]["project_binding_hash"] = "a" * 64
        check(doc, catalog=CATALOG)
        step = {"subject": "Seed", "command": ["python", "scripts/seed.py"], "script_path": "scripts/seed.py", "script_sha256": None, "environment_ref": None, "planned_by_packet_key": None}
        doc = breakdown(["o1"])
        doc["milestones"][0]["qa_plan"] = plan(setup_steps=[step])
        self.rejected(doc, "does not exist in the source")
        doc["milestones"][0]["qa_plan"]["setup_steps"] = [{**step, "planned_by_packet_key": "a"}]
        self.rejected(doc, "permitted_paths cover it")
        doc["packets"][0]["permitted_paths"].append("scripts")
        check(doc)
        doc["milestones"][0]["qa_plan"]["setup_steps"] = [{**step, "script_sha256": "b" * 64}]
        self.rejected(doc, "script_sha256 must be the hash of scripts/seed.py", sha=lambda p: "c" * 64)


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.outcomes = [{"id": "o1", "subject": "One", "version": 1, "path": ".maestro/registrations/versions/1/candidates/c/milestones/o1.json", "sha256": "1" * 64, "commit": "2" * 40}]
        self.foundation = {"decisions": {"version": 1, "decisions": []}, "carried": []}
        self.finding_refs = {"finding-1": {"id": "finding-1", "subject": "F", "version": 1, "container": {"id": "investigation", "subject": "I", "version": 1, "path": "x/investigation.json", "sha256": "3" * 64, "commit": "4" * 40}}}
        self.role = {"id": "specialist-1-role", "subject": "R", "version": 1, "path": "src/.maestro/role-x.md", "sha256": "5" * 64, "commit": "6" * 40}

    def test_identities_are_stable_and_an_amendment_rewrites_only_records_that_changed(self) -> None:
        document = breakdown(["o1"])
        document["milestones"].append({**copy.deepcopy(document["milestones"][0]), "local_key": "m2", "subject": "Second", "packet_keys": ["c"], "dependency_keys": ["m1"]})
        document["packets"].append(packet("c", "m2", ["o1"], dependency_keys=["a"]))
        checked = check(document)
        ids = bd.assign_ids(checked, {})
        self.assertEqual(["milestone-1", "milestone-2", "packet-1", "packet-2", "packet-3"], sorted(v for k, v in ids.items() if k[0] in {"milestone", "packet"}))
        args = dict(project_id="p", activity_id="a", registration_ref={"r": 1}, source_commit=COMMIT, decision_version=1, outcomes=self.outcomes, carried_foundation=[],
                    prior_decisions=self.foundation["decisions"], owner_decisions=[], owner_id="owner", finding_refs=self.finding_refs, role_refs={"s1": self.role},
                    document_refs=[self.finding_refs["finding-1"]["container"]])
        files, manifest, path, states = bd.build_breakdown_set(version=2, checked=checked, ids=ids, previous={}, **args)
        self.assertEqual(".maestro/architecture/versions/2/manifest.json", path)
        self.assertEqual("breakdown", manifest["stage"])
        self.assertEqual({"milestone-1", "milestone-2", "packet-1", "packet-2", "packet-3", "qa-plan-1", "qa-plan-2", "decisions"}, {e["id"] for e in manifest["inventory"]})
        self.assertEqual({1}, {s["version"] for s in states.values()})
        published = {i: {**s, "commit": "7" * 40, "authored_sha256": s["authored_sha256"]} for i, s in states.items()}
        # unchanged input: everything is carried forward by its exact earlier reference
        files2, manifest2, _, states2 = bd.build_breakdown_set(version=3, checked=checked, ids=ids, previous=published, **args)
        self.assertEqual({"decisions"}, {e["id"] for e in manifest2["inventory"]})
        self.assertEqual(sorted(published), sorted(c["record_ref"]["id"] for c in manifest2["carried_forward"]))
        self.assertTrue(all(c["record_ref"]["commit"] == "7" * 40 for c in manifest2["carried_forward"]))
        self.assertNotEqual(manifest["reviewed_content_hash"], manifest2["reviewed_content_hash"])  # the set changed: its content is now mostly carried forward
        # change one packet of the second milestone: it, its milestone, its plan and its siblings/dependents move; the first milestone's other records that do not link to it stay
        changed = copy.deepcopy(document)
        changed["packets"][2]["purpose"] = "Deliver it differently"
        checked3 = check(changed)
        files3, manifest3, _, states3 = bd.build_breakdown_set(version=3, checked=checked3, ids=ids, previous=published, **args)
        rewritten = {e["id"] for e in manifest3["inventory"]} - {"decisions"}
        self.assertIn("packet-3", rewritten)
        self.assertIn("milestone-2", rewritten)
        self.assertNotIn("packet-1", rewritten)  # packet-1 is a dependency of packet-3, not the other way round, and does not link to milestone-2
        self.assertNotIn("milestone-1", rewritten)
        self.assertGreater(states3["packet-3"]["version"], states["packet-3"]["version"])
        self.assertEqual(states["packet-1"]["version"], states3["packet-1"]["version"])
        self.assertIn("packet-1", {c["record_ref"]["id"] for c in manifest3["carried_forward"]})
        self.assertNotEqual(manifest2["reviewed_content_hash"], manifest3["reviewed_content_hash"])

    def test_records_satisfy_the_breakdown_schema(self) -> None:
        import jsonschema
        schema = json.loads((PACKAGED / "architecture-breakdown/1/schema.json").read_text())
        document = breakdown(["o1"])
        document["decisions"] = [{"local_key": "d", "subject": "Use it", "answer": "Yes", "rationale": "Because", "affected_keys": ["a"], "finding_ids": ["finding-1"]}]
        checked = check(document)
        ids = bd.assign_ids(checked, {})
        files, manifest, path, states = bd.build_breakdown_set(
            project_id="p", activity_id="a", version=2, registration_ref=REGISTRATION, source_commit=COMMIT, decision_version=1, outcomes=self.outcomes, checked=checked, ids=ids, previous={},
            carried_foundation=[], prior_decisions=self.foundation["decisions"], owner_decisions=[], owner_id="owner", finding_refs=self.finding_refs, role_refs={"s1": self.role},
            document_refs=[self.finding_refs["finding-1"]["container"]])
        definitions = {"manifest.json": "manifest", "decisions.json": "decisions", "development-milestones": "developmentMilestone", "work-packets": "workPacket", "qa-plans": "qaPlan"}
        for file, data in files.items():
            relative = file.split("/versions/2/")[1]
            definition = definitions.get(relative) or definitions[relative.split("/")[0]]
            errors = list(jsonschema.Draft202012Validator({"$ref": f"#/$defs/{definition}", "$defs": schema["$defs"]}).iter_errors(json.loads(data)))
            self.assertEqual([], [e.message[:150] for e in errors], relative)
        self.assertEqual("breakdown-decision-d", json.loads(files[".maestro/architecture/versions/2/decisions.json"])["decisions"][0]["id"])


class StageTests(unittest.TestCase):
    """The service continues the same activity and session from saved foundations into a published breakdown."""
    setUp = None

    def setUp(self) -> None:  # noqa: F811
        base.ArchitectureTests.setUp(self)
        del self.architecture._begin_breakdowns
        self.architecture.breakdown_schema = json.loads((PACKAGED / "architecture-breakdown/1/schema.json").read_text())
        self.architecture._source_sha = lambda row: (lambda path: None)

    tearDown = base.ArchitectureTests.tearDown
    submit = base.ArchitectureTests.submit
    start = base.ArchitectureTests.start
    open_questions = base.ArchitectureTests.open_questions
    row = base.ArchitectureTests.row
    answer = base.ArchitectureTests.answer
    run_until = base.ArchitectureTests.run_until
    drive_to_ready = base.ArchitectureTests.drive_to_ready
    version = base.ArchitectureTests.version
    registered = base.ArchitectureTests.registered
    milestone_ids = base.ArchitectureTests.milestone_ids
    start_architecture = base.ArchitectureTests.start_architecture
    row_a = base.ArchitectureTests.row_a
    run_until_a = base.ArchitectureTests.run_until_a
    save_history = base.ArchitectureTests.save_history

    def response(self, document):
        return base.architect_response({"breakdown.json": json.dumps(document)}, findings=[])

    def test_saved_foundations_lead_to_a_validated_published_breakdown(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        bad = breakdown(milestones)
        bad["packets"][0]["specialist_key"] = "nobody"
        good = breakdown(milestones)
        good["packets"][0]["parallel_with_keys"] = ["b"]
        good["decisions"] = [{"local_key": "d", "subject": "Keep it small", "answer": "Two packets", "rationale": "Bounded", "affected_keys": ["m1"], "finding_ids": ["finding-1"]}]
        self.runs.script = [base.architect_response(base.files_for(milestones)), self.response(bad), self.response(good)]
        activity = self.start_architecture(project_id, package).activity_id
        for _ in range(20):
            self.architecture.tick()
            self.save_history(activity)
            if self.row_a(activity)["breakdown_ref_json"]:
                break
        row = self.row_a(activity)
        self.assertEqual("saved", row["state"])
        # the invalid output was rejected with the exact rule and corrected in the same session; the assignment's counts are kept
        stage_runs = [s for s in self.runs.started if s[3].assignment.instructions.get("task_kind") == "break_down"]
        self.assertEqual(["initial", "recovery"], [s[2] for s in stage_runs])
        self.assertIn("specialist_key 'nobody'", stage_runs[1][3].assignment.task)
        self.assertEqual(stage_runs[0][3].assignment.instructions["session_id"], stage_runs[1][3].assignment.instructions["session_id"])
        self.assertIn("qa-catalog.json", stage_runs[0][3].inputs)
        self.assertIn("foundations/investigation.json", stage_runs[0][3].inputs)
        # version 2 holds the milestones, packets, plans and decisions; foundations are carried forward, not rewritten
        published = self.destination.published[-2]
        base_path = ".maestro/architecture/versions/2"
        self.assertEqual({f"{base_path}/{n}" for n in ("manifest.json", "decisions.json", "development-milestones/milestone-1.json", "qa-plans/qa-plan-1.json", "work-packets/packet-1.json", "work-packets/packet-2.json")}, set(published))
        manifest = json.loads(published[f"{base_path}/manifest.json"])
        self.assertEqual("breakdown", manifest["stage"])
        self.assertIn("investigation", {c["record_ref"]["id"] for c in manifest["carried_forward"]})
        packet_record = json.loads(published[f"{base_path}/work-packets/packet-1.json"])
        self.assertEqual("finding-1", packet_record["starting_context"]["finding_refs"][0]["id"])
        self.assertEqual(["packet-2"], [p["id"] for p in packet_record["parallel_opportunities"]])
        self.assertEqual("qa-plan-1", json.loads(published[f"{base_path}/development-milestones/milestone-1.json"])["qa_plan_ref"]["id"])
        view = self.architecture.project_view(project_id)
        self.assertEqual("breakdown_saved", view["stage"])
        self.assertEqual(2, view["working_ref"]["version"])
        self.assertEqual(2, len(view["breakdown"]["packets"]))
        index = json.loads(self.destination.published[-1][".maestro/architecture/index.json"])
        self.assertEqual([1, 2], [v["version"] for v in index["versions"]])

    def test_a_breakdown_question_reaches_the_owner_and_the_answer_returns_to_the_same_session(self) -> None:
        project_id, package = self.registered()
        outcomes, milestones = self.milestone_ids(package)
        question = {"local_key": "q1", "subject": "Which search fields?", "question": "Search title only?", "reason": "The outcome does not say.", "recipient": "owner", "linked_finding_keys": [],
                    "options": [{"local_key": "title", "label": "Title only", "tradeoff": "Simpler", "recommendation_reason": None}]}
        ask = base.architect_response({}, result="clarification_required", questions=[question], findings=[])
        ask["kind"] = "clarify"
        self.runs.script = [base.architect_response(base.files_for(milestones)), ask, self.response(breakdown(milestones))]
        activity = self.start_architecture(project_id, package).activity_id
        for _ in range(20):
            self.architecture.tick()
            self.save_history(activity)
            if self.row_a(activity)["state"] == "architect_waiting":
                break
        self.assertEqual("architect_waiting", self.row_a(activity)["state"])
        self.assertEqual("breakdown", self.row_a(activity)["stage"])
        (question_id, _status, version), = self.open_questions(activity)
        self.submit("question.answer", project_id, activity, question_id, version, {"text": "Title only.", "choice_id": "title"})
        for _ in range(20):
            self.architecture.tick()
            self.save_history(activity)
            if self.row_a(activity)["breakdown_ref_json"]:
                break
        asked, resumed = [s for s in self.runs.started if s[3].assignment.instructions.get("task_kind") == "break_down"][-2:]
        self.assertEqual(asked[3].assignment.instructions["session_id"], resumed[3].assignment.instructions["session_id"])
        self.assertIn("Title only.", resumed[3].inputs["answers.json"].decode())
        decisions = json.loads(self.destination.published[-2][".maestro/architecture/versions/2/decisions.json"])["decisions"]
        self.assertEqual(["architect", "owner"], [decisions[0]["authority"]["kind"], decisions[-1]["authority"]["kind"]])  # the foundations decision is kept, the Owner's answer is added
        self.assertEqual("Title only.", decisions[-1]["answer"])


if __name__ == "__main__":
    unittest.main()
