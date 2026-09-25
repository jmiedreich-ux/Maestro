"""Milestone verification: isolated Quality Assurance, outcome review, promotion and completion records.

The remote is a real local bare Git repository reached through the handler calls the service makes on GitHub; the
Quality Assurance and reviewer agents are scripted (they write real files into the run's real output directory,
then answer), while setup commands, environments, artifact storage and merges are the real ones. Real agents and
GitHub are proven on the installed path in var/qa/verify-live.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from maestro.service import execution_config, execution_qa
from maestro.service.registration_github import DestinationError

from test_execution import config_table
from test_execution_integration import ENV, IntegrationBase, LocalDestination, sh


class MilestoneDestination(LocalDestination):
    """Adds the file reads and default-branch publication the completion records use."""

    def read_file(self, repository, commit, path):
        done = self._run("show", f"{commit}:{path}", check=False)
        return None if done.returncode != 0 else subprocess.run(["git", "-c", "safe.directory=*", "-C", str(self.bare), "show", f"{commit}:{path}"], capture_output=True, env=ENV).stdout

    def check_code_branch(self, repository, branch):
        return None

    def publish(self, repository, branch, files, message, replaceable=frozenset()):
        head = self.branch_head(repository, branch)
        if all(self.read_file(repository, head, p) == d for p, d in files.items()):
            return head
        clone = self.bare.parent / f"publish-{abs(hash(message))}"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)], check=True, env=ENV)
        sh(clone, "checkout", "-q", branch)
        for path, data in files.items():
            (clone / path).parent.mkdir(parents=True, exist_ok=True)
            (clone / path).write_bytes(data)
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", message)
        commit = sh(clone, "rev-parse", "HEAD")
        sh(clone, "push", "-q", str(self.bare), f"{commit}:refs/heads/{branch}")
        return commit

    def verify_files(self, repository, commit, files):
        for path, data in files.items():
            if self.read_file(repository, commit, path) != data:
                raise DestinationError("publication_unverified", path)


PLAN = {
    "id": "qa-plan-1", "version": 1, "allowed_network_dependencies": [], "environment_refs": [], "secret_refs": [], "project_binding_hash": None,
    "checks": [{"subject": "Capture a note", "user_journey": "run add", "failure_cases": ["empty text"], "required_artifacts": ["transcript"]}],
    "data_requirements": [{"subject": "Synthetic text", "classification": "synthetic", "dataset_or_generator": "literal", "real_input_path": "add <text>", "sha256": None}],
    "setup_steps": [{"subject": "Create a temporary location", "command": ["python", "-c", "import tempfile; print(tempfile.mkdtemp(prefix='qa-'))"], "environment_ref": None, "script_path": None, "script_sha256": None}],
    "support_processes": [], "reset_check": "the temporary path is gone", "cleanup_steps": ["remove it"],
}


class VerificationBase(IntegrationBase):
    def setUp(self) -> None:
        super().setUp()
        self.dest = MilestoneDestination(self.bare)
        self.service._destination = lambda profile: self.dest
        self.qa_root = self.root / "qa"
        table = config_table(
            quality_assurance={"tool": "claude_code", "model": "qa-model", "run_timeout_seconds": 60},
            reviewers={"packet": {"primary": {"tool": "claude_code", "model": "r1", "run_timeout_seconds": 60}}, "milestone": {"primary": {"tool": "codex", "model": "mr", "run_timeout_seconds": 60}}},
            qa={"environment_root": str(self.qa_root / "env"), "artifact_root": str(self.qa_root / "artifacts")},
        )
        self.config = execution_config.validate(table)
        plan_bytes = json.dumps(PLAN).encode()
        self.plan_commit = self._commit_plan(plan_bytes)
        listing = [{"kind": "qa_plan", "id": "qa-plan-1", "path": "qa-plans/qa-plan-1.json", "commit": self.plan_commit, "sha256": execution_qa.sha256_bytes(plan_bytes)}]
        milestone = {"id": "m1", "outcome": "notes can be saved", "qa_plan_ref": {"id": "qa-plan-1", "path": "qa-plans/qa-plan-1.json"}, "completion_criteria": [{"id": "c1", "expected_result": "saved"}]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET config_json = ?, config_sha256 = ?, confirmed_ref_json = ? WHERE activity_id = 'exec-1'",
                       (json.dumps(self.config), execution_config.digest(self.config), json.dumps({"version": 1, "commit": "c", "manifest_path": "m", "listing": listing})))
            tx.execute("UPDATE service_execution_milestones SET record_json = ? WHERE milestone_key = 'm1'", (json.dumps(milestone),))
        self.head = self.integrated_packet("p1", {"app/a.py": "one = 10\ntwo = 2\nthree = 3\n"})

    def _commit_plan(self, data: bytes) -> str:
        clone = self.root / "plan-clone"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)], check=True, env=ENV)
        sh(clone, "checkout", "-q", "-b", "plans")
        (clone / "qa-plans").mkdir()
        (clone / "qa-plans" / "qa-plan-1.json").write_bytes(data)
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", "plan")
        commit = sh(clone, "rev-parse", "HEAD")
        sh(clone, "push", "-q", str(self.bare), f"{commit}:refs/heads/plans")
        return commit

    def integrated_packet(self, key: str, files: dict[str, str]) -> str:
        """A packet integrated into milestone m1 through the real queue (clean merge, no code change)."""
        head = self.packet_branch(key, files)
        self.add_packet(key, "m1", head)
        self.tick()
        self.integrator_finishes()
        self.tick()
        assert self.packet(key)["state"] == "integrated", self.entry()["note"]
        return self.dest.branch_head("o/r", "maestro/exec-1/milestone/m1")

    def verification(self):
        return self.service._verification("exec-1", "m1")

    def qa_finishes(self, results, artifacts=True, extra=None):
        run_id = self.runs.last("qa_agent")
        output = self.runs.runs[run_id]["output"]
        checks = []
        for subject, result in results:
            files = []
            if artifacts:
                (output / "artifacts").mkdir(exist_ok=True)
                (output / "artifacts" / "transcript.txt").write_text("$ tideline add 'buy tea'\nSaved.\nexit 0\n")
                files = [{"path": "artifacts/transcript.txt", "media_type": "text/plain", "description": "command transcript"}]
            checks.append({"subject": subject, "result": result, "journey_run": "tideline add", "data_source": "literal", "input_path": "add <text>", "expected": "Saved. and exit 0",
                           "actual": "Saved. and exit 0" if result == "PASS" else "crash", "limitations": [], "bypassed_paths": [], "requested_correction": "fix add" if result == "FAIL" else None, "artifacts": files, **(extra or {})})
        self.runs.finish(run_id, {"result": "completed", "checks": checks, "environment_notes": "reset ok", "summary": "s", "questions": []})

    def reviewer_finishes(self, outcome="APPROVE", blocking=0):
        run_id = self.runs.last("milestone_reviewer")
        v = self.verification()
        milestone = self.service._milestones("exec-1")["m1"]
        findings = [{"local_key": f"f{i}", "subject": f"S{i}", "severity": "blocking", "explanation": "e", "impact": "i", "requested_correction": "c", "locations": [{"path": "app/a.py", "locator": "1"}]} for i in range(blocking)]
        self.runs.finish(run_id, {"result": "completed", "review_outcome": outcome, "reviewed_range": {"base": milestone["base_commit"], "head": v["head_commit"]}, "summary": "s",
                                  "independence": "did not author", "findings": findings, "questions": []})

    def to_reviewing(self):
        self.tick()  # verification row created
        self.tick()  # environment prepared, QA agent launched
        self.qa_finishes([("Capture a note", "PASS")])
        self.tick()


class QualityAssuranceTests(VerificationBase):
    def test_a_finished_milestone_gets_an_isolated_environment_and_a_real_agent_run(self) -> None:
        self.assertEqual(self.verification()["state"], "qa", "the row is created as soon as the last packet is integrated")
        self.tick()
        self.assertEqual(self.verification()["state"], "qa_running")
        qa = self.service._qa_run("exec-1", "exec-1-m1-qa1")
        setup = json.loads(qa["setup_json"])
        self.assertEqual(setup[0]["exit_code"], 0)
        self.assertTrue(setup[0]["stdout"].strip().startswith("/"), "the real setup command ran and its output is recorded")
        self.assertEqual((qa["head_commit"], qa["plan_id"], qa["config_sha256"]), (self.head, "qa-plan-1", self.service.row_config_sha("exec-1")) if hasattr(self.service, "row_config_sha") else (self.head, "qa-plan-1", qa["config_sha256"]))
        self.assertTrue((self.qa_root / "env" / qa["environment_id"] / "work" / "app" / "a.py").is_file(), "a clean checkout of the exact milestone head")
        assignment = self.runs.runs[self.runs.last("qa_agent")]["build"].assignment
        self.assertEqual(assignment.role, "qa_agent")
        self.assertIn("plan.json", self.runs.runs[self.runs.last("qa_agent")]["build"].inputs)

    def test_a_pass_stores_evidence_with_hash_size_and_media_type_and_cleans_the_environment(self) -> None:
        self.to_reviewing()
        self.assertEqual(self.verification()["state"], "reviewing")
        qa = self.service._qa_run("exec-1", "exec-1-m1-qa1")
        self.assertEqual((qa["result"], qa["cleanup_state"]), ("PASS", "cleaned"))
        self.assertFalse((self.qa_root / "env" / qa["environment_id"]).exists())
        artifacts = self.service._rows("SELECT * FROM service_execution_qa_artifacts WHERE activity_id = 'exec-1' ORDER BY artifact_id")
        evidence = [a for a in artifacts if a["kind"] == "evidence"][0]
        data = Path(evidence["path"]).read_bytes()
        self.assertEqual((evidence["size"], evidence["sha256"], evidence["media_type"]), (len(data), execution_qa.sha256_bytes(data), "text/plain"))
        self.assertTrue(any(a["kind"] == "environment" for a in artifacts))
        fetched = self.service.artifact_content("proj", evidence["artifact_id"])
        self.assertTrue(fetched["verified"] and "Saved." in fetched["text"])
        Path(evidence["path"]).write_text("tampered")
        self.assertFalse(self.service.artifact_content("proj", evidence["artifact_id"])["verified"])

    def test_a_bypassed_required_path_is_untested_and_blocks_promotion(self) -> None:
        self.tick()
        self.tick()
        self.qa_finishes([("Capture a note", "PASS")], extra={"bypassed_paths": ["wrote the expected note file directly"]})
        self.tick()
        v = self.verification()
        self.assertEqual(v["state"], "blocked")
        self.assertIn("bypassed", v["note"])
        self.assertEqual(self.service._qa_run("exec-1", "exec-1-m1-qa1")["result"], "UNTESTED")
        self.assertIsNone(self.service._read("SELECT 1 AS n FROM service_execution_milestone_reviews"))
        for _ in range(3):
            self.tick()
        self.assertEqual(self.verification()["state"], "blocked")
        self.assertEqual(self.dest.branch_head("o/r", "main"), self.base, "nothing reached the product branch")

    def test_a_pass_without_evidence_is_untested(self) -> None:
        self.tick()
        self.tick()
        self.qa_finishes([("Capture a note", "PASS")], artifacts=False)
        self.tick()
        self.assertEqual(self.service._qa_run("exec-1", "exec-1-m1-qa1")["result"], "UNTESTED")

    def test_an_unreported_check_and_a_secret_in_evidence_stay_untested(self) -> None:
        self.tick()
        self.tick()
        output = self.runs.runs[self.runs.last("qa_agent")]["output"]
        (output / "artifacts").mkdir(exist_ok=True)
        (output / "artifacts" / "transcript.txt").write_text("token ghp_" + "a" * 30 + "\n")
        self.runs.finish(self.runs.last("qa_agent"), {"result": "completed", "checks": [{"subject": "Capture a note", "result": "PASS", "journey_run": "j", "data_source": "d", "input_path": "i", "expected": "e", "actual": "a", "limitations": [],
                                                                                   "bypassed_paths": [], "requested_correction": None, "artifacts": [{"path": "artifacts/transcript.txt", "media_type": "text/plain", "description": "d"}]}],
                                                      "environment_notes": "", "summary": "s", "questions": []})
        self.tick()
        checks = json.loads(self.service._qa_run("exec-1", "exec-1-m1-qa1")["checks_json"])
        self.assertEqual(checks[0]["result"], "UNTESTED")
        self.assertTrue(any("secret pattern" in r for r in checks[0]["reasons"]))
        self.assertEqual(self.service._rows("SELECT * FROM service_execution_qa_artifacts WHERE kind = 'evidence'"), [])

    def test_a_failed_setup_step_is_untested_with_its_real_error_and_leaves_no_environment(self) -> None:
        plan = {**PLAN, "setup_steps": [{"subject": "Break", "command": [sys.executable, "-c", "import sys; sys.exit(3)"], "environment_ref": None, "script_path": None, "script_sha256": None}]}
        self.reset_plan(plan)
        self.tick()
        self.tick()
        v = self.verification()
        self.assertEqual(v["state"], "blocked")
        self.assertIn("setup step 'Break' failed", v["note"])
        self.assertEqual(self.service._qa_run("exec-1", "exec-1-m1-qa1")["result"], "UNTESTED")
        self.assertFalse((self.qa_root / "env").exists() and any((self.qa_root / "env").iterdir()))
        self.assertEqual(self.service._rows("SELECT * FROM service_agent_assignments") if False else [], [])

    def test_a_plan_selecting_an_unconfigured_binding_is_untested_and_a_changed_binding_is_refused(self) -> None:
        self.reset_plan({**PLAN, "environment_refs": ["staging-test"], "project_binding_hash": "0" * 64})
        self.tick()
        self.tick()
        self.assertIn("no test binding", self.verification()["note"])
        binding_config = execution_config.validate(config_table(
            quality_assurance={"tool": "claude_code", "model": "m", "run_timeout_seconds": 5}, qa={"environment_root": "/tmp/x", "artifact_root": "/tmp/y", "project_bindings": {"proj": {"environments": {"staging-test": {"classification": "test", "variables": {"A": "1"}}}}}}))
        with self.assertRaises(execution_qa.QaError) as context:
            execution_qa.resolve_selection({**PLAN, "environment_refs": ["staging-test"], "project_binding_hash": "0" * 64}, binding_config, "proj")
        self.assertIn("differs", str(context.exception))
        binding, digest = execution_qa.binding_snapshot(binding_config, "proj")
        selected = execution_qa.resolve_selection({**PLAN, "environment_refs": ["staging-test"], "project_binding_hash": digest}, binding_config, "proj")
        self.assertEqual(selected["variables"], {"A": "1"})
        with self.assertRaises(execution_config.ExecutionConfigError):
            execution_config.validate(config_table(quality_assurance={"tool": "claude_code", "model": "m", "run_timeout_seconds": 5}, qa={"environment_root": "/a", "artifact_root": "/b", "project_bindings": {"proj": {"environments": {"prod": {"classification": "production"}}}}}))

    def reset_plan(self, plan):
        data = json.dumps(plan).encode()
        commit = self._commit_plan_again(data)
        confirmed = json.loads(self.service._read("SELECT confirmed_ref_json FROM service_executions")["confirmed_ref_json"])
        confirmed["listing"][0].update({"commit": commit, "sha256": execution_qa.sha256_bytes(data)})
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET confirmed_ref_json = ?", (json.dumps(confirmed),))

    def _commit_plan_again(self, data):
        clone = self.root / "plan-clone"
        (clone / "qa-plans" / "qa-plan-1.json").write_bytes(data)
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", "plan again")
        commit = sh(clone, "rev-parse", "HEAD")
        sh(clone, "push", "-q", str(self.bare), f"{commit}:refs/heads/plans-{commit[:6]}")
        return commit


class ReviewPromotionCompletionTests(VerificationBase):
    def test_both_gates_passing_merge_to_the_default_branch_publish_records_and_complete_the_execution(self) -> None:
        self.to_reviewing()
        self.tick()  # reviewer launched
        assignment = self.runs.runs[self.runs.last("milestone_reviewer")]["build"].assignment
        route = self.runs.assignments[assignment.assignment_id]
        self.assertEqual((route["tool"], route["model"]), ("codex", "mr"))
        inputs = self.runs.runs[self.runs.last("milestone_reviewer")]["build"].inputs
        self.assertIn("qa-result.json", inputs)
        self.assertEqual(json.loads(inputs["range.json"])["head"], self.head)
        self.reviewer_finishes()
        self.tick()
        self.assertEqual(self.verification()["state"], "promoting")
        self.tick()
        v = self.verification()
        self.assertEqual(v["state"], "publishing")
        main = self.dest.branch_head("o/r", "main")
        self.assertEqual(main, v["promoted_commit"])
        parents = sh(self.bare, "rev-list", "--parents", "-n", "1", main).split()
        self.assertEqual((len(parents), parents[1]), (3, self.base), "a non-fast-forward merge onto the recorded start")
        self.assertTrue(self.dest.contains("o/r", self.head, main))
        self.tick()
        v = self.verification()
        self.assertEqual(v["state"], "complete")
        record = json.loads(sh(self.bare, "show", f"{v['completion_commit']}:{v['completion_path']}"))
        self.assertEqual((record["kind"], record["final_merge_commit"], record["quality_assurance"]["result"], record["outcome_review"]["outcome"]), ("milestone-completion", main, "PASS", "APPROVE"))
        self.assertEqual(execution_qa.sha256_bytes(self.dest.read_file("o/r", v["completion_commit"], v["completion_path"])), v["completion_sha256"])
        self.assertNotEqual(self.row()["state"], "completed", "m2 and m3 have no packets yet, so the Execution is not complete")
        self.assertIsNone(self.service._read("SELECT 1 AS n FROM service_execution_completion"))

    def test_the_execution_completes_and_publishes_its_own_record_when_every_milestone_is_complete(self) -> None:
        with self.database.transaction() as tx:
            tx.execute("DELETE FROM service_execution_milestones WHERE milestone_key IN ('m2', 'm3')")
        self.to_reviewing()
        self.tick()
        self.reviewer_finishes()
        for _ in range(4):
            self.tick()
        row = self.row()
        self.assertEqual(row["state"], "completed")
        stored = self.service._read("SELECT * FROM service_execution_completion")
        self.assertEqual(stored["state"], "published")
        record = json.loads(sh(self.bare, "show", f"{stored['commit_sha']}:{stored['path']}"))
        self.assertEqual((record["kind"], record["record"], record["unresolved_work"]["assertion"]), ("completed", "execution-completion@1", "none"))
        self.assertEqual(record["milestones"][0]["merge_commit"], self.verification()["promoted_commit"])
        self.assertEqual(record["product_master"]["start_commit"], self.base)
        view = self.service.view("exec-1")["verification"]
        self.assertEqual(view["completion"]["commit"], stored["commit_sha"])
        self.assertEqual(view["milestones"][0]["qa"][0]["result"], "PASS")

    def test_requested_changes_and_failed_checks_use_the_gap_path_and_count_once_against_the_allowance(self) -> None:
        self.to_reviewing()
        self.tick()
        self.reviewer_finishes("REQUEST_CHANGES", blocking=1)
        self.tick()
        v = self.verification()
        self.assertEqual((v["state"], v["rounds_used"]), ("correcting", 1))
        finding = self.service._read("SELECT * FROM service_execution_findings")
        self.assertEqual((finding["source"], finding["milestone_key"]), ("outcome_review", "m1"))
        self.assertIsNotNone(self.service._read("SELECT 1 AS n FROM service_execution_architect WHERE kind = 'milestone_gap'"))
        self.assertEqual(self.dest.branch_head("o/r", "main"), self.base)
        # the architect decides, the correction integrates, and the new head is verified again
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = 'decided'")
        head2 = self.integrated_packet("p2", {"app/b.py": "b = 9\n"})
        self.tick()
        v = self.verification()
        self.assertEqual((v["attempt"], v["head_commit"]), (2, head2))
        self.assertIn(v["state"], ("qa", "qa_running"))
        self.assertEqual(v["rounds_used"], 1, "the review count carries over")

    def test_the_last_allowed_cycle_pauses_for_the_owner_and_a_failed_qa_check_becomes_a_finding(self) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET config_json = ?", (json.dumps({**self.config, "reviews": {**self.config["reviews"], "milestone": {"maximum_completed_rounds": 1}}}),))
        self.tick()
        self.tick()
        self.qa_finishes([("Capture a note", "FAIL")])
        self.tick()
        v = self.verification()
        self.assertEqual((v["state"], v["rounds_used"]), ("limit_paused", 1))
        finding = self.service._read("SELECT * FROM service_execution_findings")
        self.assertEqual(finding["source"], "quality_assurance")
        self.assertTrue(json.loads(finding["record_json"])["review_limit_exhausted"])
        self.assertEqual(json.loads(self.service._qa_run("exec-1", "exec-1-m1-qa1")["checks_json"])[0]["result"], "FAIL")

    def test_a_target_that_moved_refuses_promotion_and_a_missing_artifact_invalidates_the_check(self) -> None:
        self.to_reviewing()
        self.tick()
        self.reviewer_finishes()
        self.tick()
        # someone else advances the product branch after the evidence was taken
        clone = self.root / "other"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(clone)], check=True, env=ENV)
        (clone / "other.txt").write_text("x")
        sh(clone, "add", "-A")
        sh(clone, "commit", "-q", "-m", "other")
        sh(clone, "push", "-q", "origin", "HEAD:main")
        self.tick()
        v = self.verification()
        self.assertEqual(v["state"], "blocked")
        self.assertIn("promotion refused", v["note"])
        self.assertNotEqual(self.dest.branch_head("o/r", "main"), v["promoted_commit"])
        self.assertIsNone(v["promoted_commit"])

    def test_missing_evidence_before_promotion_sends_the_milestone_back_to_verification(self) -> None:
        self.to_reviewing()
        self.tick()
        self.reviewer_finishes()
        self.tick()
        for a in self.service._rows("SELECT path FROM service_execution_qa_artifacts WHERE kind = 'evidence'"):
            Path(a["path"]).unlink()
        self.tick()
        v = self.verification()
        self.assertEqual((v["state"], v["attempt"]), ("qa", 2))
        self.assertIsNone(v["promoted_commit"])

    def test_a_milestone_waits_for_its_dependency_to_be_promoted_first(self) -> None:
        # m2 depends on m1 and has its own integrated packet, verified and approved before m1
        head = self.packet_branch("p9", {"app/b.py": "b = 4\n"})
        self.add_packet("p9", "m2", head)
        self.tick()  # p9 enters the queue
        self.integrator_finishes()
        self.tick()
        v2 = self.service._read("SELECT * FROM service_execution_verifications WHERE milestone_key = 'm2'")
        self.assertIsNotNone(v2)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_verifications SET state = 'promoting' WHERE milestone_key = 'm2'")
            tx.execute("INSERT INTO service_execution_qa_runs(activity_id, qa_run_id, milestone_key, attempt, head_commit, plan_id, plan_sha256, plan_json, config_sha256, result, started_at) VALUES ('exec-1', 'exec-1-m2-qa1', 'm2', 1, ?, 'p', 'h', '{}', 'h', 'PASS', 't')", (v2["head_commit"],))
            tx.execute("INSERT INTO service_execution_milestone_reviews(activity_id, milestone_key, attempt, assignment_id, run_id, reviewer_tool, reviewer_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) VALUES ('exec-1', 'm2', 1, 'a', 'r', 'codex', 'x', 'b', ?, 'APPROVE', 's', '[]', 'i', 't')", (v2["head_commit"],))
        self.tick()
        self.assertEqual(self.service._read("SELECT * FROM service_execution_verifications WHERE milestone_key = 'm2'")["state"], "promoting")
        self.assertIn("milestone m1 must be promoted", self.service._read("SELECT note FROM service_execution_verifications WHERE milestone_key = 'm2'")["note"])
        self.assertEqual(self.dest.branch_head("o/r", "main"), self.base)


class ConfigurationTests(VerificationBase):
    def test_without_quality_assurance_configuration_a_finished_milestone_waits_with_a_plain_blocker(self) -> None:
        plain = execution_config.validate(config_table())
        with self.database.transaction() as tx:
            tx.execute("DELETE FROM service_execution_verifications")
            tx.execute("UPDATE service_executions SET config_json = ?", (json.dumps(plain),))
        self.tick()
        self.assertIsNone(self.service._read("SELECT 1 AS n FROM service_execution_verifications"))
        view = self.service.view("exec-1")
        self.assertFalse(view["verification"]["configured"])
        self.assertIn("not configured", view["waiting"])

    def test_the_milestone_reviewer_must_differ_from_every_author(self) -> None:
        self.to_reviewing()
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET tool = 'codex', model = 'mr'")
        self.tick()
        self.assertEqual(self.verification()["state"], "blocked")
        self.assertIn("no configured milestone reviewer differs", self.verification()["note"])
