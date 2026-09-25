"""Execution milestone verification: isolated Quality Assurance, whole-milestone outcome review, promotion and completion records.

Once every packet of a milestone is integrated, one verification record follows it: a real Quality Assurance agent
exercises the confirmed plan in a clean environment, a fresh non-author reviewer checks the exact assembled head
against the milestone's criteria and that evidence, and only when both pass does the service merge the milestone
into the product's default branch without fast-forward, verify the remote, and publish an immutable milestone
completion record. Failures become milestone findings for the existing gap path; corrected work is verified again
on its new head. When every milestone is complete the service publishes the Execution completion record and ends
the activity. Nothing is approved by an agent's claim: the service reads each result and each remote back.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from maestro.agents.execution_contract import QA_SCHEMA, REVIEWER_SCHEMA
from maestro.agents.transport import AgentAssignment
from maestro.foundation import DomainMigration, canonical_json

from . import execution_git, execution_qa
from .agent_runs import AgentRunError, RunBuild
from .architecture_records import encode
from .registration_github import DestinationError

MILESTONE_MIGRATION = DomainMigration(
    domain="service_execution",
    version=5,
    identity="service-execution-v5-milestone-verification",
    statements=(
        """
        CREATE TABLE service_execution_verifications(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            milestone_key TEXT NOT NULL,
            state TEXT NOT NULL,
            attempt INTEGER NOT NULL DEFAULT 1,
            head_commit TEXT NOT NULL,
            rounds_used INTEGER NOT NULL DEFAULT 0,
            note TEXT,
            pending_json TEXT NOT NULL DEFAULT '{}',
            master_before TEXT,
            promoted_commit TEXT,
            master_after TEXT,
            master_seq INTEGER NOT NULL DEFAULT 0,
            completion_path TEXT,
            completion_sha256 TEXT,
            completion_commit TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, milestone_key)
        )
        """,
        """
        CREATE TABLE service_execution_qa_runs(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            qa_run_id TEXT NOT NULL,
            milestone_key TEXT NOT NULL,
            attempt INTEGER NOT NULL,
            head_commit TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            plan_version INTEGER,
            plan_sha256 TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            binding_hash TEXT,
            binding_json TEXT NOT NULL DEFAULT '{}',
            config_sha256 TEXT NOT NULL,
            environment_id TEXT,
            environment_sha256 TEXT,
            setup_json TEXT NOT NULL DEFAULT '[]',
            processes_json TEXT NOT NULL DEFAULT '[]',
            data_json TEXT NOT NULL DEFAULT '[]',
            result TEXT CHECK(result IN ('PASS', 'FAIL', 'UNTESTED')),
            checks_json TEXT NOT NULL DEFAULT '[]',
            reason TEXT,
            agent_tool TEXT,
            agent_model TEXT,
            assignment_id TEXT,
            run_id TEXT,
            cleanup_state TEXT NOT NULL DEFAULT 'pending',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            PRIMARY KEY(activity_id, qa_run_id)
        )
        """,
        """
        CREATE TABLE service_execution_qa_artifacts(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            artifact_id TEXT NOT NULL,
            qa_run_id TEXT NOT NULL,
            milestone_key TEXT NOT NULL,
            check_subject TEXT NOT NULL,
            kind TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size INTEGER NOT NULL,
            media_type TEXT NOT NULL,
            description TEXT NOT NULL,
            classification TEXT NOT NULL DEFAULT 'test_evidence',
            retention_state TEXT NOT NULL DEFAULT 'retained',
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, artifact_id)
        )
        """,
        """
        CREATE TABLE service_execution_milestone_reviews(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            milestone_key TEXT NOT NULL,
            attempt INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            reviewer_tool TEXT NOT NULL,
            reviewer_model TEXT NOT NULL,
            reviewed_base TEXT NOT NULL,
            reviewed_head TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('APPROVE', 'REQUEST_CHANGES')),
            summary TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            independence TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, milestone_key, attempt)
        )
        """,
        """
        CREATE TABLE service_execution_completion(
            activity_id TEXT PRIMARY KEY REFERENCES service_executions(activity_id),
            state TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            commit_sha TEXT,
            final_master TEXT,
            record_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
    ),
)

_QA_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
_REVIEW_TOOLS = ["Read", "Bash", "Glob", "Grep"]
_ACTIVE = ("qa", "qa_running", "reviewing", "promoting", "publishing")
_PACKET_OPEN = ("pending", "reserved", "coding", "correcting", "publishing", "review_ready", "reviewing", "approved", "failed", "limit_paused")
_QUEUE_OPEN = ("queued", "integrating", "publishing", "reviewing", "merging", "blocked", "limit_paused")

_QA_TASK = """You are the Maestro Quality Assurance agent for one assembled milestone. You are not the implementer, an implementation reviewer or the outcome reviewer, and you do not fix code, change expectations or approve anything. Exercise the product the way its users do, in the isolated environment, and report each planned check honestly as PASS, FAIL or UNTESTED. Work only from this assignment, the files under input/ and the clone at output/work/ (the exact milestone commit {head}). source/ is a read-only copy of the same commit.

1. Read input/plan.json (the confirmed Quality Assurance plan: checks with user journeys and failure cases, data requirements, setup, artifacts and cleanup), input/milestone.json (the outcome and completion criteria) and output/environment.json (written by the service before you started: each setup step's real command and output, the environment identity, health results, and the temporary directory setup used).
2. Run every check in plan.json through the product's real entry path from output/work (set PYTHONDONTWRITEBYTECODE=1; use the setup results such as created temporary locations exactly as the plan describes). Cover each check's user journey and every listed failure case. Use only the plan's data; test data may be an input but must never directly create the result whose path you are verifying. If a required step can only be shown by bypassing the product (inserting the expected result, editing internals, a mock), do not count it: list it in bypassed_paths and give the check UNTESTED.
3. Write each piece of evidence as a file under output/artifacts/ (for example the real command transcript with exit status, the test runner output, the resulting data file before cleanup). Never write credentials or tokens into evidence. PASS needs at least one artifact that shows the actual result.
4. Return one entry in checks for EVERY check in plan.json, using its exact subject: result, journey_run (what you actually ran), data_source (what data and where it came from), input_path (how it entered the product), expected and actual results, limitations, bypassed_paths, artifacts (path relative to output/, media_type, description) and, for FAIL only, requested_correction (the smallest change needed). Do not add other checks. environment_notes states anything unusual about the environment, including the result of the plan's reset check: {reset}
5. result is completed when you have reported every check; use technical_failure only for a tool failure.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_MILESTONE_REVIEW_TASK = """You are the independent outcome reviewer of one assembled development milestone. You did not write or integrate any of its code, and you cannot change it. Decide whether the assembled branch delivers the milestone's promised usable outcome and its completion criteria, the packets and dependency deliveries work together, and the Quality Assurance evidence supports it. Work only from this assignment, the files under input/ and source/, a read-only checkout of the exact reviewed commit {head}. Never modify source/ or input/.

1. Read input/milestone.json (outcome, completion criteria, integration points, exclusions), input/range.json (the exact base and head you review), input/diff.patch (base..head), input/packets.json (each packet's criteria, review counts and integration), input/integration.json (queue results and dependency deliveries), input/qa-plan.json and input/qa-result.json (each check's result, actual behavior, limitations and artifact hashes).
2. Check every completion criterion against the code in source/, and run the real command or test that shows it (PYTHONDONTWRITEBYTECODE=1; work on a copy under scratch/ if a check writes). Check that the QA evidence is real and covers the criteria and that no required path was bypassed.
3. A blocking finding names a concrete unmet outcome, criterion or required evidence, the affected code, the impact and the minimum correction. Preferences and optional improvements are non_blocking and never block. Give each finding a unique local_key.
4. Return review_outcome APPROVE only when there is no blocking finding; otherwise REQUEST_CHANGES with at least one blocking finding. Copy reviewed_range exactly from input/range.json. independence states in one sentence that you did not author or integrate the code. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class MilestoneMixin:
    """Milestone verification behavior of ``ExecutionService``."""

    # --------------------------------------------------------------- helpers

    def _dest(self, row: Mapping[str, Any]) -> Any:
        return self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])

    def _verifications(self, activity_id: str) -> dict[str, dict[str, Any]]:
        return {v["milestone_key"]: v for v in self._rows("SELECT * FROM service_execution_verifications WHERE activity_id = ? ORDER BY milestone_key", (activity_id,))}

    def _verification(self, activity_id: str, key: str) -> dict[str, Any]:
        found = self._read("SELECT * FROM service_execution_verifications WHERE activity_id = ? AND milestone_key = ?", (activity_id, key))
        assert found is not None
        return found

    def _set_v(self, activity_id: str, key: str, pending: Mapping[str, Any] | None = None, **columns: object) -> None:
        sets = "".join(f", {name} = ?" for name in columns)
        values: list[object] = [_now()]
        head = "updated_at = ?"
        if pending is not None:
            head += ", pending_json = ?"
            values.append(canonical_json(pending))
        with self.database.transaction() as tx:
            tx.execute(f"UPDATE service_execution_verifications SET {head}{sets} WHERE activity_id = ? AND milestone_key = ?", (*values, *columns.values(), activity_id, key))

    def _v_block(self, row: Mapping[str, Any], v: Mapping[str, Any], reason: str, state: str = "blocked") -> None:
        if v["state"] == state and v["note"] == reason[:500]:
            return
        self._set_v(row["activity_id"], v["milestone_key"], state=state, note=reason[:500])
        with self.database.transaction() as tx:
            self._event(tx, row["activity_id"], "milestone_blocked", None, f"milestone {v['milestone_key']}: {reason[:300]}")
            self._say(tx, row["project_id"], row["activity_id"], f"Milestone {v['milestone_key']} cannot be verified or promoted yet: {reason[:400]}. Unrelated eligible work continues; nothing was merged.")

    def _qa_settings(self, config: Mapping[str, Any]) -> Mapping[str, Any]:
        """The operator's ``execution.qa`` settings, or service-owned defaults under the state directory (the effective paths are recorded with every run)."""
        configured = config.get("qa")
        if configured:
            return configured
        root = self.state_dir / "qa"
        return {"environment_root": str(root / "env"), "artifact_root": str(root / "artifacts"), "project_bindings": {}, "secret_patterns": [], "artifact_retention_days_after_close": 30,
                "setup_timeout_seconds": 300, "maximum_artifact_bytes": 20_000_000}

    def _qa_route(self, row: Mapping[str, Any], config: Mapping[str, Any]) -> Mapping[str, Any]:
        """The configured Quality Assurance route, or the Development Manager's route (a Codex or Claude route that can run commands) when none is configured."""
        return config.get("quality_assurance") or {"tool": row["manager_tool"], "model": row["manager_model"], "run_timeout_seconds": config["development_manager"]["run_timeout_seconds"]}

    def _milestone_ready(self, activity_id: str, key: str, packets: list[dict[str, Any]], queue: list[dict[str, Any]], deliveries: list[dict[str, Any]]) -> bool:
        mine = [p for p in packets if p["milestone_key"] == key]
        if not mine or any(p["state"] != "integrated" for p in mine):
            return False
        if any(e["milestone_key"] == key and e["state"] in _QUEUE_OPEN for e in queue):
            return False
        if any(d["consumer_milestone"] == key and d["state"] in ("queued", "held") for d in deliveries):
            return False
        return True

    # ---------------------------------------------------------------- advance

    def _advance_verification(self, row: Mapping[str, Any]) -> None:
        activity_id = row["activity_id"]
        config = json.loads(row["config_json"])
        milestones = self._load_milestones(row)
        packets, queue, deliveries = self._packets(activity_id), self._queue(activity_id), self._deliveries(activity_id)
        for key in sorted(milestones):
            known = self._verifications(activity_id).get(key)
            if self._outside_set(row, "milestones", key) and (known is None or known["state"] == "qa"):
                continue  # a pause or stop is in effect and this milestone was not fully in the saved set
            if known is None:
                if self._milestone_ready(activity_id, key, packets, queue, deliveries) and self._settled_of(activity_id, key):
                    head = self._current_milestone_head(row, key)
                    with self.database.transaction() as tx:
                        tx.execute("INSERT OR IGNORE INTO service_execution_verifications(activity_id, milestone_key, state, attempt, head_commit, created_at, updated_at) VALUES (?, ?, 'qa', 1, ?, ?, ?)",
                                   (activity_id, key, head, _now(), _now()))
                        self._say(tx, row["project_id"], activity_id, f"Every packet of milestone {key} is integrated (branch head {head[:12]}). Isolated Quality Assurance is next, then the independent outcome review.")
                continue
            try:
                self._advance_one(row, config, known)
            except DestinationError as error:
                if error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500):
                    raise
                self._v_block(row, known, f"{error.code}: {error}")
            except (execution_git.GitError, AgentRunError, execution_qa.QaError, ValueError, OSError) as error:
                self._v_block(row, known, f"{getattr(error, 'code', type(error).__name__)}: {error}")
        if self._settlement_of(row) is None:
            self._release_held_deliveries(row)
            self._advance_completion(row)

    def _settled_of(self, activity_id: str, key: str) -> bool:
        """No unresolved finding or gap assignment still concerns this milestone."""
        return self._gap_settled(activity_id, key) and not any(
            f["state"] == "reregistration_required" for f in self._rows("SELECT state FROM service_execution_findings WHERE activity_id = ? AND milestone_key = ?", (activity_id, key)))

    def _gap_settled(self, activity_id: str, key: str) -> bool:
        for arch in self._architects(activity_id, "milestone_gap"):
            if json.loads(arch["trigger_json"]).get("milestone_key") == key and arch["state"] not in ("active", "decided"):
                return False
        return True

    def _advance_one(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        state = v["state"]
        if state == "qa":
            self._qa_start(row, config, v)
        elif state == "qa_running":
            self._qa_advance(row, config, v)
        elif state == "reviewing":
            self._mr_advance(row, config, v)
        elif state == "correcting":
            self._correcting(row, config, v)
        elif state == "limit_paused":
            self._limit_check(row, config, v)
        elif state == "promoting":
            self._promote(row, config, v)
        elif state == "publishing":
            self._publish_milestone(row, v)
        elif state == "blocked":
            self._blocked_check(row, v)

    def _blocked_check(self, row: Mapping[str, Any], v: dict[str, Any]) -> None:
        """A blocked milestone is verified again only when corrected work has moved its branch; the earlier evidence stays as history."""
        activity_id, key = row["activity_id"], v["milestone_key"]
        head = self._current_milestone_head_or_recorded(row, key)
        if head != v["head_commit"] and self._milestone_ready(activity_id, key, self._packets(activity_id), self._queue(activity_id), self._deliveries(activity_id)):
            self._invalidate(row, v, "new work reached the milestone branch while it was blocked")

    # --------------------------------------------------------- QA: preparation

    def _qa_plan(self, row: Mapping[str, Any], key: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
        record = json.loads(self._load_milestones(row)[key]["record_json"])
        ref = record.get("qa_plan_ref") or {}
        confirmed = json.loads(row["confirmed_ref_json"])
        entry = next((e for e in confirmed["listing"] if e["kind"] == "qa_plan" and e["id"] == ref.get("id")), None)
        if entry is None:
            raise execution_qa.QaError(f"the confirmed breakdown has no Quality Assurance plan for milestone {key}")
        data = self._dest(row).read_file(row["repository"], entry["commit"], entry["path"])
        if data is None or _sha(data) != entry["sha256"]:
            raise execution_qa.QaError(f"Quality Assurance plan {entry['id']} does not match its confirmed hash")
        return json.loads(data), entry["sha256"], record

    def _qa_run(self, activity_id: str, qa_run_id: str) -> dict[str, Any]:
        found = self._read("SELECT * FROM service_execution_qa_runs WHERE activity_id = ? AND qa_run_id = ?", (activity_id, qa_run_id))
        assert found is not None
        return found

    def _untested_run(self, row: Mapping[str, Any], v: dict[str, Any], plan_id: str, plan_sha: str, plan: Mapping[str, Any], reason: str, setup: list[dict[str, Any]] | None = None, environment_id: str | None = None) -> None:
        """The run could not be prepared: record UNTESTED with the specific prerequisite and block promotion."""
        activity_id, key = row["activity_id"], v["milestone_key"]
        qa_run_id = f"{activity_id}-{key}-qa{v['attempt']}"
        now = _now()
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT OR REPLACE INTO service_execution_qa_runs(activity_id, qa_run_id, milestone_key, attempt, head_commit, plan_id, plan_version, plan_sha256, plan_json, config_sha256, environment_id, setup_json, result, reason, cleanup_state, started_at, finished_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNTESTED', ?, 'cleaned', ?, ?)",
                (activity_id, qa_run_id, key, v["attempt"], v["head_commit"], plan_id, plan.get("version"), plan_sha, canonical_json(plan), row["config_sha256"], environment_id, _dump(setup or []), reason[:500], now, now))
        self._v_block(row, v, f"Quality Assurance is UNTESTED: {reason}")

    def _qa_start(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], v["milestone_key"]
        qa_config = self._qa_settings(config)
        head = self._current_milestone_head(row, key)
        if head != v["head_commit"]:
            self._set_v(activity_id, key, head_commit=head)
            v = {**v, "head_commit": head}
        try:
            plan, plan_sha, milestone = self._qa_plan(row, key)
        except execution_qa.QaError as error:
            self._v_block(row, v, f"Quality Assurance is UNTESTED: {error}")
            return
        qa_run_id = f"{activity_id}-{key}-qa{v['attempt']}"
        existing = self._read("SELECT * FROM service_execution_qa_runs WHERE activity_id = ? AND qa_run_id = ?", (activity_id, qa_run_id))
        if existing is not None:
            self._teardown(existing)  # a restart between preparation and launch: discard the half-built environment and prepare again
        environment_id = f"{activity_id}-{key}-env{v['attempt']}"
        env_dir = Path(qa_config["environment_root"]) / environment_id
        try:
            selection = execution_qa.resolve_selection(plan, config, row["project_id"])
        except execution_qa.QaError as error:
            self._untested_run(row, v, plan["id"], plan_sha, plan, str(error))
            return
        if not plan.get("checks"):
            self._untested_run(row, v, plan["id"], plan_sha, plan, "the confirmed plan lists no checks")
            return
        if env_dir.exists():
            self._untested_run(row, v, plan["id"], plan_sha, plan, f"environment directory {env_dir} already exists and is quarantined; it is never reused", environment_id=environment_id)
            return
        mirror = self._mirror(row["project_id"])
        self._dest(row).fetch_source(row["repository"], head, mirror)
        env_dir.mkdir(parents=True, mode=0o750)
        processes: list[dict[str, Any]] = []
        variables = selection.get("variables", {})
        if plan.get("support_processes"):
            try:
                execution_git.prepare_clone(mirror, head, env_dir / "work", "maestro-qa")
                processes = execution_qa.start_support(plan, env_dir / "work", env_dir, environment_id, variables)
            except (execution_qa.QaError, execution_git.GitError) as error:
                execution_qa.stop_processes(processes)
                clean = execution_qa.clean_environment(env_dir)
                self._untested_run(row, v, plan["id"], plan_sha, plan, str(error) + ("" if clean else "; the environment could not be removed and is quarantined"), [], environment_id)
                return
        environment_sha = _sha(canonical_json({"environment_id": environment_id, "head_commit": head, "plan_sha256": plan_sha, "config_sha256": row["config_sha256"], "binding_hash": selection.get("binding_hash")}).encode())
        data = [{**d, "recorded_at": _now()} for d in plan.get("data_requirements", [])]
        now = _now()
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT OR REPLACE INTO service_execution_qa_runs(activity_id, qa_run_id, milestone_key, attempt, head_commit, plan_id, plan_version, plan_sha256, plan_json, binding_hash, binding_json, config_sha256, environment_id, environment_sha256, setup_json, processes_json, data_json, cleanup_state, started_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', ?, ?, 'active', ?)",
                (activity_id, qa_run_id, key, v["attempt"], head, plan["id"], plan.get("version"), plan_sha, canonical_json(plan), selection.get("binding_hash"),
                 canonical_json({k: selection.get(k) for k in ("environments", "secrets", "network")}), row["config_sha256"], environment_id, environment_sha, _dump(processes), _dump(data), now))
        route = self._qa_route(row, config)
        assignment_id = f"{qa_run_id}-agent"
        inputs = {"plan.json": _json(plan), "milestone.json": _json(milestone)}
        pending = json.loads(v["pending_json"] or "{}")
        task = _QA_TASK.format(head=head, reset=plan.get("reset_check") or "none stated")
        outcome: dict[str, Any] = {"setup": []}

        def prepare(workspace) -> None:
            # The agent sees only its own workspace, so the plan's setup runs here: in the clone at the exact head, with HOME and TMPDIR inside the sandbox's scratch area.
            work = workspace.paths.output / "work"
            execution_git.prepare_clone(mirror, head, work, "maestro-qa-work")
            execution_git.prepare_agent_home(workspace.paths.scratch / "home")
            artifacts = workspace.paths.output / "artifacts"
            artifacts.mkdir(mode=0o707, exist_ok=True)
            artifacts.chmod(0o707)
            try:
                outcome["setup"] = execution_qa.run_setup(plan, work, workspace.paths.scratch, environment_id, variables, int(qa_config["setup_timeout_seconds"]))
            except execution_qa.QaError as error:
                outcome["setup"] = getattr(error, "results", [])
                outcome["error"] = error
                raise
            finally:
                execution_git.make_writable(workspace.paths.scratch / "tmp")
            environment = {"environment_id": environment_id, "directory": str(env_dir), "head_commit": head, "plan_sha256": plan_sha, "config_sha256": row["config_sha256"], "binding_hash": selection.get("binding_hash"),
                           "setup": outcome["setup"], "processes": processes, "work_directory": str(work), "temporary_directory": str(workspace.paths.scratch / "tmp"),
                           "note": "Setup already ran inside your sandbox in output/work with HOME=scratch/home and TMPDIR=scratch/tmp; locations it created are readable and writable by you. Product work happens in output/work."}
            (workspace.paths.output / "environment.json").write_bytes(_json(environment))
            (workspace.paths.output / "environment.json").chmod(0o644)

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="qa_agent",
                role_responsibilities=("Exercise the assembled milestone's real user journeys and failure cases and report PASS, FAIL or UNTESTED honestly; never fix code or approve a merge.",),
                task=task, source_commit=head, decision_version=f"qa{v['attempt']}",
                instructions={"session_id": run_id, "claude_tools": _QA_TOOLS, "task_kind": "milestone_qa", "milestone": key},
                permitted_actions=("read_source", "write_output"), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("A required prerequisite is unavailable.",), response_schema=QA_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None, prepare)

        try:
            self._launch(row, pending, "qa_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], self._assignment_exists(assignment_id), build, "qa_agent",
                         save=lambda _a, p: self._set_v(activity_id, key, pending=p))
        except execution_qa.QaError as error:
            pending.pop("qa_run", None)
            self._set_v(activity_id, key, pending=pending)
            execution_qa.stop_processes(processes)
            clean = execution_qa.clean_environment(env_dir)
            self._untested_run(row, v, plan["id"], plan_sha, plan, str(error) + ("" if clean else "; the environment could not be removed and is quarantined"), outcome["setup"], environment_id)
            return
        except Exception:
            self._teardown(self._qa_run(activity_id, qa_run_id))
            raise
        pending["qa_run_id"] = qa_run_id
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_qa_runs SET assignment_id = ?, run_id = ?, agent_tool = ?, agent_model = ?, setup_json = ? WHERE activity_id = ? AND qa_run_id = ?",
                       (assignment_id, pending["qa_run"]["run_id"], route["tool"], route["model"], _dump(outcome["setup"]), activity_id, qa_run_id))
            tx.execute("UPDATE service_execution_verifications SET state = 'qa_running', note = NULL, pending_json = ?, updated_at = ? WHERE activity_id = ? AND milestone_key = ?", (canonical_json(pending), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id,
                      f"Quality Assurance for milestone {key} started (attempt {v['attempt']}): {route['tool']} {route['model']} runs plan {plan['id']} against {head[:12]} in isolated environment {environment_id}; "
                      f"{len(outcome['setup'])} setup step(s) ran in its sandbox, {len(processes)} support process(es) are healthy.")
            self._activity(tx, activity_id, "running", f"Quality Assurance is exercising milestone {key}")

    def _teardown(self, qa: Mapping[str, Any]) -> None:
        processes = json.loads(qa["processes_json"] or "[]")
        execution_qa.stop_processes(processes)
        clean = True
        if qa["environment_id"]:
            config = json.loads(self._read("SELECT config_json FROM service_executions WHERE activity_id = ?", (qa["activity_id"],))["config_json"])
            clean = execution_qa.clean_environment(Path(self._qa_settings(config)["environment_root"]) / qa["environment_id"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_qa_runs SET cleanup_state = ? WHERE activity_id = ? AND qa_run_id = ?", ("cleaned" if clean else "quarantined", qa["activity_id"], qa["qa_run_id"]))

    # ------------------------------------------------------------- QA: results

    def _qa_advance(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        assert self.runs is not None
        pending = json.loads(v["pending_json"] or "{}")
        current = pending.get("qa_run")
        if current is None:
            self._set_v(row["activity_id"], v["milestone_key"], state="qa")
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            self._qa_finish(row, config, v, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if int(assignment["automatic_used"]) >= int(assignment["automatic_limit"]):
                self._teardown(self._qa_run(row["activity_id"], pending["qa_run_id"]))
                self._qa_untested_after(row, v, pending, f"the Quality Assurance agent failed after the configured recovery attempts: {detail}")
                return
            pending.pop("qa_run", None)
            self._set_v(row["activity_id"], v["milestone_key"], pending=pending, state="qa")
            self._say_recovery(row, v, detail)
            return
        if view.state == "cancelled":
            return
        self._teardown(self._qa_run(row["activity_id"], pending["qa_run_id"]))
        self._qa_untested_after(row, v, pending, f"the Quality Assurance run {view.state}" + (f" ({view.failure_code})" if view.failure_code else ""))

    def _say_recovery(self, row: Mapping[str, Any], v: Mapping[str, Any], detail: str) -> None:
        with self.database.transaction() as tx:
            self._say(tx, row["project_id"], row["activity_id"], f"The Quality Assurance run for milestone {v['milestone_key']} failed ({detail}); the service prepares a fresh environment and tries again within the configured recovery limit.")

    def _qa_untested_after(self, row: Mapping[str, Any], v: dict[str, Any], pending: dict[str, Any], reason: str) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_qa_runs SET result = 'UNTESTED', reason = ?, finished_at = ? WHERE activity_id = ? AND qa_run_id = ?", (reason[:500], _now(), row["activity_id"], pending["qa_run_id"]))
        pending.pop("qa_run", None)
        self._set_v(row["activity_id"], v["milestone_key"], pending=pending)
        self._v_block(row, {**v, "pending_json": canonical_json(pending)}, f"Quality Assurance is UNTESTED: {reason}")

    @staticmethod
    def _qa_tampered(work: Path, head: str) -> str:
        """A pass counts only for the assigned commit: the tested checkout must still be at that commit with no tracked file changed."""
        import subprocess
        try:
            current = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=60, check=True).stdout.strip()
            changed = subprocess.run(["git", "-C", str(work), "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True, timeout=120, check=True).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            return "the tested checkout could not be verified against the assigned commit"
        if current != head or changed:
            return "the tested checkout no longer matches the assigned commit, so its results cannot be recorded against it"
        return ""

    def _qa_finish(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], v["milestone_key"]
        qa = self._qa_run(activity_id, pending["qa_run_id"])
        plan = json.loads(qa["plan_json"])
        response = self.runs.response(current["run_id"]) or {}
        output = self._run_workspace(current["run_id"])
        qa_config = self._qa_settings(config)
        destination_dir = Path(qa_config["artifact_root"]) / activity_id / qa["qa_run_id"]
        if output is None:
            self._teardown(qa)
            pending.pop("qa_run", None)
            self._qa_untested_after(row, v, {**pending, "qa_run_id": qa["qa_run_id"]}, "the Quality Assurance run's workspace is no longer available")
            return
        unreported = "the Quality Assurance agent did not report this check"
        if response.get("result") != "completed":
            unreported = "the Quality Assurance agent could not complete: " + ("; ".join(f"{q.get('subject')}: {q.get('reason')}" for q in response.get("questions", [])) or str(response.get("summary", "no reason given")))[:400]
            response = {**response, "checks": [], "environment_notes": response.get("environment_notes", "") or str(response.get("summary", ""))}
        tampered = self._qa_tampered(output / "work", qa["head_commit"])
        if tampered:
            response = {**response, "checks": []}
            unreported = tampered
        reported = {c["subject"]: c for c in response["checks"]}
        checks: list[dict[str, Any]] = []
        stored: list[dict[str, Any]] = []
        for planned in plan["checks"]:
            subject = planned["subject"]
            agent = reported.get(subject)
            reasons: list[str] = []
            captured: list[dict[str, Any]] = []
            if agent is None:
                result = "UNTESTED"
                reasons.append(unreported)
                entry = {"subject": subject, "journey_run": "", "data_source": "", "input_path": "", "expected": "", "actual": "", "limitations": [], "bypassed_paths": [], "requested_correction": None}
            else:
                entry = {k: agent[k] for k in ("subject", "journey_run", "data_source", "input_path", "expected", "actual", "limitations", "bypassed_paths", "requested_correction")}
                result = agent["result"]
                for artifact in agent["artifacts"]:
                    try:
                        relative = artifact["path"][len("output/"):] if artifact["path"].startswith("output/") else artifact["path"]
                        info = execution_qa.store_artifact(output / relative, output, destination_dir, qa_config["secret_patterns"], int(qa_config["maximum_artifact_bytes"]))
                    except execution_qa.QaError as error:
                        reasons.append(str(error))
                        continue
                    captured.append({**info, "description": artifact["description"], "declared_media_type": artifact["media_type"]})
                if agent["bypassed_paths"]:
                    result = "UNTESTED"
                    reasons.append("required path(s) bypassed by test data or a mock: " + "; ".join(agent["bypassed_paths"]))
                if result == "PASS" and (not captured or not agent["actual"].strip() or not agent["expected"].strip()):
                    result = "UNTESTED"
                    reasons.append("a pass needs captured evidence and stated expected and actual results")
                if result == "PASS" and len(captured) < len(planned.get("required_artifacts", [])):
                    result = "UNTESTED"
                    reasons.append(f"the plan requires {len(planned['required_artifacts'])} artifact(s) for this check but {len(captured)} were captured")
                if result == "PASS" and reasons:
                    result = "UNTESTED"
            stored.extend({**a, "check_subject": subject} for a in captured)
            checks.append({**entry, "result": result, "reasons": reasons, "artifact_ids": [a["artifact_id"] for a in captured]})
        setup_log = execution_qa.store_bytes("setup-log.json", _json({"environment_id": qa["environment_id"], "environment_sha256": qa["environment_sha256"], "setup": json.loads(qa["setup_json"]),
                                                                    "processes": json.loads(qa["processes_json"]), "data": json.loads(qa["data_json"]), "notes": response.get("environment_notes", "")}), destination_dir, "application/json")
        stored.append({**setup_log, "check_subject": "(environment)", "description": "Setup steps, support processes, data lineage and the agent's environment notes"})
        overall = "FAIL" if any(c["result"] == "FAIL" for c in checks) else "UNTESTED" if any(c["result"] == "UNTESTED" for c in checks) else "PASS"
        self._teardown(qa)
        cleanup = self._qa_run(activity_id, qa["qa_run_id"])["cleanup_state"]
        now = _now()
        with self.database.transaction() as tx:
            for a in stored:
                tx.execute("INSERT INTO service_execution_qa_artifacts(activity_id, artifact_id, qa_run_id, milestone_key, check_subject, kind, path, sha256, size, media_type, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (activity_id, a["artifact_id"], qa["qa_run_id"], key, a["check_subject"], "environment" if a["check_subject"] == "(environment)" else "evidence", a["path"], a["sha256"], a["size"], a["media_type"], a["description"][:500], now))
            tx.execute("UPDATE service_execution_qa_runs SET result = ?, checks_json = ?, finished_at = ?, reason = ? WHERE activity_id = ? AND qa_run_id = ?",
                       (overall, _dump(checks), now, response.get("environment_notes", "")[:500], activity_id, qa["qa_run_id"]))
            failed = [c["subject"] for c in checks if c["result"] == "FAIL"]
            untested = [c["subject"] for c in checks if c["result"] == "UNTESTED"]
            self._say(tx, row["project_id"], activity_id,
                      f"Quality Assurance for milestone {key} finished: {overall} ({sum(1 for c in checks if c['result'] == 'PASS')} pass, {len(failed)} fail, {len(untested)} untested); {len(stored)} artifact(s) stored with hashes; environment {cleanup}."
                      + (f" Failed: {', '.join(failed)}." if failed else "") + (f" Untested: {', '.join(untested)}." if untested else ""))
            self._emit(tx, row["project_id"], activity_id, "execution.qa_finished", {"milestone": key, "result": overall, "run": qa["qa_run_id"]})
        pending.pop("qa_run", None)
        if overall == "PASS":
            self._set_v(activity_id, key, pending=pending, state="reviewing", note=None)
        elif failed:
            self._cycle_findings(row, config, v, pending, "quality_assurance", [{
                "subject": f"Quality Assurance failed: {c['subject']}"[:200], "explanation": f"Expected: {c['expected']} Actual: {c['actual']}", "impact": f"The milestone's planned check '{c['subject']}' does not pass, so the milestone cannot be promoted.",
                "requested_correction": c["requested_correction"] or "Correct the behavior so the planned check passes.", "evidence": [f"QA run {qa['qa_run_id']}", f"artifact(s): {', '.join(c['artifact_ids']) or 'none'}", f"attempt {v['attempt']} at {v['head_commit'][:12]}"]}
                for c in checks if c["result"] == "FAIL"])
        else:
            self._set_v(activity_id, key, pending=pending, state="blocked", note=("Quality Assurance is UNTESTED, which blocks promotion: " + "; ".join(f"{c['subject']}: {' / '.join(c['reasons']) or 'not verified'}" for c in checks if c["result"] == "UNTESTED"))[:500])
            with self.database.transaction() as tx:
                self._event(tx, activity_id, "milestone_untested", None, f"milestone {key} has untested required paths and cannot pass")

    # --------------------------------------------------- findings and correction

    def _limit(self, config: Mapping[str, Any], activity_id: str, key: str) -> int:
        grants = 0
        for arch in self._architects(activity_id, "milestone_gap"):
            if json.loads(arch["trigger_json"]).get("milestone_key") == key and json.loads(arch["pending_json"] or "{}").get("owner_decision", {}).get("choice") == "grant_one":
                grants += 1
        return int(config["reviews"].get("milestone", {}).get("maximum_completed_rounds", 2)) + grants

    def _cycle_findings(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any], pending: dict[str, Any], source: str, items: list[dict[str, Any]]) -> None:
        """Record this cycle's blocking findings through the milestone-gap path; the cycle counts once against the milestone review allowance."""
        activity_id, key = row["activity_id"], v["milestone_key"]
        rounds = int(v["rounds_used"]) + 1
        exhausted = rounds >= self._limit(config, activity_id, key)
        ids: list[str] = []
        with self.database.transaction() as tx:
            for item in items:
                record = {"milestone_key": key, "source": source, "subject": item["subject"], "explanation": item["explanation"], "impact": item["impact"], "requested_correction": item["requested_correction"],
                          "evidence": item["evidence"], "review_limit_exhausted": exhausted}
                digest = hashlib.sha256(canonical_json(record).encode()).hexdigest()
                duplicate = self._row(tx, "SELECT finding_id FROM service_execution_findings WHERE activity_id = ? AND record_sha256 = ? AND state != 'closed'", (activity_id, digest))
                ids.append(duplicate["finding_id"] if duplicate else self._route_finding(tx, row, row["project_id"], activity_id, record, digest)[0])
            pending["findings"] = ids
            state = "limit_paused" if exhausted else "correcting"
            tx.execute("UPDATE service_execution_verifications SET state = ?, rounds_used = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND milestone_key = ?",
                       (state, rounds, canonical_json(pending), ("the milestone review allowance is used up with blocking findings; the Owner may grant one extra attempt" if exhausted else f"{len(ids)} finding(s) go through the correction path, then the corrected head is verified again"), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Milestone {key} verification cycle {rounds} of {self._limit(config, activity_id, key)} found {len(ids)} blocking issue(s) ({source.replace('_', ' ')}): "
                      + "; ".join(i["subject"] for i in items)[:400] + (". The allowance is exhausted, so the Owner decides whether to grant one more attempt." if exhausted else ". Each goes to the Project Architect for a determination; corrections follow normal review and integration."))

    def _correcting(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        activity_id, key = row["activity_id"], v["milestone_key"]
        pending = json.loads(v["pending_json"] or "{}")
        waiting: list[str] = []
        for finding_id in pending.get("findings", []):
            finding = self._finding(activity_id, finding_id)
            if finding["state"] == "reregistration_required":
                waiting.append(f"{finding_id} needs re-registration and an Owner disposition")
                continue
            arch = self._read("SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, finding["gap_key"]))
            if arch is None or arch["state"] not in ("active", "decided"):
                waiting.append(f"{finding_id} is waiting for the architect's determination ({arch['state'] if arch else 'missing'}{': ' + arch['note'] if arch and arch['note'] else ''})")
        if not waiting:
            packets, queue, deliveries = self._packets(activity_id), self._queue(activity_id), self._deliveries(activity_id)
            if not self._milestone_ready(activity_id, key, packets, queue, deliveries):
                waiting.append("correction work for the milestone is still being coded, reviewed or integrated")
        if waiting:
            note = "; ".join(waiting)[:500]
            if v["note"] != note:
                self._set_v(activity_id, key, note=note)
            return
        head = self._current_milestone_head(row, key)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_verifications SET state = 'qa', attempt = attempt + 1, head_commit = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND milestone_key = ?", (head, _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Corrections for milestone {key} are integrated (head {head[:12]}). Quality Assurance and outcome review run again on the exact new head; earlier evidence stays on record and the review count carries over.")

    def _limit_check(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        if int(v["rounds_used"]) < self._limit(config, row["activity_id"], v["milestone_key"]):
            self._set_v(row["activity_id"], v["milestone_key"], state="correcting", note="one extra attempt was granted; corrections go through the normal path")

    # ----------------------------------------------------------- outcome review

    def _milestone_authors(self, activity_id: str, key: str) -> set[tuple[str, str]]:
        authors = {(p["tool"], p["model"]) for p in self._packets(activity_id) if p["milestone_key"] == key and p["tool"]}
        for entry in self._queue(activity_id):
            if entry["milestone_key"] == key:
                integrator = json.loads(entry["pending_json"] or "{}").get("integrator")
                if integrator:
                    authors.add((integrator["tool"], integrator["model"]))
        return authors

    def _mr_route(self, config: Mapping[str, Any], authors: set[tuple[str, str]], qa_agent: tuple[str, str] | None) -> dict[str, Any]:
        pair = config.get("milestone_reviewers") or config.get("integration_reviewers") or config["reviewers"]["packet"]
        for name in ("primary", "backup"):
            candidate = pair.get(name)
            if candidate and (candidate["tool"], candidate["model"]) not in authors:
                return candidate
        raise AgentRunError("no_independent_reviewer", "no configured milestone reviewer differs from every author and the Integration Manager of this milestone")

    def _mr_inputs(self, row: Mapping[str, Any], v: Mapping[str, Any], qa: Mapping[str, Any], base: str) -> dict[str, bytes]:
        activity_id, key = row["activity_id"], v["milestone_key"]
        milestone = self._milestones(activity_id)[key]
        packets = []
        for p in self._packets(activity_id):
            if p["milestone_key"] != key:
                continue
            packets.append({"key": p["packet_key"], "subject": p["subject"], "state": p["state"], "head_commit": p["head_commit"], "review_rounds": p["rounds_used"], "record": json.loads(p["record_json"])})
        integration = {"queue": [{"entry": e["entry_id"], "kind": e["kind"], "packet": e["packet_key"], "delivery": e["delivery_id"], "state": e["state"], "merged_commit": e["merged_commit"]} for e in self._queue(activity_id) if e["milestone_key"] == key],
                       "deliveries": [{"id": d["delivery_id"], "provider": d["provider_milestone"], "state": d["state"], "source_commit": d["source_commit"], "packets": json.loads(d["packet_set_json"])} for d in self._deliveries(activity_id) if d["consumer_milestone"] == key]}
        artifacts = self._rows("SELECT artifact_id, check_subject, sha256, size, media_type, description FROM service_execution_qa_artifacts WHERE activity_id = ? AND qa_run_id = ?", (activity_id, qa["qa_run_id"]))
        mirror = self._mirror(row["project_id"])
        diff = execution_git.diff_text(mirror, base, v["head_commit"]) if base != v["head_commit"] else ""
        return {
            "milestone.json": milestone["record_json"].encode("utf-8"), "range.json": _json({"base": base, "head": v["head_commit"], "branch": milestone["branch"]}),
            "diff.patch": diff.encode("utf-8"), "packets.json": _json(packets), "integration.json": _json(integration),
            "qa-plan.json": qa["plan_json"].encode("utf-8"),
            "qa-result.json": _json({"result": qa["result"], "checks": json.loads(qa["checks_json"]), "artifacts": artifacts, "environment_sha256": qa["environment_sha256"], "cleanup": qa["cleanup_state"], "head_commit": qa["head_commit"]}),
        }

    def _mr_start(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any], pending: dict[str, Any], recovery_note: str | None = None) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], v["milestone_key"]
        milestone = self._milestones(activity_id)[key]
        head = v["head_commit"]
        qa = self._read("SELECT * FROM service_execution_qa_runs WHERE activity_id = ? AND qa_run_id = ?", (activity_id, f"{activity_id}-{key}-qa{v['attempt']}"))
        assert qa is not None
        route = self._mr_route(config, self._milestone_authors(activity_id, key), (qa["agent_tool"], qa["agent_model"]))
        base = milestone["base_commit"]
        mirror = self._mirror(row["project_id"])
        self._dest(row).fetch_source(row["repository"], head, mirror)
        assignment_id = f"{activity_id}-{key}-mreview-{v['attempt']}"
        inputs = self._mr_inputs(row, v, qa, base)
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _MILESTONE_REVIEW_TASK.format(head=head) + note

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="milestone_reviewer",
                role_responsibilities=("Decide whether the exact assembled milestone delivers its promised outcome; never edit code or authorize a merge.",),
                task=task, source_commit=head, decision_version=f"mr{v['attempt']}",
                instructions={"session_id": run_id, "claude_tools": _REVIEW_TOOLS, "task_kind": "review_milestone", "milestone": key},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("The range cannot be verified.",), response_schema=REVIEWER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "review_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "milestone_reviewer",
                     save=lambda _a, p: self._set_v(activity_id, key, pending=p))
        pending["reviewer"] = {"tool": route["tool"], "model": route["model"], "base": base}
        self._set_v(activity_id, key, pending=pending, note=None)
        with self.database.transaction() as tx:
            self._say(tx, row["project_id"], activity_id, f"Independent outcome review of milestone {key} started: {route['tool']} {route['model']} reviews exactly {head[:12]} against the milestone's criteria and the Quality Assurance evidence (authors and integrator differ).")
            self._activity(tx, activity_id, "running", f"Reviewing the outcome of milestone {key}")

    def _mr_advance(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], v["milestone_key"]
        if self._current_milestone_head(row, key) != v["head_commit"]:
            self._invalidate(row, v, "the milestone branch moved after Quality Assurance, so the evidence no longer covers it")
            return
        pending = json.loads(v["pending_json"] or "{}")
        current = pending.get("review_run")
        if current is None:
            self._mr_start(row, config, v, pending)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            self._mr_accept(row, config, v, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if int(assignment["automatic_used"]) >= int(assignment["automatic_limit"]):
                self._v_block(row, v, f"the outcome reviewer failed after the configured recovery attempts: {detail}")
                return
            pending.pop("review_run", None)
            self._set_v(activity_id, key, pending=pending)
            self._mr_start(row, config, {**v, "pending_json": canonical_json(pending)}, pending, recovery_note=detail)
            return
        if view.state == "cancelled":
            return
        self._v_block(row, v, f"the outcome review run {view.state}" + (f" ({view.failure_code})" if view.failure_code else ""))

    def _mr_accept(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], v["milestone_key"]
        response = self.runs.response(current["run_id"]) or {}
        reviewer = pending["reviewer"]
        expected = {"base": reviewer["base"], "head": v["head_commit"]}
        if response.get("result") != "completed" or response.get("reviewed_range") != expected:
            self.runs.reject_result(current["run_id"], "conflicting_response", "the review does not state the exact range it was given")
            pending.pop("review_run", None)
            if self.runs.assignment_state(current["assignment_id"])["state"] != "needs_recovery":
                self._v_block(row, v, "the outcome review did not state the exact revision it reviewed")
                return
            self._set_v(activity_id, key, pending=pending)
            self._mr_start(row, config, {**v, "pending_json": canonical_json(pending)}, pending, recovery_note="the review must copy reviewed_range exactly from input/range.json")
            return
        findings = [{**f, "finding_id": f"{activity_id}-{key}-a{v['attempt']}-{f['local_key']}"} for f in response.get("findings", [])]
        blocking = [f for f in findings if f["severity"] == "blocking"]
        outcome = response["review_outcome"]
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT INTO service_execution_milestone_reviews(activity_id, milestone_key, attempt, assignment_id, run_id, reviewer_tool, reviewer_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (activity_id, key, v["attempt"], current["assignment_id"], current["run_id"], reviewer["tool"], reviewer["model"], expected["base"], expected["head"], outcome, str(response["summary"])[:2000], _dump(findings), str(response.get("independence", ""))[:500], _now()))
            self._say(tx, row["project_id"], activity_id, f"Outcome review of milestone {key}: {outcome} at {v['head_commit'][:12]} by {reviewer['tool']} {reviewer['model']}. {str(response['summary'])[:300]}")
            self._emit(tx, row["project_id"], activity_id, "execution.milestone_reviewed", {"milestone": key, "outcome": outcome})
        pending.pop("review_run", None)
        if outcome == "APPROVE":
            self._set_v(activity_id, key, pending=pending, state="promoting", note=None)
            return
        self._cycle_findings(row, config, v, pending, "outcome_review", [{
            "subject": f["subject"][:200], "explanation": f["explanation"], "impact": f["impact"], "requested_correction": f["requested_correction"],
            "evidence": [f"outcome review of {key}", f"attempt {v['attempt']} at {v['head_commit'][:12]}", *[f"{loc['path']} {loc['locator']}" for loc in f["locations"]]]} for f in blocking])

    def _invalidate(self, row: Mapping[str, Any], v: dict[str, Any], reason: str) -> None:
        """Evidence no longer covers the branch: verify the current head from the start; the earlier records stay."""
        head = self._current_milestone_head_or_recorded(row, v["milestone_key"])
        pending = json.loads(v["pending_json"] or "{}")
        pending.pop("review_run", None)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_verifications SET state = 'qa', attempt = attempt + 1, head_commit = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND milestone_key = ?",
                       (head, canonical_json(pending), _now(), row["activity_id"], v["milestone_key"]))
            self._say(tx, row["project_id"], row["activity_id"], f"Milestone {v['milestone_key']}: {reason}. Quality Assurance and outcome review restart on the current head; the earlier evidence stays as history.")

    def _current_milestone_head_or_recorded(self, row: Mapping[str, Any], key: str) -> str:
        milestone = self._milestones(row["activity_id"])[key]
        remote = self._dest(row).branch_head(row["repository"], milestone["branch"])
        return remote or str(milestone["head_commit"])

    # --------------------------------------------------------------- promotion

    def _master_head(self, row: Mapping[str, Any]) -> str:
        """The product default-branch head this service last wrote (or the start head): the target the evidence was checked against."""
        found = self._read("SELECT master_after FROM service_execution_verifications WHERE activity_id = ? AND master_after IS NOT NULL ORDER BY master_seq DESC LIMIT 1", (row["activity_id"],))
        return str(found["master_after"]) if found else str(row["master_commit"])

    def _promotion_blockers(self, row: Mapping[str, Any], v: Mapping[str, Any]) -> tuple[str | None, str | None]:
        """A reason the gates are not met, and 'wait' when the reason is only another milestone's promotion still pending."""
        activity_id, key = row["activity_id"], v["milestone_key"]
        qa = self._read("SELECT * FROM service_execution_qa_runs WHERE activity_id = ? AND qa_run_id = ?", (activity_id, f"{activity_id}-{key}-qa{v['attempt']}"))
        review = self._read("SELECT * FROM service_execution_milestone_reviews WHERE activity_id = ? AND milestone_key = ? AND attempt = ?", (activity_id, key, v["attempt"]))
        if qa is None or qa["result"] != "PASS":
            return "Quality Assurance has not passed for this head", None
        for artifact in self._rows("SELECT * FROM service_execution_qa_artifacts WHERE activity_id = ? AND qa_run_id = ?", (activity_id, qa["qa_run_id"])):
            problem = execution_qa.verify_stored({"artifact_id": artifact["artifact_id"], "path": artifact["path"], "size": artifact["size"], "sha256": artifact["sha256"]})
            if problem:
                return problem + "; the check is invalid until its evidence is captured again", "invalid"
        if review is None or review["outcome"] != "APPROVE" or review["reviewed_head"] != v["head_commit"]:
            return "the independent outcome review has not approved this exact head", None
        verifications = self._verifications(activity_id)
        milestones = self._milestones(activity_id)
        needed = set(json.loads(milestones[key]["dependencies_json"]))
        needed |= {d["provider_milestone"] for d in self._deliveries(activity_id) if d["consumer_milestone"] == key and d["state"] == "delivered"}
        for other in sorted(needed):
            if verifications.get(other, {}).get("state") not in ("publishing", "complete"):
                return f"milestone {other} must be promoted to the product's default branch first", "wait"
        return None, None

    def _promote(self, row: Mapping[str, Any], config: Mapping[str, Any], v: dict[str, Any]) -> None:
        activity_id, key = row["activity_id"], v["milestone_key"]
        pending = json.loads(v["pending_json"] or "{}")
        destination = self._dest(row)
        milestone = self._milestones(activity_id)[key]
        merging = pending.get("merging")
        if merging is None:
            problem, kind = self._promotion_blockers(row, v)
            if kind == "invalid":
                self._invalidate(row, v, str(problem))
                return
            if problem:
                if v["note"] != problem:
                    self._set_v(activity_id, key, note=problem)
                    if kind is None:
                        self._v_block(row, v, f"promotion refused: {problem}")
                return
            remote = destination.branch_head(row["repository"], milestone["branch"])
            if remote != v["head_commit"]:
                self._invalidate(row, v, "the milestone branch changed after its evidence was taken")
                return
            expected = self._master_head(row)
            target = destination.branch_head(row["repository"], row["master_branch"])
            if target != expected:
                self._v_block(row, v, f"promotion refused: the product's {row['master_branch']} branch is at {(target or 'nothing')[:12]}, not the {expected[:12]} this milestone was checked against; it must be reconciled first")
                return
            mirror = self._mirror(row["project_id"])
            for commit in (expected, v["head_commit"]):
                destination.fetch_source(row["repository"], commit, mirror)
            staging = self.state_dir / "execution" / activity_id / f"promote-{key}-a{v['attempt']}"
            shutil.rmtree(staging, ignore_errors=True)
            merge_commit = execution_git.merge_into(mirror, expected, v["head_commit"], staging, f"maestro-promote-{key}", f"Merge verified milestone {key} ({milestone['subject'][:100]}) into {row['master_branch']}")
            merging = {"commit": merge_commit, "clone": str(staging), "expected": expected}
            pending["merging"] = merging
            self._set_v(activity_id, key, pending=pending)
            self._journal_begin(row, f"{activity_id}-{key}-promote-a{v['attempt']}", key, "milestone_promotion", row["master_branch"], merge_commit, expected)
        operation_id = f"{activity_id}-{key}-promote-a{v['attempt']}"
        try:
            remote_after = destination.push_branch(row["repository"], Path(merging["clone"]), row["master_branch"], merging["commit"], expected_before=merging["expected"])
        except DestinationError as error:
            if error.code in {"github_unreachable", "push_failed"}:
                raise
            if error.code != "target_changed":
                self._journal_end(operation_id, "failed", None, f"{error.code}: {error}"[:300])
            pending.pop("merging", None)
            shutil.rmtree(merging["clone"], ignore_errors=True)
            self._set_v(activity_id, key, pending=pending)
            raise
        if not destination.contains(row["repository"], v["head_commit"], remote_after):
            raise DestinationError("verification_failed", "the product branch does not contain the verified milestone head after the merge")
        shutil.rmtree(merging["clone"], ignore_errors=True)
        pending.pop("merging", None)
        seq = 1 + int(self._read("SELECT COALESCE(MAX(master_seq), 0) AS n FROM service_execution_verifications WHERE activity_id = ?", (activity_id,))["n"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (remote_after, operation_id))
            tx.execute("UPDATE service_execution_verifications SET state = 'publishing', promoted_commit = ?, master_before = ?, master_after = ?, master_seq = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND milestone_key = ?",
                       (remote_after, merging["expected"], remote_after, seq, canonical_json(pending), _now(), activity_id, key))
            self._event(tx, activity_id, "milestone_promoted", None, f"milestone {key} merged into {row['master_branch']} at {remote_after[:12]}")
            self._say(tx, row["project_id"], activity_id, f"Both gates passed for milestone {key}: the service merged {v['head_commit'][:12]} into {row['master_branch']} without fast-forward (was {merging['expected'][:12]}, now {remote_after[:12]}) and verified it on the remote. Its completion record is published next.")
            self._emit(tx, row["project_id"], activity_id, "execution.milestone_promoted", {"milestone": key, "commit": remote_after})

    # -------------------------------------------------------------- completion

    def _milestone_record(self, row: Mapping[str, Any], v: Mapping[str, Any]) -> dict[str, Any]:
        activity_id, key = row["activity_id"], v["milestone_key"]
        milestone = self._milestones(activity_id)[key]
        qa = self._read("SELECT * FROM service_execution_qa_runs WHERE activity_id = ? AND qa_run_id = ?", (activity_id, f"{activity_id}-{key}-qa{v['attempt']}"))
        review = self._read("SELECT * FROM service_execution_milestone_reviews WHERE activity_id = ? AND milestone_key = ? AND attempt = ?", (activity_id, key, v["attempt"]))
        packets = [{"key": p["packet_key"], "subject": p["subject"], "head_commit": p["head_commit"], "review_rounds": p["rounds_used"]} for p in self._packets(activity_id) if p["milestone_key"] == key]
        queue = [{"entry": e["entry_id"], "kind": e["kind"], "packet": e["packet_key"], "delivery": e["delivery_id"], "merged_commit": e["merged_commit"], "review_rounds": e["rounds_used"]} for e in self._queue(activity_id) if e["milestone_key"] == key]
        artifacts = [{"artifact_id": a["artifact_id"], "check": a["check_subject"], "sha256": a["sha256"], "size": a["size"], "media_type": a["media_type"]}
                     for a in self._rows("SELECT * FROM service_execution_qa_artifacts WHERE activity_id = ? AND qa_run_id = ? ORDER BY artifact_id", (activity_id, qa["qa_run_id"]))]
        supplements = [{"supplement_id": s["supplement_id"], "version": s["version"], "sha256": s["record_sha256"], "finding": s["finding_id"]} for s in self._rows("SELECT * FROM service_execution_supplements WHERE activity_id = ? AND milestone_key = ?", (activity_id, key))]
        deliveries = [{"id": d["delivery_id"], "provider": d["provider_milestone"], "source_commit": d["source_commit"], "import_commit": d["import_commit"], "packets": json.loads(d["packet_set_json"])} for d in self._deliveries(activity_id) if d["consumer_milestone"] == key and d["state"] == "delivered"]
        operations = [{"operation": j["operation_id"], "kind": j["kind"], "branch": j["branch"], "remote_after": j["remote_after"]} for j in self._rows("SELECT * FROM service_execution_journal WHERE activity_id = ? AND state = 'verified' AND (packet_key = ? OR kind = 'milestone_promotion' AND packet_key = ?) ORDER BY created_at", (activity_id, key, key))]
        findings = [{"finding": f["finding_id"], "source": f["source"], "subject": f["subject"], "state": f["state"]} for f in self._rows("SELECT * FROM service_execution_findings WHERE activity_id = ? AND milestone_key = ?", (activity_id, key))]
        confirmed = json.loads(row["confirmed_ref_json"])
        return {
            "schema_version": 1, "kind": "milestone-completion", "project_id": row["project_id"], "activity_id": activity_id, "registration_activity_id": row["registration_activity_id"], "source_commit": row["source_commit"],
            "breakdown": {k: confirmed[k] for k in ("version", "commit", "manifest_path")}, "milestone": {"id": key, "subject": milestone["subject"], "record_sha256": milestone["record_sha256"]},
            "configuration": {"sha256": row["config_sha256"], "bundle": json.loads(row["bundle_json"])},
            "baseline_commit": milestone["base_commit"], "branch": milestone["branch"], "milestone_head_commit": v["head_commit"], "final_merge_commit": v["promoted_commit"], "master_before": v["master_before"],
            "packets": packets, "integration_queue": queue, "supplements": supplements, "dependency_deliveries": deliveries, "findings": findings,
            "review_counts": {"milestone_verification_cycles": v["rounds_used"], "attempts": v["attempt"]},
            "quality_assurance": {"run_id": qa["qa_run_id"], "result": qa["result"], "plan": {"id": qa["plan_id"], "version": qa["plan_version"], "sha256": qa["plan_sha256"]}, "binding_hash": qa["binding_hash"], "environment_sha256": qa["environment_sha256"],
                                  "cleanup": qa["cleanup_state"], "checks": [{"subject": c["subject"], "result": c["result"]} for c in json.loads(qa["checks_json"])], "artifacts": artifacts},
            "outcome_review": {"reviewer": f"{review['reviewer_tool']} {review['reviewer_model']}", "outcome": review["outcome"], "reviewed_base": review["reviewed_base"], "reviewed_head": review["reviewed_head"],
                               "non_blocking_observations": [f["subject"] for f in json.loads(review["findings_json"]) if f["severity"] != "blocking"]},
            "repository_operations": operations, "started_at": v["created_at"],
        }

    def _publish_milestone(self, row: Mapping[str, Any], v: dict[str, Any]) -> None:
        activity_id, key = row["activity_id"], v["milestone_key"]
        pending = json.loads(v["pending_json"] or "{}")
        destination = self._dest(row)
        if "completion" not in pending:
            record = self._milestone_record(row, v)
            record["completed_at"] = _now()
            data = encode(record)
            path = f".maestro/execution/{activity_id}/milestones/{key}/completion/versions/1/completion.json"
            pending["completion"] = {"path": path, "sha256": _sha(data), "record": record}
            self._set_v(activity_id, key, pending=pending)
        completion = pending["completion"]
        data = encode(completion["record"])
        if _sha(data) != completion["sha256"]:
            raise DestinationError("verification_failed", "the saved milestone completion record changed before publication")
        operation_id = f"{activity_id}-{key}-completion-v1"
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE operation_id = ?", (operation_id,)) is None:
            self._journal_begin(row, operation_id, key, "milestone_completion_publish", row["master_branch"], completion["sha256"], destination.branch_head(row["repository"], row["master_branch"]))
        destination.check_code_branch(row["repository"], row["master_branch"])
        try:
            commit = destination.publish(row["repository"], row["master_branch"], {completion["path"]: data}, f"Execution {activity_id}: milestone {key} completion record version 1")
        except DestinationError as error:
            if error.code in {"github_unreachable", "publication_failed", "branch_unverifiable"}:
                raise
            self._journal_end(operation_id, "failed", None, f"{error.code}: {error}"[:300])
            raise
        destination.verify_files(row["repository"], commit, {completion["path"]: data})
        if not destination.contains(row["repository"], v["promoted_commit"], commit):
            raise DestinationError("verification_failed", "the completion commit does not contain the verified merge")
        seq = 1 + int(self._read("SELECT COALESCE(MAX(master_seq), 0) AS n FROM service_execution_verifications WHERE activity_id = ?", (activity_id,))["n"])
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (commit, operation_id))
            tx.execute("UPDATE service_execution_verifications SET state = 'complete', completion_path = ?, completion_sha256 = ?, completion_commit = ?, master_after = ?, master_seq = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND milestone_key = ?",
                       (completion["path"], completion["sha256"], commit, commit, seq, _now(), activity_id, key))
            self._event(tx, activity_id, "milestone_complete", None, f"milestone {key} is complete: record {completion['path']} in {commit[:12]}")
            self._say(tx, row["project_id"], activity_id, f"Milestone {key} is complete: its completion record ({completion['path']}, SHA-256 {completion['sha256'][:12]}) is published in {commit[:12]} on {row['master_branch']} and its bytes were read back and verified.")
            self._emit(tx, row["project_id"], activity_id, "execution.milestone_complete", {"milestone": key, "commit": commit})

    def _release_held_deliveries(self, row: Mapping[str, Any]) -> None:
        """A delivery held for a provider milestone's completion is queued once that milestone is complete, importing its exact verified head."""
        activity_id = row["activity_id"]
        verifications = self._verifications(activity_id)
        for delivery in self._deliveries(activity_id):
            provider = verifications.get(delivery["provider_milestone"])
            if delivery["state"] != "held" or provider is None or provider["state"] != "complete":
                continue
            with self.database.transaction() as tx:
                entry_id = self._enqueue(tx, row, "dependency_import", None, delivery["delivery_id"], delivery["consumer_milestone"], provider["head_commit"])
                tx.execute("UPDATE service_execution_deliveries SET state = 'queued', queue_entry = ?, source_commit = ?, note = ?, updated_at = ? WHERE activity_id = ? AND delivery_id = ? AND state = 'held'",
                           (entry_id, provider["head_commit"], f"provider milestone completion record {provider['completion_path']}", _now(), activity_id, delivery["delivery_id"]))
                self._say(tx, row["project_id"], activity_id, f"Milestone {delivery['provider_milestone']} is complete, so held dependency delivery {delivery['delivery_id']} imports its exact verified head {provider['head_commit'][:12]} into milestone {delivery['consumer_milestone']} (queue entry {entry_id}).")

    def _advance_completion(self, row: Mapping[str, Any]) -> None:
        """Publish the Execution completion record and end the activity once every authorized milestone is complete and nothing is unfinished or uncertain."""
        activity_id = row["activity_id"]
        milestones = self._milestones(activity_id)
        verifications = self._verifications(activity_id)
        if not milestones or any(verifications.get(k, {}).get("state") != "complete" for k in milestones):
            return
        pending = json.loads(row["pending_json"] or "{}")
        blockers = self._unfinished(row, pending)
        if blockers:
            return
        destination = self._dest(row)
        stored = self._read("SELECT * FROM service_execution_completion WHERE activity_id = ?", (activity_id,))
        if stored is None:
            final = self._master_head(row)
            confirmed = json.loads(row["confirmed_ref_json"])
            ordered = sorted(verifications.values(), key=lambda x: x["master_seq"])
            observations = sorted({f["subject"] for m in verifications.values() for r in self._rows("SELECT findings_json FROM service_execution_milestone_reviews WHERE activity_id = ? AND milestone_key = ?", (activity_id, m["milestone_key"]))
                                   for f in json.loads(r["findings_json"]) if f["severity"] != "blocking"})
            record = {
                "schema_version": 1, "kind": "completed", "record": "execution-completion@1", "project_id": row["project_id"], "activity_id": activity_id, "registration_activity_id": row["registration_activity_id"],
                "breakdown": {k: confirmed[k] for k in ("version", "commit", "manifest_path")}, "configuration": {"sha256": row["config_sha256"], "bundle": json.loads(row["bundle_json"])},
                "milestones": [{"id": m["milestone_key"], "completion_path": m["completion_path"], "completion_sha256": m["completion_sha256"], "completion_commit": m["completion_commit"], "merge_commit": m["promoted_commit"]} for m in ordered],
                "product_master": {"branch": row["master_branch"], "start_commit": row["master_commit"], "final_commit": final},
                "unresolved_work": {"assertion": "none", "packets_not_integrated": [], "open_findings": [], "queue_entries_open": [], "external_operations_open": []},
                "non_blocking_observations": observations,
                "started_at": row["created_at"], "completed_at": _now(),
            }
            path = f".maestro/execution/{activity_id}/completion/versions/1/completion.json"
            data = encode(record)
            with self.database.transaction() as tx:
                tx.execute("INSERT INTO service_execution_completion(activity_id, state, path, sha256, record_json, final_master, created_at, updated_at) VALUES (?, 'prepared', ?, ?, ?, ?, ?, ?)",
                           (activity_id, path, _sha(data), canonical_json(record), final, _now(), _now()))
            stored = self._read("SELECT * FROM service_execution_completion WHERE activity_id = ?", (activity_id,))
        data = encode(json.loads(stored["record_json"]))
        if _sha(data) != stored["sha256"]:
            raise DestinationError("verification_failed", "the saved Execution completion record changed before publication")
        operation_id = f"{activity_id}-execution-completion-v1"
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE operation_id = ?", (operation_id,)) is None:
            self._journal_begin(row, operation_id, "execution", "execution_completion_publish", row["master_branch"], stored["sha256"], destination.branch_head(row["repository"], row["master_branch"]))
        destination.check_code_branch(row["repository"], row["master_branch"])
        remote_head = destination.branch_head(row["repository"], row["master_branch"])
        if remote_head != stored["final_master"] and stored["commit_sha"] is None:
            raise DestinationError("target_changed", f"the product's {row['master_branch']} branch moved from {stored['final_master'][:12]} to {(remote_head or 'nothing')[:12]}; Execution completion pauses until it is reconciled", remote=remote_head)
        commit = destination.publish(row["repository"], row["master_branch"], {stored["path"]: data}, f"Execution {activity_id}: completion record version 1")
        destination.verify_files(row["repository"], commit, {stored["path"]: data})
        for m in verifications.values():
            if not destination.contains(row["repository"], m["promoted_commit"], commit):
                raise DestinationError("verification_failed", f"the product branch does not contain the verified merge of milestone {m['milestone_key']}")
        with self.database.transaction() as tx:
            current = self._row(tx, "SELECT state, pending_json FROM service_executions WHERE activity_id = ?", (activity_id,))
            if current is None or current["state"] not in ("running", "blocked", "finishing"):
                return
            saved = (json.loads(current["pending_json"] or "{}").get("settlement") or {}).get("kind")
            if saved == "pause" or (current["state"] == "finishing" and saved != "stop"):
                return  # a pause accepted during publication completes after resume; the publication is idempotent
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (commit, operation_id))
            tx.execute("UPDATE service_execution_completion SET state = 'published', commit_sha = ?, updated_at = ? WHERE activity_id = ?", (commit, _now(), activity_id))
            tx.execute("UPDATE service_executions SET state = 'completed', note = 'all milestones verified and promoted' WHERE activity_id = ?", (activity_id,))
            self.reservations.release(tx, row["project_id"], activity_id)
            text = (f"Execution is complete. All {len(verifications)} milestone(s) passed isolated Quality Assurance and independent outcome review and were merged into {row['master_branch']}; "
                    f"the completion record {stored['path']} (SHA-256 {stored['sha256'][:12]}) is published in {commit[:12]} and verified.")
            self._activity(tx, activity_id, "completed", text)
            self._event(tx, activity_id, "execution_complete", None, text[:400])
            self._say(tx, row["project_id"], activity_id, text)
            self._emit(tx, row["project_id"], activity_id, "execution.completed", {"commit": commit, "path": stored["path"]})

    def _finding_open(self, activity_id: str, finding: Mapping[str, Any]) -> bool:
        if finding["state"] == "reregistration_required":
            return True
        arch = self._read("SELECT state FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, finding["gap_key"]))
        return arch is None or arch["state"] not in ("active", "decided")

    def _unfinished(self, row: Mapping[str, Any], pending: Mapping[str, Any]) -> list[str]:
        activity_id = row["activity_id"]
        reasons: list[str] = []
        if any(p["state"] != "integrated" for p in self._packets(activity_id)):
            reasons.append("packets are not integrated")
        if any(e["state"] in _QUEUE_OPEN for e in self._queue(activity_id)):
            reasons.append("the integration queue has open entries")
        if any(d["state"] in ("queued", "held") for d in self._deliveries(activity_id)):
            reasons.append("dependency deliveries are open")
        if any(a["state"] not in ("active", "decided", "superseded", "disposition_recorded") for a in self._architects(activity_id)):
            reasons.append("an architect assignment is open")
        if any(f["state"] in ("routed", "reregistration_required") and self._finding_open(activity_id, f) for f in self._rows("SELECT * FROM service_execution_findings WHERE activity_id = ?", (activity_id,))):
            reasons.append("a finding is unresolved")
        if pending.get("manager_run") is not None or any(not q.get("answered") for q in pending.get("questions", {}).values()):
            reasons.append("the Development Manager is active or a question is open")
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE activity_id = ? AND state = 'prepared' AND kind NOT LIKE '%completion_publish'", (activity_id,)) is not None:
            reasons.append("a repository operation is unfinished")
        return reasons

    # ---------------------------------------------------------------- settle/view

    def _verification_status(self, activity_id: str) -> tuple[int, list[str]]:
        """How many milestone verification steps are running, and the plain blockers to show while nothing else can move."""
        verifications = self._verifications(activity_id)
        running = sum(1 for v in verifications.values() if v["state"] in _ACTIVE)
        parts = []
        for key, v in sorted(verifications.items()):
            if v["state"] == "complete":
                parts.append(f"milestone {key} is complete and promoted")
            elif v["state"] in ("blocked", "limit_paused", "correcting"):
                parts.append(f"milestone {key}: {v['note'] or v['state']}")
        return running, parts

    def verification_view(self, activity_id: str) -> dict[str, Any]:
        verifications = self._verifications(activity_id)
        config = json.loads(self._read("SELECT config_json FROM service_executions WHERE activity_id = ?", (activity_id,))["config_json"])
        milestones = []
        for key, v in sorted(verifications.items()):
            runs = self._rows("SELECT * FROM service_execution_qa_runs WHERE activity_id = ? AND milestone_key = ? ORDER BY attempt", (activity_id, key))
            reviews = self._rows("SELECT * FROM service_execution_milestone_reviews WHERE activity_id = ? AND milestone_key = ? ORDER BY attempt", (activity_id, key))
            artifacts = self._rows("SELECT artifact_id, qa_run_id, check_subject, sha256, size, media_type, description, retention_state FROM service_execution_qa_artifacts WHERE activity_id = ? AND milestone_key = ? ORDER BY qa_run_id, artifact_id", (activity_id, key))
            milestones.append({
                "key": key, "state": v["state"], "attempt": v["attempt"], "head_commit": v["head_commit"], "note": v["note"], "cycles": {"used": v["rounds_used"], "limit": self._limit(config, activity_id, key)},
                "qa": [{"run": r["qa_run_id"], "attempt": r["attempt"], "head": r["head_commit"], "result": r["result"], "reason": r["reason"], "plan": {"id": r["plan_id"], "sha256": r["plan_sha256"]}, "binding_hash": r["binding_hash"],
                        "environment": r["environment_id"], "environment_sha256": r["environment_sha256"], "cleanup": r["cleanup_state"], "agent": f"{r['agent_tool']} {r['agent_model']}" if r["agent_tool"] else None,
                        "setup": [{"subject": s["subject"], "exit_code": s["exit_code"]} for s in json.loads(r["setup_json"])], "processes": [{"subject": p["subject"], "health": p["health"]} for p in json.loads(r["processes_json"])],
                        "data": [{"subject": d.get("subject"), "classification": d.get("classification"), "source": d.get("dataset_or_generator"), "path": d.get("real_input_path")} for d in json.loads(r["data_json"])],
                        "checks": [{"subject": c["subject"], "result": c["result"], "reasons": c.get("reasons", []), "expected": c.get("expected"), "actual": c.get("actual"), "limitations": c.get("limitations", []), "artifacts": c.get("artifact_ids", [])} for c in json.loads(r["checks_json"])]} for r in runs],
                "artifacts": artifacts,
                "reviews": [{"attempt": r["attempt"], "outcome": r["outcome"], "reviewer": f"{r['reviewer_tool']} {r['reviewer_model']}", "head": r["reviewed_head"], "summary": r["summary"],
                             "blocking": sum(1 for f in json.loads(r["findings_json"]) if f["severity"] == "blocking")} for r in reviews],
                "promotion": {"commit": v["promoted_commit"], "master_before": v["master_before"]} if v["promoted_commit"] else None,
                "completion": {"path": v["completion_path"], "sha256": v["completion_sha256"], "commit": v["completion_commit"]} if v["completion_commit"] else None,
            })
        completion = self._read("SELECT state, path, sha256, commit_sha, final_master FROM service_execution_completion WHERE activity_id = ?", (activity_id,))
        return {"milestones": milestones,
                "completion": None if completion is None else {"state": completion["state"], "path": completion["path"], "sha256": completion["sha256"], "commit": completion["commit_sha"], "final_master": completion["final_master"]}}

    def artifact_content(self, project_id: str, artifact_id: str) -> dict[str, Any] | None:
        """One stored artifact with its content, after re-checking size and hash; the caller has already authorized the read."""
        found = self._read("SELECT a.* FROM service_execution_qa_artifacts a JOIN service_executions e ON e.activity_id = a.activity_id WHERE e.project_id = ? AND a.artifact_id = ?", (project_id, artifact_id))
        if found is None:
            return None
        problem = execution_qa.verify_stored({"artifact_id": artifact_id, "path": found["path"], "size": found["size"], "sha256": found["sha256"]})
        meta = {k: found[k] for k in ("artifact_id", "qa_run_id", "milestone_key", "check_subject", "sha256", "size", "media_type", "description", "retention_state")}
        if problem:
            return {**meta, "verified": False, "problem": problem}
        data = Path(found["path"]).read_bytes()
        try:
            return {**meta, "verified": True, "text": data.decode("utf-8")}
        except UnicodeDecodeError:
            import base64
            return {**meta, "verified": True, "base64": base64.b64encode(data).decode()}
