"""Execution: explicit start, a persistent Development Manager, coders in isolated workspaces and independent packet review.

One Execution activity per project owns its packets in SQL. The worker thread calls ``tick`` repeatedly; every
step reads saved state, so a restart continues where the saved records say. Agents propose (a plan, a change, a
verdict); the service checks each proposal against saved state, does every Git write itself, and records a
revision as delivered only after it reads the remote branch back.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Collection, Iterable, Mapping

from maestro.agents.execution_contract import CODER_SCHEMA, DISPOSITION_CHOICES, MANAGER_SCHEMA, PLAN_KEYS, REVIEWER_SCHEMA
from maestro.agents.session_state import SessionUse
from maestro.agents.transport import AgentAssignment, _questions
from maestro.agents.architecture_contract import _question_view
from maestro.foundation import Database, DomainMigration, Transaction, canonical_json

from . import execution_config, execution_git
from .execution_integration import INTEGRATION_MIGRATION, IntegrationMixin, is_delivered
from .execution_milestones import MILESTONE_MIGRATION, MilestoneMixin
from .execution_determination import DeterminationMixin
from .execution_gaps import GAP_MIGRATION, GapMixin
from .execution_support import SUPPORT_MIGRATION, SupportMixin
from .activities import ActivityAction, ActivityRecord, ActivityRepository, ConversationRecord, QuestionRecord
from .agent_runs import AgentRunError, AgentRunService, RunBuild
from .questions import DeliveredAnswer, QuestionService, RecipientDeliveryInterrupted
from .registration_github import DestinationError, GitHubDestination, RepositoryProfile
from .registry import OperationHandler, OperationResult, PreparedOperation, RequestLike
from .requests import RequestRejection
from .reservations import ProjectReservations, ReservationError
from .resources import InstalledSchemaResources, ProcessResourceError

log = logging.getLogger("maestro.execution")

EXECUTION_MIGRATION = DomainMigration(
    domain="service_execution",
    version=1,
    identity="service-execution-v1",
    statements=(
        """
        CREATE TABLE service_executions(
            activity_id TEXT PRIMARY KEY REFERENCES service_activities(activity_id) ON DELETE RESTRICT,
            project_id TEXT NOT NULL REFERENCES service_projects(project_id) ON DELETE RESTRICT,
            registration_activity_id TEXT NOT NULL,
            architecture_activity_id TEXT NOT NULL,
            registration_json TEXT NOT NULL,
            confirmed_ref_json TEXT NOT NULL,
            repository TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            source_commit TEXT NOT NULL,
            master_branch TEXT NOT NULL,
            master_commit TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            config_json TEXT NOT NULL,
            config_sha256 TEXT NOT NULL,
            bundle_json TEXT NOT NULL,
            manager_route_id TEXT NOT NULL,
            manager_tool TEXT NOT NULL,
            manager_model TEXT NOT NULL,
            state TEXT NOT NULL,
            pending_json TEXT NOT NULL DEFAULT '{}',
            pass_number INTEGER NOT NULL DEFAULT 0,
            question_seq INTEGER NOT NULL DEFAULT 0,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_execution_sessions(
            session_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            tool TEXT NOT NULL,
            model TEXT NOT NULL,
            provider_session_id TEXT,
            assigned_provider_id TEXT,
            prior_session_id TEXT,
            state TEXT NOT NULL CHECK(state IN ('active', 'lost')),
            note TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_execution_packets(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            packet_key TEXT NOT NULL,
            subject TEXT NOT NULL,
            record_json TEXT NOT NULL,
            record_sha256 TEXT NOT NULL,
            milestone_key TEXT NOT NULL,
            dependency_keys_json TEXT NOT NULL,
            state TEXT NOT NULL,
            route_id TEXT,
            tool TEXT,
            model TEXT,
            reason TEXT,
            branch TEXT,
            base_commit TEXT,
            head_commit TEXT,
            remote_head TEXT,
            plan_json TEXT,
            result_json TEXT,
            rounds_used INTEGER NOT NULL DEFAULT 0,
            round_limit INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            pending_json TEXT NOT NULL DEFAULT '{}',
            note TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, packet_key)
        )
        """,
        """
        CREATE TABLE service_execution_reviews(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            packet_key TEXT NOT NULL,
            review_round INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            reviewer_tool TEXT NOT NULL,
            reviewer_model TEXT NOT NULL,
            author_tool TEXT NOT NULL,
            author_model TEXT NOT NULL,
            reviewed_base TEXT NOT NULL,
            reviewed_head TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('APPROVE', 'REQUEST_CHANGES')),
            summary TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            independence TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, packet_key, review_round)
        )
        """,
        """
        CREATE TABLE service_execution_plans(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            pass_number INTEGER NOT NULL,
            assignment_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            result_json TEXT NOT NULL,
            accepted_json TEXT NOT NULL,
            rejected_json TEXT NOT NULL,
            event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, pass_number)
        )
        """,
        """
        CREATE TABLE service_execution_events(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            event_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            packet_key TEXT,
            detail TEXT NOT NULL,
            handled INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, event_id)
        )
        """,
        """
        CREATE TABLE service_execution_journal(
            operation_id TEXT PRIMARY KEY,
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            packet_key TEXT NOT NULL,
            kind TEXT NOT NULL,
            repository TEXT NOT NULL,
            branch TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            intended_head TEXT NOT NULL,
            remote_before TEXT,
            state TEXT NOT NULL CHECK(state IN ('prepared', 'verified', 'failed')),
            remote_after TEXT,
            detail TEXT,
            created_at TEXT NOT NULL
        )
        """,
    ),
)

_OPEN_STATES = ("running", "blocked", "paused")
_PACKET_ACTIVE = ("reserved", "coding", "reviewing", "correcting")
_MANAGER_TOOLS = ["Read"]
_CODER_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
_REVIEWER_TOOLS = ["Read", "Bash", "Glob", "Grep"]
_ROLE_CLASS = {"development_manager": "architect", "packet_coder": "architect", "packet_reviewer": "fidelity_reviewer", "integration_manager": "architect", "integration_reviewer": "fidelity_reviewer",
               "support_architect": "architect", "support_limit_architect": "architect", "determination_architect": "architect", "milestone_gap_architect": "architect", "support_reviewer": "fidelity_reviewer",
               "qa_agent": "fidelity_reviewer", "milestone_reviewer": "fidelity_reviewer"}

_COMMON_RULES = """Common rules: follow the exact packet and its permitted paths; change only what the packet needs; own the feature's required connections and real entry path; run real checks and report each honestly as passed, failed or untested (an unavailable check is untested, never passed); never expose credentials, never merge or deploy, never assume an Owner decision. A completion claim means ready for independent review, not accepted."""

_MANAGER_TASK = """You are the Maestro Development Manager for one project's Execution. You coordinate confirmed work packets; you do not change scope, redesign the architecture or replan. You choose which eligible packets start and with which coder route; the service checks every request against saved state and rejects stale, blocked, conflicting or unauthorized ones. Work only from this assignment and the files under input/. You cannot change anything; write no files.

1. Read input/execution.json (project, source commit, milestones), input/integration.json (the integration queue, milestone heads and dependency deliveries), input/packets.json (each packet: key, subject, purpose, milestone, dependencies, execution requirements, permitted paths, parallel opportunities, current state, review counts and any note), input/routes.json (the permitted coder routes: capabilities, location, context limit, concurrent capacity and current use), input/events.json (what changed since your last pass; handle each once) and input/decisions.json (Owner answers recorded so far).
2. {first_pass}Choose from the packets whose state is `pending` and whose dependencies are all delivered (see `startable` in packets.json). A dependency is delivered only when its providing packet is integrated into a milestone branch and, when that packet belongs to another milestone, imported into the consuming milestone by a dependency delivery (see waiting_for and integration.json); a packet that depends on undelivered work stays blocked and you say why. Approved packets and imports are integrated by the service's queue, not by you. Independent eligible packets may run in parallel within route capacity and shared-path limits. Reconsider on each event; do not interrupt or reassign running work.
3. Qwen (the default route {default_route}) is the primary coder. Choose a configured Codex or Claude route only when the packet's complexity, capabilities or context justify it, and give a brief reason either way. A launch names packet_key, route_id, the route's exact model from routes.json, and the reason. Request only what you can justify now.
4. Ask the Owner (result clarification_required, questions with recipient owner, and no launches) only when missing information affects intended outcomes or scope. Otherwise result completed.
5. Specialist guidance. A pending packet with `specialist_role` true already has its confirmed role and needs no support; request support for it only if you can name a concrete gap between that role and the packet. A pending packet with `specialist_role` false has no specialist guidance, and roles carry the source-local context a coder needs: do not launch it; list it in support_requests with the specific reason (packet_key and reason). The service then starts a bounded architectural-support assignment and notifies you when a validated role is bound; unrelated work continues. If a pending packet raises an architectural question the confirmed design does not answer, list it in architectural_questions (packet_key and the question); do not ask the Owner to interpret the architecture. Use empty lists when there is nothing to request.
6. Return: understanding (a concise statement of the intended outcomes, existing progress and blockers), launches, priorities (short ordered plain sentences), blockers (packet_key and reason for each packet you are not starting), support_requests, architectural_questions, and a checkpoint (your decisions, reasons and unresolved issues in a few plain sentences, for your own continuity).
{continuation}{rejections}
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_CODER_TASK = """You are a Maestro packet coder delivering exactly one work packet as a real, working change to a real repository. Work only from this assignment, the files under input/ and the working clone at output/work/. source/ is a read-only reference copy of the same commit; never modify source/ or input/.

1. Read input/packet.json (the exact packet: scope, permitted paths, completion criteria, essential failure checks, required outputs, shared-code constraints) and, when present, input/specialist-role.md and input/specialist-context.md (guidance for this source area).
2. output/work is a git clone at base commit {base} on branch {branch}. Change files only inside output/work and only under these permitted paths: {paths}. Anything else is rejected. Never create symbolic links. Run Python with PYTHONDONTWRITEBYTECODE=1 so no caches appear, and remove any cache directory you create.
3. BEFORE you change any file, write output/plan.json exactly as {{"schema":"execution_plan_v1","intended_changes":["<file and what changes>"],"existing_code":["<existing code you will reuse or amend>"],"connections":["<provider-to-consumer connection and real entry path>"],"verification":["<the real checks you will run>"],"blockers":[]}}. Every list except blockers has at least one entry. There is no approval step: write it and continue.
4. Implement the packet completely, including the connections and essential failure behavior it lists. Reuse the existing code; do not add adjacent work. Then run the packet's real checks from output/work (the real command, not a stand-in) and read their results. {common}
5. Leave your changes in output/work. You may commit; the service commits anything left over. Do not push and do not change branches.
6. Response: base_revision is {base}; changed_paths lists every file you changed (repository-relative); checks lists each real command you ran with outcome passed, failed or untested and a short detail; evidence lists plain statements of what you observed; limitations, blockers and unfinished list anything not done (empty when none). result is completed when the packet is finished and ready for independent review; use clarification_required with questions only if a missing prerequisite blocks it, and technical_failure only for a tool failure.
{correction}
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_CORRECTION = """
This is a targeted correction. An independent reviewer requested changes to your earlier revision (already on the branch; output/work starts from it). input/review-findings.json lists the blocking findings, each with its minimum correction. Fix exactly those blocking findings and what they affect; do not add other work. output/plan.json must describe this correction. If you disagree with a finding, say so in limitations rather than ignoring it."""

_REVIEW_TASK = """You are an independent packet reviewer. You did not write this change and you cannot change it. Decide whether the exact submitted revision satisfies the packet. Work only from this assignment, the files under input/ and source/, a read-only checkout of the exact reviewed commit {head}. Never modify source/ or input/; write no files under output/ except as the assignment's response instructions say.

1. Read input/packet.json (the exact packet), input/range.json (the exact base and head you must review), input/coder-result.json (the coder's report), input/plan.json, input/diff.patch (base..head), and, when present, input/specialist-role.md and input/specialist-context.md{later}.
2. Check: every completion criterion and essential failure check is met by the code in source/; the change stays inside the permitted paths ({paths}); required provider-to-consumer connections and the real entry path exist; the coder's evidence is real, not stale or circular. Independently run the packet's checks against source/ where you can (use PYTHONDONTWRITEBYTECODE=1, and work on a copy under scratch/ if a check needs to write). An unavailable check is not passing evidence.
3. This is not a search for improvements. A blocking finding names a concrete unmet requirement, the affected code, the impact and the minimum correction. Preferences and optional improvements are non_blocking. Give each finding a unique local_key and its locations.
4. Return review_outcome APPROVE only when there is no blocking finding; otherwise REQUEST_CHANGES with at least one blocking finding. Copy reviewed_range exactly from input/range.json. independence states in one sentence that you did not author the change. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_REVIEW_LATER = ", input/prior-findings.json (your earlier findings; recheck them and what the correction changed, and do not reopen unchanged work over preference)"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _paths_overlap(a: Iterable[str], b: Iterable[str]) -> bool:
    """True when any path in one set equals or lies inside a path in the other."""
    def inside(x: str, y: str) -> bool:
        x, y = x.strip("/"), y.strip("/")
        return x == y or x.startswith(y + "/")
    return any(inside(x, y) or inside(y, x) for x in a for y in b)


class ExecutionService(MilestoneMixin, GapMixin, DeterminationMixin, SupportMixin, IntegrationMixin):
    """Owns Execution state; the worker thread calls ``tick`` repeatedly."""

    def __init__(
        self,
        database: Database,
        *,
        records: ActivityRepository,
        questions: QuestionService,
        reservations: ProjectReservations,
        runs: AgentRunService | None,
        profiles: Mapping[str, RepositoryProfile],
        destination: Callable[[RepositoryProfile], GitHubDestination],
        state_dir: Path,
        owner_id: str,
        config_source: Callable[[], object],
        resources: InstalledSchemaResources | None = None,
    ) -> None:
        self.database = database
        self.records = records
        self.questions = questions
        self.reservations = reservations
        self.runs = runs
        self.profiles = profiles
        self._destination = destination
        self.state_dir = state_dir
        self.owner_id = owner_id
        self.config_source = config_source
        self.resources = resources
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()
        database.registry.register(EXECUTION_MIGRATION)
        database.registry.register(INTEGRATION_MIGRATION)
        database.registry.register(SUPPORT_MIGRATION)
        database.registry.register(GAP_MIGRATION)
        database.registry.register(MILESTONE_MIGRATION)
        database.initialize()

    @property
    def operation_handlers(self) -> tuple[OperationHandler, ...]:
        return (OperationHandler("execution.start", self.prepare_start), OperationHandler("execution.record_finding", self.prepare_record_finding))

    def owns(self, activity_id: str) -> bool:
        return self._read("SELECT 1 AS n FROM service_executions WHERE activity_id = ?", (activity_id,)) is not None

    def recipients(self) -> dict[str, Callable[[DeliveredAnswer], None]]:
        return {"owner": self.receive_answer}

    # ------------------------------------------------------------------ start

    def prepare_start(self, request: RequestLike) -> PreparedOperation:
        payload = dict(request.payload)
        if request.project_id is None or request.activity_id is not None or request.question_id is not None:
            raise ValueError("execution.start needs a project and no activity or question")
        if request.expected_version is not None:
            raise ValueError("execution.start expected_version must be null")
        if set(payload) != {"confirmed_ref", "manager_route_id"}:
            raise ValueError("execution.start payload must be confirmed_ref and manager_route_id")
        project_id = request.project_id
        project = self._read("SELECT * FROM service_projects WHERE project_id = ?", (project_id,))
        if project is None:
            raise RequestRejection(404, "project_not_found", "the project does not exist", fields={"project_id": project_id})
        entity_id = f"execution-request-{request.request_id}"
        existing = self._open_activity(project_id)
        if existing is not None:
            return self._duplicate(entity_id, project_id, existing)
        if self.runs is None:
            raise ValueError("no agent tools are configured for Execution")
        architecture = self._read(
            "SELECT * FROM service_architectures WHERE project_id = ? AND state = 'completed' AND confirmed_ref_json IS NOT NULL ORDER BY architecture_version DESC, created_at DESC LIMIT 1",
            (project_id,),
        )
        open_architecture = self._read("SELECT activity_id FROM service_architectures WHERE project_id = ? AND state NOT IN ('completed', 'cancelled')", (project_id,))
        if open_architecture is not None:
            raise RequestRejection(409, "architecture_unfinished", "an architecture activity is unfinished for this project; finish or cancel it before starting Execution", fields={"activity_id": open_architecture["activity_id"]})
        active = self._read(
            "SELECT a.package_json, r.* FROM service_registration_active a JOIN service_registrations r ON r.activity_id = a.activity_id WHERE a.project_id = ?", (project_id,),
        )
        if architecture is None or active is None or project["registration_status"] != "registered":
            raise RequestRejection(409, "breakdown_not_confirmed", "this project has no confirmed breakdown to execute; confirm one in the architecture loop first")
        if architecture["registration_activity_id"] != active["activity_id"] or architecture["source_commit"] != active["source_commit"]:
            raise RequestRejection(409, "breakdown_not_current", "the confirmed breakdown does not belong to the current registration and its pinned source; re-run the architecture loop", fields={"registration": active["activity_id"]})
        confirmed = json.loads(architecture["confirmed_ref_json"])
        supplied = payload["confirmed_ref"]
        identity = ("version", "commit", "manifest_path", "manifest_sha256", "reviewed_content_hash")
        if not isinstance(supplied, dict) or any(supplied.get(k) != confirmed.get(k) for k in identity):
            raise RequestRejection(409, "confirmed_ref_stale", "the confirmed breakdown reference is not the project's newest confirmed version", fields={"current": confirmed})
        try:
            config = execution_config.validate(self.config_source())
        except execution_config.ExecutionConfigError as error:
            raise ValueError(f"Execution is not configured: {error}") from error
        route_id = payload["manager_route_id"]
        manager = config["development_manager"]["routes"].get(route_id) if isinstance(route_id, str) else None
        if manager is None:
            raise ValueError("manager_route_id does not name a configured Development Manager route; configured: " + ", ".join(config["development_manager"]["routes"]))
        try:
            self.runs.route_resolver("architect", manager["tool"], manager["model"])
        except Exception as error:  # noqa: BLE001 - any refusal to resolve the route means it cannot be launched
            raise ValueError(f"the Development Manager route {route_id} cannot be used: {error}") from error
        if self.resources is None:
            raise ValueError("the execution@3 schema bundle is unavailable")
        try:
            bundle = self.resources.resolve("execution@3").snapshot.as_dict()
        except ProcessResourceError as error:
            raise ValueError(f"the installed execution@3 bundle cannot be used: {error}") from error
        profile = self.profiles[json.loads(active["profile_json"])["profile"]]
        try:
            destination = self._destination(profile)
            packets = self._read_packets(destination, confirmed, architecture["repository"])
            milestones = self._read_milestones(destination, confirmed, architecture["repository"])
            mirror = self._mirror(project_id)
            destination.fetch_source(architecture["repository"], architecture["source_commit"], mirror)
            master_branch = destination.default_branch(architecture["repository"])
            master_commit = destination.head(architecture["repository"], master_branch)
        except (DestinationError, ValueError) as error:
            raise ValueError(f"the confirmed breakdown or its source cannot be read: {getattr(error, 'code', '')} {error}".replace("  ", " ")) from error
        if not any(not p["dependency_keys"] for p in packets):
            raise RequestRejection(409, "no_eligible_packet", "no packet is eligible to start: every packet depends on another")
        activity_id = f"execution-{uuid.uuid4().hex[:12]}"
        details = {"architecture": architecture, "active": active, "confirmed": confirmed, "config": config, "route_id": route_id, "manager": manager, "bundle": bundle,
                   "packets": packets, "milestones": milestones, "master": (master_branch, master_commit), "project": project}

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            found = self._open_activity(project_id, transaction)
            if found is not None:
                return OperationResult(data={"activity_id": found, "duplicate": True, "message": "an Execution activity is already unfinished for this project"}, project_id=project_id, activity_id=found)
            try:
                self.reservations.reserve(transaction, project_id, "start", activity_id, check_unresolved=True)
            except ReservationError as error:
                raise RequestRejection(409, error.code, str(error), fields=error.fields) from error
            now = _now()
            self.records.create_activity(transaction, ActivityRecord(
                activity_id, project_id, "execution", f"Execution for {details['project']['name']}", "running", 1,
                "Starting the Development Manager", now, None, (),
            ))
            transaction.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, 1) ON CONFLICT(entity_id) DO UPDATE SET version = 1", (activity_id,))
            registration = details["active"]
            transaction.execute(
                """
                INSERT INTO service_executions(activity_id, project_id, registration_activity_id, architecture_activity_id, registration_json, confirmed_ref_json,
                    repository, profile_json, source_commit, master_branch, master_commit, observed_at, config_json, config_sha256, bundle_json,
                    manager_route_id, manager_tool, manager_model, state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', ?)
                """,
                (activity_id, project_id, registration["activity_id"], details["architecture"]["activity_id"], canonical_json(json.loads(registration["package_json"])),
                 canonical_json(details["confirmed"]), details["architecture"]["repository"], registration["profile_json"], details["architecture"]["source_commit"],
                 *details["master"], now, canonical_json(details["config"]), execution_config.digest(details["config"]), canonical_json(details["bundle"]),
                 details["route_id"], details["manager"]["tool"], details["manager"]["model"], now),
            )
            tool = details["manager"]["tool"]
            transaction.execute(
                "INSERT INTO service_execution_sessions(session_id, activity_id, tool, model, assigned_provider_id, state, created_at) VALUES (?, ?, ?, ?, ?, 'active', ?)",
                (f"{activity_id}-session-1", activity_id, tool, details["manager"]["model"], str(uuid.uuid4()) if tool == "claude_code" else None, now),
            )
            limit = details["config"]["reviews"]["packet"]["maximum_completed_rounds"]
            for packet in details["packets"]:
                transaction.execute(
                    "INSERT INTO service_execution_packets(activity_id, packet_key, subject, record_json, record_sha256, milestone_key, dependency_keys_json, state, round_limit, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
                    (activity_id, packet["key"], packet["record"]["subject"], canonical_json(packet["record"]), packet["sha256"], packet["milestone_key"], _dump(packet["dependency_keys"]), limit, now),
                )
            for m in details["milestones"]:
                transaction.execute(
                    "INSERT INTO service_execution_milestones(activity_id, milestone_key, subject, record_json, record_sha256, dependencies_json, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (activity_id, m["key"], str(m["record"].get("subject", m["key"])), canonical_json(m["record"]), m["sha256"], _dump(m["dependencies"]), now),
                )
            self._event(transaction, activity_id, "started", None, "Execution started; the Development Manager plans the first packets")
            self._say(transaction, project_id, activity_id,
                      f"Execution started from confirmed breakdown version {details['confirmed']['version']} (registration candidate {json.loads(registration['package_json'])['candidate_id']}): "
                      f"code baseline {details['architecture']['source_commit'][:12]}, product {details['master'][0]} observed at {details['master'][1][:12]}, "
                      f"{len(details['packets'])} packets, Development Manager {tool} {details['manager']['model']} (route {details['route_id']}), configuration {execution_config.digest(details['config'])[:12]}.")
            return OperationResult(
                data={"activity_id": activity_id, "project_id": project_id, "duplicate": False, "source_commit": details["architecture"]["source_commit"],
                      "product_master_start_commit": details["master"][1], "packets": len(details["packets"])},
                status="accepted", project_id=project_id, activity_id=activity_id,
            )

        return PreparedOperation(entity_id, "execution.started", {"project_id": project_id}, apply)

    def _duplicate(self, entity_id: str, project_id: str, activity_id: str) -> PreparedOperation:
        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            return OperationResult(data={"activity_id": activity_id, "duplicate": True, "message": "an Execution activity is already unfinished for this project"}, project_id=project_id, activity_id=activity_id)
        return PreparedOperation(entity_id, "execution.duplicate", {"activity_id": activity_id}, apply)

    def _open_activity(self, project_id: str, tx: Transaction | None = None) -> str | None:
        sql = f"SELECT activity_id FROM service_executions WHERE project_id = ? AND state IN ({','.join('?' for _ in _OPEN_STATES)}) ORDER BY created_at LIMIT 1"
        params = (project_id, *_OPEN_STATES)
        found = self._row(tx, sql, params) if tx is not None else self._read(sql, params)
        return None if found is None else str(found["activity_id"])

    @staticmethod
    def _read_packets(destination: GitHubDestination, confirmed: Mapping[str, Any], repository: str) -> list[dict[str, Any]]:
        import hashlib

        packets: list[dict[str, Any]] = []
        for entry in confirmed["listing"]:
            if entry["kind"] != "work_packet":
                continue
            data = destination.read_file(repository, entry["commit"], entry["path"])
            if data is None or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"the published packet {entry['id']} does not match the confirmed hash")
            record = json.loads(data)
            packets.append({
                "key": entry["id"], "record": record, "sha256": entry["sha256"], "commit": entry["commit"], "path": entry["path"],
                "milestone_key": str(record["development_milestone_ref"]["id"]), "dependency_keys": [str(d["id"]) for d in record.get("dependencies", [])],
            })
        if not packets:
            raise ValueError("the confirmed breakdown lists no work packets")
        return packets

    def _mirror(self, project_id: str) -> Path:
        return self.state_dir / "sources" / f"{project_id}.git"

    # ---------------------------------------------------------------- answers

    def receive_answer(self, answer: DeliveredAnswer) -> None:
        with self.database.transaction() as tx:
            row = self._row(tx, "SELECT * FROM service_executions WHERE activity_id = ?", (answer.activity_id,))
            if row is None:
                return
            pending = json.loads(row["pending_json"] or "{}")
            info = pending.get("questions", {}).get(answer.question_id)
            if info is None or info.get("answered"):
                return
            info["answered"] = answer.answer_id
            question = self._row(tx, "SELECT subject, prompt FROM service_questions WHERE question_id = ?", (answer.question_id,))
            pending.setdefault("answers", []).append({"question_id": answer.question_id, "subject": str(question["subject"]), "question": str(question["prompt"]), "answer": answer.text, "choice_id": answer.choice_id})
            tx.execute("UPDATE service_executions SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), answer.activity_id))
            self._event(tx, answer.activity_id, "answer", None, f"The Owner answered: {answer.text[:300]}")
            self._resolve_question(tx, answer.question_id)

    # ----------------------------------------------------------------- worker

    def tick(self) -> None:
        try:
            self.questions.deliver_pending()
        except RecipientDeliveryInterrupted:
            log.warning("an answer delivery was interrupted and will be retried", exc_info=True)
        with self.database.read_connection() as connection:
            ids = [str(r[0]) for r in connection.execute(f"SELECT activity_id FROM service_executions WHERE state IN ('running', 'blocked') ORDER BY created_at")]
        for activity_id in ids:
            lock = self._lock(activity_id)
            if not lock.acquire(blocking=False):
                continue
            try:
                self.advance(activity_id)
            except Exception as error:  # noqa: BLE001 - one activity's failure must not stop the others
                log.exception("execution step failed for %s", activity_id)
                self._pause_on_error(activity_id, error)
            finally:
                lock.release()

    def _lock(self, activity_id: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(activity_id, threading.Lock())

    def advance(self, activity_id: str) -> None:
        row = self._read("SELECT * FROM service_executions WHERE activity_id = ?", (activity_id,))
        if row is None or row["state"] not in {"running", "blocked"}:
            return
        self._advance_manager(row)
        self._advance_support(row)
        self._advance_determinations(row)
        self._advance_gaps(row)
        self._verify_deliveries(row)
        self._plan_deliveries(row)
        self._enqueue_approved(row)
        self._advance_integration(row)
        self._advance_verification(row)
        for packet in self._packets(activity_id):
            row = self._read("SELECT * FROM service_executions WHERE activity_id = ?", (activity_id,))
            if row is None or row["state"] not in {"running", "blocked"}:
                return
            try:
                self._advance_packet(row, packet)
            except Exception as error:  # noqa: BLE001 - a packet's failure pauses that packet, not the activity
                log.exception("packet %s step failed", packet["packet_key"])
                self._fail_packet(row, packet, f"{getattr(error, 'code', type(error).__name__)}: {error}")
        self._settle(activity_id)

    def _pause_on_error(self, activity_id: str, error: Exception) -> None:
        transient = isinstance(error, DestinationError) and (
            error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500)
        )
        if transient:
            return
        reason = f"{getattr(error, 'code', type(error).__name__)}: {error}"
        with self.database.transaction() as tx:
            row = self._row(tx, "SELECT state FROM service_executions WHERE activity_id = ?", (activity_id,))
            if row is None or row["state"] not in {"running", "blocked"}:
                return
            tx.execute("UPDATE service_executions SET state = 'paused', note = ? WHERE activity_id = ?", (reason[:500], activity_id))
            self._activity(tx, activity_id, "paused", f"Paused: {reason[:300]}")
            self._say(tx, str(self._row(tx, "SELECT project_id FROM service_executions WHERE activity_id = ?", (activity_id,))["project_id"]), activity_id, f"Execution paused: {reason[:400]}")

    # ---------------------------------------------------------------- manager

    def _packets(self, activity_id: str) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM service_execution_packets WHERE activity_id = ? ORDER BY packet_key", (activity_id,))

    def _advance_manager(self, row: Mapping[str, Any]) -> None:
        assert self.runs is not None
        activity_id = row["activity_id"]
        pending = json.loads(row["pending_json"] or "{}")
        current = pending.get("manager_run")
        if current is None:
            if self._needs_planning(row, pending):
                self._start_manager(row, pending)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        self._remember_conversation(activity_id, current["run_id"])
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            if assignment["state"] == "waiting_for_answers":
                self._manager_questions(row, current)
            else:
                self._accept_plan(row, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = self.runs.view(current["run_id"]).terminal_reason or view.failure_code or "technical_failure"
            if pending.get("last_recovery_detail") == detail:
                raise AgentRunError("repeated_output_error", f"the same output error came back after a correction: {detail}")
            pending["last_recovery_detail"] = detail
            self._start_manager(row, {**pending, "manager_run": None}, recovery_note=detail)
            return
        if view.state == "cancelled":
            return
        raise AgentRunError("manager_run_failed", f"Development Manager run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else ""))

    def _needs_planning(self, row: Mapping[str, Any], pending: Mapping[str, Any]) -> bool:
        if any(not q.get("answered") for q in pending.get("questions", {}).values()):
            return False
        packets = self._packets(row["activity_id"])
        if not any(p["state"] in {"pending"} for p in packets):
            return False
        return self._read("SELECT 1 AS n FROM service_execution_events WHERE activity_id = ? AND handled = 0", (row["activity_id"],)) is not None

    def _session(self, activity_id: str, role: str = "development_manager") -> dict[str, Any]:
        session = self._read("SELECT * FROM service_execution_sessions WHERE activity_id = ? AND role = ? AND state = 'active' ORDER BY created_at DESC, rowid DESC LIMIT 1", (activity_id, role))
        assert session is not None
        return session

    def _remember_conversation(self, activity_id: str, run_id: str, role: str = "development_manager") -> None:
        assert self.runs is not None
        session = self._session(activity_id, role)
        provider = self.runs.run_evidence(run_id).get("session_id")
        if not provider and session["assigned_provider_id"]:
            history = self.state_dir / "sessions" / session["session_id"] / "history"
            if history.is_dir() and any(history.rglob(f"{session['assigned_provider_id']}.jsonl")):
                provider = session["assigned_provider_id"]
        if not provider:
            return
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_sessions SET provider_session_id = ? WHERE session_id = ? AND provider_session_id IS NULL", (provider, session["session_id"]))

    def _session_use(self, row: Mapping[str, Any], role: str = "development_manager") -> tuple[SessionUse, str | None]:
        session = self._session(row["activity_id"], role)
        label = "Development Manager" if role == "development_manager" else "Integration Manager"
        prefix = "session" if role == "development_manager" else "isession"
        state_dir = self.state_dir / "sessions" / session["session_id"]
        note = None
        if session["provider_session_id"] is not None and not (state_dir / "history").is_dir():
            number = int(session["session_id"].rsplit("-", 1)[1]) + 1
            new_id = f"{row['activity_id']}-{prefix}-{number}"
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_execution_sessions SET state = 'lost', note = ? WHERE session_id = ?", ("the saved conversation is unavailable", session["session_id"]))
                tx.execute(
                    "INSERT INTO service_execution_sessions(session_id, activity_id, tool, model, assigned_provider_id, prior_session_id, state, created_at, role) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                    (new_id, row["activity_id"], session["tool"], session["model"], str(uuid.uuid4()) if session["tool"] == "claude_code" else None, session["session_id"], _now(), role),
                )
                self._say(tx, row["project_id"], row["activity_id"], f"The {label}'s conversation was unavailable; replacement session {new_id} continues from the saved records and its last checkpoint.")
            session = self._session(row["activity_id"], role)
            state_dir = self.state_dir / "sessions" / session["session_id"]
            note = "Your earlier conversation was unavailable, so this is a replacement session. The saved records in input/ and the checkpoint below are authoritative; nothing of your earlier work is assumed."
        provider = session["provider_session_id"]
        return SessionUse(session["session_id"], state_dir, provider, session["assigned_provider_id"] if provider is None else None), note

    def _start_manager(self, row: Mapping[str, Any], pending: dict[str, Any], recovery_note: str | None = None) -> None:
        assert self.runs is not None
        activity_id, project_id = row["activity_id"], row["project_id"]
        config = json.loads(row["config_json"])
        pass_number = int(row["pass_number"]) + (1 if recovery_note is None else 0)
        assignment_id = f"{activity_id}-mgr-{pass_number}"
        session, replacement_note = self._session_use(row)
        events = self._rows("SELECT * FROM service_execution_events WHERE activity_id = ? AND handled = 0 ORDER BY event_id", (activity_id,))
        pending["planning_event_ids"] = [e["event_id"] for e in events] if recovery_note is None else pending.get("planning_event_ids", [e["event_id"] for e in events])
        inputs = self._manager_inputs(row, pending, events)
        first = pass_number == 1 and session.provider_session_id is None
        continuation = replacement_note or ("" if first else "\nThis session continues: your conversation history is restored. Your last checkpoint is in input/checkpoint.md. Use the events in input/events.json; do not redo settled work.")
        rejections = "" if not pending.get("rejections") else f"\nThe service rejected these earlier requests for the reasons in input/rejections.json; reconsider them against the current state."
        if recovery_note:
            rejections += f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _MANAGER_TASK.format(first_pass="This is your first pass: begin by stating your understanding. " if first else "", default_route=config["coder_default_route_id"], continuation=continuation, rejections=rejections)
        decision_version = f"d{len(pending.get('answers', []))}"
        tool, model = row["manager_tool"], row["manager_model"]
        mirror = self._mirror(project_id)

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=project_id, activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="development_manager",
                role_responsibilities=("Choose which eligible work packets start and with which coder route; never change scope or the architecture.",),
                task=task, source_commit=row["source_commit"], decision_version=decision_version,
                instructions={"session_id": session.session_id, "claude_tools": _MANAGER_TOOLS, "task_kind": "plan_execution"},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": config["development_manager"]["run_timeout_seconds"]},
                clarification_conditions=("Information affecting intended outcomes or scope is missing.",), response_schema=MANAGER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, session)

        self._launch(row, pending, "manager_run", assignment_id, tool, model, config["development_manager"]["run_timeout_seconds"], recovery_note is not None, build, "development_manager")
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET pass_number = ?, pending_json = ? WHERE activity_id = ?", (pass_number, canonical_json(pending), activity_id))
            self._activity(tx, activity_id, "running", f"Development Manager ({tool} {model}) is planning (pass {pass_number})")
            self._say(tx, project_id, activity_id, f"Development Manager planning pass {pass_number} started: {tool} {model}, assignment {assignment_id}, session {session.session_id}, handling {len(events)} saved event(s).")

    def _launch(self, row: Mapping[str, Any], pending: dict[str, Any], slot: str, assignment_id: str, tool: str, model: str, duration: int, recovery: bool,
                build: Callable[[str], RunBuild], role: str, intervention: str = "", save: Callable[[str, dict[str, Any]], None] | None = None) -> str:
        """Create the assignment when needed and start the next run; the run is saved in ``pending[slot]`` so a restart finds it."""
        assert self.runs is not None
        config = json.loads(row["config_json"])
        if not self._assignment_exists(assignment_id):
            self.runs.create_assignment(assignment_id, row["project_id"], row["activity_id"], _ROLE_CLASS[role], tool, model,
                                        duration_seconds=duration, automatic_limit=int(config["recovery"]["automatic_recovery_attempts"]))
        before = self.runs.run_count(assignment_id)
        run_id = f"{assignment_id}-run{before + 1}"
        kind = "recovery" if recovery else "initial"
        try:
            self.runs.start_run(assignment_id, run_id, kind, build, intervention=intervention)
        except Exception:
            if self.runs.run_count(assignment_id) > before:
                pending[slot] = {"assignment_id": assignment_id, "run_id": run_id}
                (save or self._save_pending)(row["activity_id"], pending)
            raise
        pending[slot] = {"assignment_id": assignment_id, "run_id": run_id}
        return run_id

    def _assignment_exists(self, assignment_id: str) -> bool:
        assert self.runs is not None
        try:
            self.runs.assignment_state(assignment_id)
            return True
        except AgentRunError:
            return False

    def _save_pending(self, activity_id: str, pending: Mapping[str, Any]) -> None:
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_executions SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), activity_id))

    def _manager_inputs(self, row: Mapping[str, Any], pending: Mapping[str, Any], events: list[dict[str, Any]]) -> dict[str, bytes]:
        config = json.loads(row["config_json"])
        packets = self._packets(row["activity_id"])
        by_key = {p["packet_key"]: p for p in packets}
        deliveries = self._deliveries(row["activity_id"])
        held = self._held_packets(row["activity_id"])
        supports = self._architects(row["activity_id"], "support")
        listing = []
        for p in packets:
            record = json.loads(p["record_json"])
            dependencies = json.loads(p["dependency_keys_json"])
            waiting = [d for d in dependencies if not is_delivered(by_key, deliveries, p, d)]
            listing.append({
                "key": p["packet_key"], "subject": p["subject"], "purpose": record.get("purpose"), "milestone": p["milestone_key"], "dependencies": dependencies,
                "parallel_opportunities": [str(x.get("id", x)) if isinstance(x, Mapping) else str(x) for x in record.get("parallel_opportunities", [])],
                "execution_requirements": record.get("execution_requirements"), "permitted_paths": record.get("permitted_paths"),
                "state": p["state"], "startable": p["state"] == "pending" and not waiting and p["packet_key"] not in held,
                "specialist_role": bool((record.get("starting_context") or {}).get("specialist_role_ref")) or self._support_binding(row["activity_id"], p["packet_key"]) is not None,
                "support": [{"support_id": a["assignment_key"], "state": a["state"], "note": a["note"]} for a in supports if a["packet_key"] == p["packet_key"]],
                "waiting_for": waiting, "route": p["route_id"], "review_rounds": {"completed": p["rounds_used"], "limit": p["round_limit"]}, "note": p["note"],
            })
        use = {r: sum(1 for p in packets if p["route_id"] == r and p["state"] in _PACKET_ACTIVE) for r in config["coder_routes"]}
        routes = [{"route_id": rid, "default": rid == config["coder_default_route_id"], **{k: v for k, v in r.items() if k in {"tool", "model", "location", "capabilities", "context_limit_tokens", "maximum_concurrent_runs"}}, "in_use": use[rid]}
                  for rid, r in config["coder_routes"].items()]
        files: dict[str, bytes] = {
            "execution.json": _json({"project_id": row["project_id"], "activity_id": row["activity_id"], "source_commit": row["source_commit"], "repository": row["repository"],
                                     "product_master_start_commit": row["master_commit"], "confirmed_breakdown": {k: json.loads(row["confirmed_ref_json"])[k] for k in ("version", "commit", "manifest_path")},
                                     "milestones": sorted({p["milestone_key"] for p in packets})}),
            "packets.json": _json({"packets": listing}), "routes.json": _json({"routes": routes}),
            "events.json": _json({"events": [{"event_id": e["event_id"], "kind": e["kind"], "packet_key": e["packet_key"], "detail": e["detail"]} for e in events]}),
            "decisions.json": _json({"answers": pending.get("answers", [])}),
            "checkpoint.md": (pending.get("checkpoint") or "No earlier checkpoint.").encode("utf-8"),
            "integration.json": _json(self._manager_integration(row["activity_id"])),
        }
        if pending.get("rejections"):
            files["rejections.json"] = _json({"rejections": pending["rejections"]})
        return files

    def _manager_integration(self, activity_id: str) -> dict[str, Any]:
        view = self.integration_view(activity_id)
        return {"milestones": [{k: m[k] for k in ("key", "dependencies", "head_commit")} for m in view["milestones"]],
                "queue": [{k: e[k] for k in ("entry_id", "kind", "packet_key", "delivery_id", "milestone", "state", "note")} for e in view["queue"] if e["state"] not in ("merged", "invalidated", "withdrawn")],
                "deliveries": [{k: d[k] for k in ("delivery_id", "provider", "consumer", "state", "packets", "note")} for d in view["deliveries"]]}

    def _manager_questions(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        requests = _questions(_question_view(response.get("questions", [])))
        assignment = AgentAssignment(
            project_id=row["project_id"], activity_id=row["activity_id"], assignment_id=current["assignment_id"], run_id=current["run_id"], parent_assignment_id=None,
            role="development_manager", role_responsibilities=("x",), task="x", source_commit=row["source_commit"], decision_version="d0",
            instructions={}, permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={}, clarification_conditions=("x",), response_schema={},
        )
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_executions WHERE activity_id = ?", (row["activity_id"],))
            pending = json.loads(fresh["pending_json"] or "{}")
            pending.pop("manager_run", None)
            seq = int(fresh["question_seq"])
            for request in requests:
                seq += 1
                question_id = f"{row['activity_id']}-q{seq}"
                self.questions.publish(tx, request.to_linked_question(question_id=question_id, assignment=assignment, requester="development_manager"))
                pending.setdefault("questions", {})[question_id] = {"kind": "manager_question"}
            tx.execute("UPDATE service_executions SET question_seq = ?, pending_json = ? WHERE activity_id = ?", (seq, canonical_json(pending), row["activity_id"]))
            self._activity(tx, row["activity_id"], "waiting", f"Waiting for your answer: the Development Manager asked {len(requests)} question(s); packets already running continue")
            self._say(tx, row["project_id"], row["activity_id"], f"The Development Manager needs {len(requests)} answer(s) before it plans further; its session is kept and unrelated running work continues.")

    def _accept_plan(self, row: Mapping[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        config = json.loads(row["config_json"])
        accepted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        with self.database.transaction() as tx:
            fresh = self._row(tx, "SELECT * FROM service_executions WHERE activity_id = ?", (row["activity_id"],))
            pending = json.loads(fresh["pending_json"] or "{}")
            packets = {p["packet_key"]: p for p in (self._row_list(tx, "SELECT * FROM service_execution_packets WHERE activity_id = ?", (row["activity_id"],)))}
            deliveries = self._row_list(tx, "SELECT * FROM service_execution_deliveries WHERE activity_id = ?", (row["activity_id"],))
            held = self._held_packets(row["activity_id"], tx)
            bound = {b["packet_key"] for b in self._row_list(tx, "SELECT packet_key FROM service_execution_support_bindings WHERE activity_id = ? AND state = 'active'", (row["activity_id"],))}
            for launch in response.get("launches", []):
                reason = held.get(launch["packet_key"]) or self._launch_problem(config, packets, launch, accepted, deliveries, bound)
                if reason is not None:
                    rejected.append({"packet_key": launch["packet_key"], "route_id": launch["route_id"], "reason": reason})
                    continue
                route = config["coder_routes"][launch["route_id"]]
                branch = f"maestro/{row['activity_id']}/packet/{launch['packet_key']}"
                tx.execute(
                    "UPDATE service_execution_packets SET state = 'reserved', route_id = ?, tool = ?, model = ?, reason = ?, branch = ?, base_commit = ?, note = NULL, updated_at = ? "
                    "WHERE activity_id = ? AND packet_key = ? AND state = 'pending'",
                    (launch["route_id"], route["tool"], route["model"], str(launch["reason"])[:500], branch, row["source_commit"], _now(), row["activity_id"], launch["packet_key"]),
                )
                packets[launch["packet_key"]] = {**packets[launch["packet_key"]], "state": "reserved", "route_id": launch["route_id"]}
                accepted.append(launch)
            for request in response.get("support_requests", []):
                packet = packets.get(request.get("packet_key"))
                problem = "no such packet in this Execution" if packet is None else self._request_support(tx, row, packet, str(request.get("reason", ""))) 
                if problem is not None:
                    rejected.append({"packet_key": request.get("packet_key"), "route_id": "support", "reason": problem})
            for request in response.get("architectural_questions", []):
                problem = self._request_manager_question(tx, row, packets.get(request.get("packet_key")), str(request.get("question", "")))
                if problem is not None:
                    rejected.append({"packet_key": request.get("packet_key"), "route_id": "architectural_question", "reason": problem})
            event_ids = pending.pop("planning_event_ids", [])
            for event_id in event_ids:
                tx.execute("UPDATE service_execution_events SET handled = 1 WHERE activity_id = ? AND event_id = ?", (row["activity_id"], event_id))
            number = int(fresh["pass_number"])
            tx.execute(
                "INSERT INTO service_execution_plans(activity_id, pass_number, assignment_id, run_id, result_json, accepted_json, rejected_json, event_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["activity_id"], number, current["assignment_id"], current["run_id"], canonical_json(response), _dump(accepted), _dump(rejected), _dump(event_ids), _now()),
            )
            pending.pop("manager_run", None)
            pending["checkpoint"] = str(response.get("checkpoint", ""))[:4000]
            pending["understanding"] = str(response.get("understanding", ""))[:2000]
            pending["priorities"] = [str(p)[:300] for p in response.get("priorities", [])][:10]
            pending["blockers"] = [{"packet_key": str(b["packet_key"]), "reason": str(b["reason"])[:300]} for b in response.get("blockers", [])][:20]
            pending["rejections"] = rejected
            pending.pop("last_recovery_detail", None)
            if rejected:
                pending["rejected_streak"] = int(pending.get("rejected_streak", 0)) + 1
                if not accepted:
                    self._event(tx, row["activity_id"], "rejected", None, "; ".join(f"{r['packet_key']}: {r['reason']}" for r in rejected)[:500])
            else:
                pending.pop("rejected_streak", None)
            tx.execute("UPDATE service_executions SET pending_json = ? WHERE activity_id = ?", (canonical_json(pending), row["activity_id"]))
            self._say(tx, row["project_id"], row["activity_id"],
                      f"Planning pass {number} recorded: {len(accepted)} launch(es) reserved"
                      + "".join(f" [{a['packet_key']} on {a['route_id']}: {str(a['reason'])[:160]}]" for a in accepted)
                      + (f"; {len(rejected)} rejected" + "".join(f" [{r['packet_key']}: {r['reason']}]" for r in rejected) if rejected else "") + ".")
            self._activity(tx, row["activity_id"], "running", f"Planning pass {number} recorded; {len(accepted)} packet(s) reserved")
        if int(pending.get("rejected_streak", 0)) >= 3 and not accepted:
            raise AgentRunError("planning_rejected", "the Development Manager's requests were rejected three passes in a row; see the rejection reasons")

    @staticmethod
    def _launch_problem(config: Mapping[str, Any], packets: Mapping[str, Mapping[str, Any]], launch: Mapping[str, Any], accepted: list[dict[str, Any]], deliveries: list[Mapping[str, Any]] = (), bound: Collection[str] = ()) -> str | None:
        packet = packets.get(launch["packet_key"])
        if packet is None:
            return "no such packet in this Execution"
        if packet["state"] != "pending":
            return f"the packet is {packet['state']}, not pending"
        record = json.loads(packet["record_json"])
        deps = json.loads(packet["dependency_keys_json"])
        undelivered = [d for d in deps if not is_delivered(packets, list(deliveries), packet, d)]
        if undelivered:
            return "its dependencies are not delivered yet: " + ", ".join(undelivered)
        if not (record.get("starting_context") or {}).get("specialist_role_ref") and launch["packet_key"] not in bound:
            return "the packet has no confirmed specialist role and no active support binding; it needs architectural support first"
        route = config["coder_routes"].get(launch["route_id"])
        if route is None:
            return "the route is not a configured coder route"
        if launch["model"] != route["model"]:
            return f"the model must be the route's exact model {route['model']}"
        requirements = record.get("execution_requirements") or {}
        missing = sorted(set(requirements.get("required_capabilities", [])) - set(route["capabilities"]))
        if missing:
            return "the route lacks capabilities: " + ", ".join(missing)
        if route["location"] not in requirements.get("allowed_locations", [route["location"]]):
            return f"the route location {route['location']} is not allowed for this packet"
        if route["context_limit_tokens"] < int(requirements.get("minimum_context_tokens", 0)):
            return "the route's context limit is below the packet's minimum"
        in_use = sum(1 for p in packets.values() if p.get("route_id") == launch["route_id"] and p["state"] in _PACKET_ACTIVE) + sum(1 for a in accepted if a["route_id"] == launch["route_id"])
        if in_use >= route["maximum_concurrent_runs"]:
            return f"the route is at its capacity of {route['maximum_concurrent_runs']} concurrent run(s)"
        parallel = {str(x.get("id", x)) if isinstance(x, Mapping) else str(x) for x in record.get("parallel_opportunities", [])}
        mine = set(record.get("permitted_paths", []))
        for other_key, other in packets.items():
            active = other["state"] in _PACKET_ACTIVE or any(a["packet_key"] == other_key for a in accepted)
            if not active or other_key == launch["packet_key"]:
                continue
            theirs = json.loads(other["record_json"]).get("permitted_paths", [])
            if _paths_overlap(mine, theirs) and other_key not in parallel:
                return f"it shares permitted paths with the running packet {other_key}, which is not a declared parallel opportunity"
        return None

    # ---------------------------------------------------------------- packets

    def _advance_packet(self, row: Mapping[str, Any], packet: Mapping[str, Any]) -> None:
        state = packet["state"]
        if self._packet_pending(packet).get("quarantined"):
            return  # its dependency evidence changed: the running result may only preserve work until reconciled
        if state == "reserved":
            self._start_coder(row, packet)
        elif state in {"coding", "correcting"}:
            self._advance_coder(row, packet)
        elif state == "publishing":
            self._advance_publish(row, packet)
        elif state == "review_ready":
            self._start_reviewer(row, packet)
        elif state == "reviewing":
            self._advance_reviewer(row, packet)

    def _packet_pending(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        return json.loads(packet["pending_json"] or "{}")

    def _save_packet(self, activity_id: str, key: str, pending: Mapping[str, Any], **columns: object) -> None:
        sets = ", ".join(f"{name} = ?" for name in columns)
        with self.database.transaction() as tx:
            tx.execute(f"UPDATE service_execution_packets SET pending_json = ?, updated_at = ?{', ' + sets if sets else ''} WHERE activity_id = ? AND packet_key = ?",
                       (canonical_json(pending), _now(), *columns.values(), activity_id, key))

    def _recommendation_fields(self, activity_id: str, assignment_id: str) -> dict[str, Any]:
        arch = self._read("SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ?", (activity_id, f"det-{assignment_id}"))
        result = json.loads(arch["result_json"]) if arch is not None and arch["result_json"] else None
        if result is None:
            return {"recommendation": None, "rationale": None, "determination": None if arch is None else arch["state"]}
        return {"recommendation": result["owner_recommendation"], "rationale": result["rationale"], "determination": result["determination"]}

    def _held_packets(self, activity_id: str, tx: Transaction | None = None) -> dict[str, str]:
        """Pending packets that must not launch, with the plain reason: an unresolved support assignment for the packet."""
        held = dict(self._held_by_support(activity_id))
        held.update(self._held_by_determination(activity_id))
        row = self._read("SELECT * FROM service_executions WHERE activity_id = ?", (activity_id,))
        if row is not None:
            held.update(self._held_by_disposition(row))
        return held

    def _packet_paths(self, packet: Mapping[str, Any]) -> list[str]:
        return list(json.loads(packet["record_json"]).get("permitted_paths", []))

    def _role_inputs(self, row: Mapping[str, Any], packet: Mapping[str, Any]) -> dict[str, bytes]:
        record = json.loads(packet["record_json"])
        inputs = {"packet.json": _json(record)}
        ref = (record.get("starting_context") or {}).get("specialist_role_ref")
        binding = self._support_binding(row["activity_id"], packet["packet_key"])
        if binding is not None:
            destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
            role = destination.read_file(row["repository"], binding["commit_sha"], binding["role_path"])
            if role is None or hashlib.sha256(role).hexdigest() != binding["role_sha256"]:
                raise AgentRunError("support_changed", f"the activated specialist role {binding['role_path']} no longer matches its verified hash")
            inputs["specialist-role.md"] = role
            if binding["context_path"]:
                context = destination.read_file(row["repository"], binding["commit_sha"], binding["context_path"])
                if context is None or hashlib.sha256(context).hexdigest() != binding["context_sha256"]:
                    raise AgentRunError("support_changed", f"the activated starting context {binding['context_path']} no longer matches its verified hash")
                inputs["specialist-context.md"] = context
            inputs["support-binding.json"] = _json({"confirmed_specialist_role_ref": ref, "activated_support": json.loads(binding["activation_json"])})
            return inputs
        if isinstance(ref, Mapping):
            destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
            role = destination.read_file(row["repository"], ref["commit"], ref["path"])
            if role is not None:
                if hashlib.sha256(role).hexdigest() != ref["sha256"]:
                    raise AgentRunError("specialist_changed", f"the specialist role {ref['path']} does not match the confirmed hash")
                inputs["specialist-role.md"] = role
                context = destination.read_file(row["repository"], ref["commit"], ref["path"].rsplit("/", 1)[0] + "/context.md")
                if context is not None:
                    inputs["specialist-context.md"] = context
        return inputs

    # -- coder

    def _start_coder(self, row: Mapping[str, Any], packet: Mapping[str, Any], recovery_note: str | None = None, correction: list[dict[str, Any]] | None = None) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], packet["packet_key"]
        config = json.loads(row["config_json"])
        route = config["coder_routes"][packet["route_id"]]
        pending = self._packet_pending(packet)
        attempt = int(pending.get("coder_attempt", 0)) + (1 if recovery_note is None else 0)
        assignment_id = f"{activity_id}-{key}-code-{attempt}"
        if pending.get("correction"):
            base = packet["head_commit"]
        elif packet["head_commit"] is None and recovery_note is None and not pending.get("run_base"):
            base = str(self._ensure_branch(row, packet["milestone_key"])["head_commit"])
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_execution_packets SET base_commit = ? WHERE activity_id = ? AND packet_key = ?", (base, activity_id, key))
        else:
            base = packet["base_commit"]
        if pending.get("correction") and correction is None:
            correction = pending["correction"]["findings"]
        pending["run_base"] = base
        branch = packet["branch"]
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        mirror = self._mirror(row["project_id"])
        destination.fetch_source(row["repository"], base, mirror)
        inputs = self._role_inputs(row, packet)
        if correction:
            inputs["review-findings.json"] = _json({"findings": correction})
        paths = self._packet_paths(packet)
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _CODER_TASK.format(base=base, branch=branch, paths=", ".join(paths), common=_COMMON_RULES, correction=(_CORRECTION if correction else "") + note)
        decision_version = f"a{attempt}"

        def prepare(workspace) -> None:
            execution_git.prepare_clone(mirror, base, workspace.paths.output / "work", branch)
            execution_git.prepare_agent_home(workspace.paths.scratch / "home")

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="packet_coder",
                role_responsibilities=("Deliver exactly this work packet as a working, connected change inside its permitted paths.",),
                task=task, source_commit=base, decision_version=decision_version,
                instructions={"session_id": run_id, "claude_tools": _CODER_TOOLS, "task_kind": "implement_packet", "packet": key, "branch": branch, "permitted_paths": paths},
                permitted_actions=("read_source", "write_output"), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("A missing prerequisite blocks the packet.",), response_schema=CODER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None, prepare)

        self._launch(row, pending, "coder_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "packet_coder")
        pending["coder_attempt"] = attempt
        pending.pop("plan_seen", None)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = ?, pending_json = ?, attempts = attempts + ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                       ("correcting" if correction else "coding", canonical_json(pending), 0 if recovery_note is not None else 1, _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Coder started for {key}: {route['tool']} {route['model']} (route {packet['route_id']}), assignment {assignment_id}, base {base[:12]}, branch {branch}" + (" (correction)" if correction else "") + ".")
            self._activity(tx, activity_id, "running", f"Coding {key} with {route['tool']}")

    def _advance_coder(self, row: Mapping[str, Any], packet: Mapping[str, Any]) -> None:
        assert self.runs is not None
        pending = self._packet_pending(packet)
        current = pending.get("coder_run")
        if current is None:
            self._start_coder(row, packet)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            self._capture_plan(row, packet, pending, current["run_id"])
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            self._capture_plan(row, packet, pending, current["run_id"], final=True)
            self._finish_coder(row, packet, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if pending.get("last_recovery_detail") == detail:
                self._fail_packet(row, packet, f"the same coder error came back after a correction: {detail}")
                return
            pending["last_recovery_detail"] = detail
            pending.pop("coder_run", None)
            self._save_packet(row["activity_id"], packet["packet_key"], pending)
            self._start_coder(row, {**packet, "pending_json": canonical_json(pending)}, recovery_note=detail)
            return
        if view.state == "cancelled":
            return
        self._fail_packet(row, packet, f"coder run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else ""))

    def _run_workspace(self, run_id: str) -> Path | None:
        with self.database.read_connection() as connection:
            found = connection.execute("SELECT workspace_json FROM service_agent_runs WHERE run_id = ?", (run_id,)).fetchone()
        if not found or not found[0]:
            return None
        return Path(json.loads(found[0])["paths"]["output"])

    def _capture_plan(self, row: Mapping[str, Any], packet: Mapping[str, Any], pending: dict[str, Any], run_id: str, final: bool = False) -> None:
        """The coder's plan is saved and shown as soon as its file appears, before its work continues."""
        if pending.get("plan_seen") == run_id:
            return
        output = self._run_workspace(run_id)
        if output is None or not (output / "plan.json").is_file():
            return
        try:
            plan = json.loads((output / "plan.json").read_text(encoding="utf-8"))
            self._check_plan(plan)
        except (OSError, ValueError):
            return  # still being written, or not valid yet; the final result is checked strictly
        pending["plan_seen"] = run_id
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET plan_json = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                       (canonical_json({"run_id": run_id, "seen_at": _now(), "plan": plan}), canonical_json(pending), _now(), row["activity_id"], packet["packet_key"]))
            self._say(tx, row["project_id"], row["activity_id"], f"Plan for {packet['packet_key']} saved before its work continues: " + "; ".join(str(x) for x in plan["intended_changes"])[:500])
            self._emit(tx, row["project_id"], row["activity_id"], "execution.plan_saved", {"packet_key": packet["packet_key"], "run_id": run_id})

    @staticmethod
    def _check_plan(plan: object) -> None:
        if not isinstance(plan, Mapping) or plan.get("schema") != "execution_plan_v1" or set(plan) != {"schema", *PLAN_KEYS}:
            raise ValueError("the plan does not match execution_plan_v1")
        for name in PLAN_KEYS:
            if not isinstance(plan[name], list) or not all(isinstance(x, str) and x.strip() for x in plan[name]) or (name != "blockers" and not plan[name]):
                raise ValueError(f"plan {name} is invalid")

    def _finish_coder(self, row: Mapping[str, Any], packet: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        """The coder run completed: verify the working clone, commit and journal the push."""
        assert self.runs is not None
        response = self.runs.response(current["run_id"]) or {}
        activity_id, key = row["activity_id"], packet["packet_key"]
        assignment = self.runs.assignment_state(current["assignment_id"])
        if assignment["state"] == "waiting_for_answers":
            self._fail_packet(row, packet, "the coder needs information it does not have: " + str(response.get("summary", ""))[:300])
            return
        base = pending["run_base"]
        output = self._run_workspace(current["run_id"])
        try:
            if output is None or not (output / "work").is_dir():
                raise execution_git.GitError("work_missing", "the coder's working clone is missing")
            if response.get("base_revision") != base:
                raise execution_git.GitError("wrong_base", f"the coder reported base {response.get('base_revision')}, not {base}")
            if response.get("blockers") or response.get("unfinished"):
                raise BlockedResult("the coder reports blockers or unfinished work: " + "; ".join(map(str, [*response.get("blockers", []), *response.get("unfinished", [])]))[:400])
            plan = json.loads((output / "plan.json").read_text(encoding="utf-8"))
            self._check_plan(plan)
            sealed = execution_git.seal(output / "work", base, packet["branch"], f"{key}: {packet['subject']}")
            if sealed["head"] == base:
                raise execution_git.GitError("no_change", "the coder made no change to the repository")
            outside = execution_git.outside_scope(sealed["changed_paths"], self._packet_paths(packet))
            if outside:
                raise execution_git.GitError("out_of_scope", "the change touches paths outside the packet's permitted paths: " + ", ".join(outside[:8]))
            claimed = sorted(str(p) for p in response.get("changed_paths", []))
            if claimed != sealed["changed_paths"]:
                raise execution_git.GitError("changed_paths_mismatch", f"the coder listed {claimed} but the change touches {sealed['changed_paths']}")
            diff = execution_git.diff_text(output / "work", base, sealed["head"])
        except BlockedResult as blocked:
            self._fail_packet(row, packet, str(blocked))
            return
        except (execution_git.GitError, ValueError, OSError) as error:
            self._reject_coder_result(row, packet, pending, current, f"{getattr(error, 'code', type(error).__name__)}: {error}")
            return
        directory = self.state_dir / "execution" / activity_id / key
        directory.mkdir(parents=True, exist_ok=True)
        attempt = int(pending.get("coder_attempt", 1))
        (directory / f"round-{int(packet['rounds_used']) + 1}.diff").write_text(diff, encoding="utf-8")
        # Keep the clone (with its commit) where the service, not the agent, owns it until the push is verified.
        keep = directory / f"clone-{attempt}"
        if keep.exists():
            shutil.rmtree(keep, ignore_errors=True)
        shutil.copytree(output / "work", keep, symlinks=True)
        evidence = self.runs.run_evidence(current["run_id"])
        result = {"response": response, "changed_paths": sealed["changed_paths"], "head": sealed["head"], "base": base, "commits": sealed["commits"], "run_evidence": evidence,
                  "run_id": current["run_id"], "diff_file": str(directory / f"round-{int(packet['rounds_used']) + 1}.diff"), "clone": str(keep)}
        pending["pushing"] = {"head": sealed["head"], "base": base, "clone": str(keep)}
        pending.pop("coder_run", None)
        pending.pop("correction", None)
        pending.pop("last_recovery_detail", None)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'publishing', result_json = ?, head_commit = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                       (canonical_json(result), sealed["head"], canonical_json(pending), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Coder result for {key} accepted for publication: {len(sealed['changed_paths'])} file(s) changed ({', '.join(sealed['changed_paths'])[:200]}), local commit {sealed['head'][:12]}; the service verifies it on the remote before review.")

    def _reject_coder_result(self, row: Mapping[str, Any], packet: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str], reason: str) -> None:
        assert self.runs is not None
        self.runs.reject_result(current["run_id"], "malformed_response", reason)
        assignment = self.runs.assignment_state(current["assignment_id"])
        if assignment["state"] != "needs_recovery" or pending.get("last_recovery_detail") == reason:
            self._fail_packet(row, packet, f"the coder's result was rejected: {reason}")
            return
        pending["last_recovery_detail"] = reason
        pending.pop("coder_run", None)
        self._save_packet(row["activity_id"], packet["packet_key"], pending)
        self._start_coder(row, {**packet, "pending_json": canonical_json(pending)}, recovery_note=reason)

    def _advance_publish(self, row: Mapping[str, Any], packet: Mapping[str, Any]) -> None:
        """Push the exact local commit with the bound repository profile and record it only after reading the remote back."""
        activity_id, key = row["activity_id"], packet["packet_key"]
        pending = self._packet_pending(packet)
        push = pending["pushing"]
        profile = self.profiles[json.loads(row["profile_json"])["profile"]]
        destination = self._destination(profile)
        operation_id = f"{activity_id}-{key}-push-{push['head'][:12]}"
        journal = self._read("SELECT * FROM service_execution_journal WHERE operation_id = ?", (operation_id,))
        if journal is None:
            before = destination.branch_head(row["repository"], packet["branch"])
            with self.database.transaction() as tx:
                tx.execute(
                    "INSERT OR IGNORE INTO service_execution_journal(operation_id, activity_id, packet_key, kind, repository, branch, profile_json, intended_head, remote_before, state, created_at) "
                    "VALUES (?, ?, ?, 'push', ?, ?, ?, ?, ?, 'prepared', ?)",
                    (operation_id, activity_id, key, row["repository"], packet["branch"], row["profile_json"], push["head"], before, _now()),
                )
        try:
            remote = destination.push_branch(row["repository"], Path(push["clone"]), packet["branch"], push["head"])
        except DestinationError as error:
            if error.code in {"github_unreachable", "push_failed"} and journal is not None and journal["state"] != "failed":
                raise
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_execution_journal SET state = 'failed', detail = ? WHERE operation_id = ?", (f"{error.code}: {error}"[:300], operation_id))
            raise
        # A verified remote head: fetch it so the reviewer's read-only checkout is of the exact remote revision.
        destination.fetch_source(row["repository"], remote, self._mirror(row["project_id"]))
        pending.pop("pushing", None)
        shutil.rmtree(push["clone"], ignore_errors=True)
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (remote, operation_id))
            tx.execute("UPDATE service_execution_packets SET state = 'review_ready', remote_head = ?, head_commit = ?, pending_json = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                       (remote, remote, canonical_json(pending), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Branch {packet['branch']} for {key} verified on the remote at {remote[:12]} (equals the local commit). Independent review is next.")
            self._emit(tx, row["project_id"], activity_id, "execution.revision_published", {"packet_key": key, "branch": packet["branch"], "commit": remote})

    # -- reviewer

    def _reviewer_route(self, config: Mapping[str, Any], packet: Mapping[str, Any]) -> dict[str, Any]:
        """The configured reviewer route that differs from the packet's author (tool and exact model)."""
        author = (packet["tool"], packet["model"])
        pair = config["reviewers"]["packet"]
        for name in ("primary", "backup"):
            candidate = pair.get(name)
            if candidate and (candidate["tool"], candidate["model"]) != author:
                return candidate
        raise AgentRunError("no_independent_reviewer", "no configured packet reviewer differs from the author's tool and model")

    def _start_reviewer(self, row: Mapping[str, Any], packet: Mapping[str, Any], recovery_note: str | None = None) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], packet["packet_key"]
        config = json.loads(row["config_json"])
        pending = self._packet_pending(packet)
        reviewer = self._reviewer_route(config, packet)
        round_number = int(packet["rounds_used"]) + 1
        assignment_id = f"{activity_id}-{key}-review-{round_number}"
        result = json.loads(packet["result_json"])
        head, base = packet["head_commit"], result["base"]
        mirror = self._mirror(row["project_id"])
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        destination.fetch_source(row["repository"], head, mirror)
        inputs = self._role_inputs(row, packet)
        inputs.update({
            "range.json": _json({"base": base, "head": head, "branch": packet["branch"]}),
            "coder-result.json": _json(result["response"]),
            "plan.json": _json((json.loads(packet["plan_json"]) if packet["plan_json"] else {}).get("plan", {})),
            "diff.patch": Path(result["diff_file"]).read_bytes(),
        })
        prior = self._rows("SELECT findings_json FROM service_execution_reviews WHERE activity_id = ? AND packet_key = ? ORDER BY review_round", (activity_id, key))
        if prior:
            inputs["prior-findings.json"] = _json({"findings": json.loads(prior[-1]["findings_json"])})
        paths = self._packet_paths(packet)
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _REVIEW_TASK.format(head=head, later=_REVIEW_LATER if prior else "", paths=", ".join(paths)) + note

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="packet_reviewer",
                role_responsibilities=("Decide whether the exact submitted revision satisfies the packet; never edit code or authorize a merge.",),
                task=task, source_commit=head, decision_version=f"r{round_number}",
                instructions={"session_id": run_id, "claude_tools": _REVIEWER_TOOLS, "task_kind": "review_packet", "packet": key},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": reviewer["run_timeout_seconds"]},
                clarification_conditions=("The range cannot be verified.",), response_schema=REVIEWER_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "reviewer_run", assignment_id, reviewer["tool"], reviewer["model"], reviewer["run_timeout_seconds"], recovery_note is not None, build, "packet_reviewer")
        pending["reviewer"] = {"tool": reviewer["tool"], "model": reviewer["model"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_packets SET state = 'reviewing', pending_json = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?", (canonical_json(pending), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id,
                      f"Independent review round {round_number} of {packet['round_limit']} for {key} started: reviewer {reviewer['tool']} {reviewer['model']} (author {packet['tool']} {packet['model']}), exact revision {head[:12]}.")
            self._activity(tx, activity_id, "running", f"Reviewing {key} (round {round_number})")

    def _advance_reviewer(self, row: Mapping[str, Any], packet: Mapping[str, Any]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], packet["packet_key"]
        pending = self._packet_pending(packet)
        current = pending.get("reviewer_run")
        if current is None:
            self._start_reviewer(row, packet)
            return
        view = self.runs.poll(current["run_id"])
        if view.state in {"reserved", "running", "stopping"}:
            return
        assignment = self.runs.assignment_state(current["assignment_id"])
        if view.state == "completed":
            self._accept_review(row, packet, pending, current)
            return
        if assignment["state"] == "needs_recovery":
            detail = view.terminal_reason or view.failure_code or "technical_failure"
            if pending.get("last_recovery_detail") == detail:
                self._fail_packet(row, packet, f"the same reviewer error came back after a correction: {detail}")
                return
            pending["last_recovery_detail"] = detail
            pending.pop("reviewer_run", None)
            self._save_packet(activity_id, key, pending)
            self._start_reviewer(row, {**packet, "pending_json": canonical_json(pending)}, recovery_note=detail)
            return
        if view.state == "cancelled":
            return
        self._fail_packet(row, packet, f"reviewer run {view.state}" + (f" ({view.failure_code})" if view.failure_code else "") + (f": {view.terminal_reason}" if view.terminal_reason else ""))

    def _accept_review(self, row: Mapping[str, Any], packet: Mapping[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], packet["packet_key"]
        response = self.runs.response(current["run_id"]) or {}
        result = json.loads(packet["result_json"])
        expected = {"base": result["base"], "head": packet["head_commit"]}
        if response.get("result") != "completed" or response.get("reviewed_range") != expected:
            self.runs.reject_result(current["run_id"], "conflicting_response", "the review does not state the exact range it was given")
            pending.pop("reviewer_run", None)
            assignment = self.runs.assignment_state(current["assignment_id"])
            if assignment["state"] != "needs_recovery":
                self._fail_packet(row, packet, "the review did not state the exact revision it reviewed")
                return
            self._save_packet(activity_id, key, pending)
            self._start_reviewer(row, {**packet, "pending_json": canonical_json(pending)}, recovery_note="the review must copy reviewed_range exactly from input/range.json")
            return
        round_number = int(packet["rounds_used"]) + 1
        findings = [{**f, "finding_id": f"{activity_id}-{key}-r{round_number}-{f['local_key']}"} for f in response.get("findings", [])]
        reviewer = pending["reviewer"]
        outcome = response["review_outcome"]
        blocking = [f for f in findings if f["severity"] == "blocking"]
        limit = int(packet["round_limit"]) + len(pending.get("grants", []))
        with self.database.transaction() as tx:
            tx.execute(
                "INSERT INTO service_execution_reviews(activity_id, packet_key, review_round, assignment_id, run_id, reviewer_tool, reviewer_model, author_tool, author_model, reviewed_base, reviewed_head, outcome, summary, findings_json, independence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (activity_id, key, round_number, current["assignment_id"], current["run_id"], reviewer["tool"], reviewer["model"], packet["tool"], packet["model"], expected["base"], expected["head"],
                 outcome, str(response["summary"])[:2000], _dump(findings), str(response.get("independence", ""))[:500], _now()),
            )
            pending.pop("reviewer_run", None)
            pending.pop("last_recovery_detail", None)
            if outcome == "APPROVE":
                tx.execute("UPDATE service_execution_packets SET state = 'approved', rounds_used = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                           (round_number, canonical_json(pending), _now(), activity_id, key))
                self._event(tx, activity_id, "packet_approved", key, f"{key} approved at {expected['head'][:12]} after {round_number} review round(s)")
                self._say(tx, row["project_id"], activity_id, f"Review round {round_number} of {limit} for {key}: APPROVED at {expected['head'][:12]} by {reviewer['tool']} {reviewer['model']}. Only this exact revision is eligible for integration. {str(response['summary'])[:300]}")
            elif round_number < limit:
                pending["correction"] = {"findings": blocking, "round": round_number}
                pending.pop("coder_run", None)
                tx.execute("UPDATE service_execution_packets SET state = 'reserved', rounds_used = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                           (round_number, canonical_json(pending), f"correcting {len(blocking)} blocking finding(s)", _now(), activity_id, key))
                self._say(tx, row["project_id"], activity_id, f"Review round {round_number} of {limit} for {key}: changes requested ({len(blocking)} blocking): " + "; ".join(f"{f['subject']}" for f in blocking)[:400] + ". The coder gets one targeted correction.")
            else:
                pending["limit"] = {"assignment_id": current["assignment_id"], "round": round_number}
                tx.execute("UPDATE service_execution_packets SET state = 'limit_paused', rounds_used = ?, pending_json = ?, note = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?",
                           (round_number, canonical_json(pending), f"review limit reached with {len(blocking)} blocking finding(s)", _now(), activity_id, key))
                self._event(tx, activity_id, "limit_reached", key, f"{key} reached its review limit ({round_number} of {limit}) with blocking findings; the Owner decides")
                self._say(tx, row["project_id"], activity_id, f"Review round {round_number} of {limit} for {key}: blocking findings remain at the review limit, so {key} stays unapproved and unmerged. Grant one extra attempt or keep it paused.")

    def _fail_packet(self, row: Mapping[str, Any], packet: Mapping[str, Any], reason: str) -> None:
        with self.database.transaction() as tx:
            current = self._row(tx, "SELECT state FROM service_execution_packets WHERE activity_id = ? AND packet_key = ?", (row["activity_id"], packet["packet_key"]))
            if current is None or current["state"] in {"failed", "approved", "limit_paused"}:
                return
            tx.execute("UPDATE service_execution_packets SET state = 'failed', note = ?, updated_at = ? WHERE activity_id = ? AND packet_key = ?", (reason[:500], _now(), row["activity_id"], packet["packet_key"]))
            self._event(tx, row["activity_id"], "packet_failed", packet["packet_key"], f"{packet['packet_key']} stopped: {reason[:300]}")
            self._say(tx, row["project_id"], row["activity_id"], f"Packet {packet['packet_key']} stopped without approval: {reason[:400]}. Nothing was merged; other eligible work continues.")

    # ------------------------------------------------------------------ status

    def _settle(self, activity_id: str) -> None:
        row = self._read("SELECT * FROM service_executions WHERE activity_id = ?", (activity_id,))
        if row is None or row["state"] not in {"running", "blocked"}:
            return
        packets = self._packets(activity_id)
        pending = json.loads(row["pending_json"] or "{}")
        config_now = json.loads(row["config_json"])
        queue = self._queue(activity_id)
        active = [p for p in packets if p["state"] in {*_PACKET_ACTIVE, "publishing", "review_ready"}]
        queued = [e for e in queue if e["state"] in {"queued", "integrating", "publishing", "reviewing", "merging"}]
        integrated = [p for p in packets if p["state"] == "integrated"]
        waiting = [p for p in packets if p["state"] == "pending"]
        stuck = [p for p in packets if p["state"] in {"failed", "limit_paused"}]
        stuck_entries = [e for e in queue if e["state"] in {"blocked", "limit_paused"}]
        held = [d for d in self._deliveries(activity_id) if d["state"] == "held"]
        verifying, verification_parts = self._verification_status(activity_id)
        manager_active = pending.get("manager_run") is not None
        supports = self._architects(activity_id, "support")
        support_active = [a for a in supports if a["state"] in ("requested", "drafting", "reviewing", "correcting", "publishing", "recommending")]
        support_stuck = [a for a in supports if a["state"] in ("limit_paused", "blocked_route", "replanning_required")]
        determinations = [a for a in self._architects(activity_id) if a["kind"] != "support"]
        support_active += [a for a in determinations if a["state"] in ("requested", "determining", "publishing")]
        support_stuck += [a for a in determinations if a["state"] in ("blocked_route", "awaiting_disposition")]
        if self._settled_for_replanning(row):
            self._end_for_replanning(row)
            return
        unanswered = any(not q.get("answered") for q in pending.get("questions", {}).values())
        if active or manager_active or queued or support_active or verifying:
            state, text = "running", f"{len(active)} packet(s) in progress" + (f", {len(support_active)} architectural support assignment(s) in progress" if support_active else "") + (f", {len(queued)} integration queue entr{'y' if len(queued) == 1 else 'ies'} in progress" if queued else "") + (f", {verifying} milestone verification step(s) in progress" if verifying else "") + (", Development Manager planning" if manager_active else "")
        elif unanswered:
            state, text = "running", "Waiting for your answer to the Development Manager"
        elif waiting and self._read("SELECT 1 AS n FROM service_execution_events WHERE activity_id = ? AND handled = 0", (activity_id,)) is not None:
            state, text = "running", "Waiting for the Development Manager's next planning pass"
        else:
            state = "blocked"
            parts = []
            if integrated:
                parts.append(f"{len(integrated)} packet(s) are integrated into their milestone branches")
            parts.extend(verification_parts)
            if integrated and not verification_parts and self._qa_config_problem(config_now):
                parts.append(str(self._qa_config_problem(config_now)))
            if waiting:
                parts.append(f"{len(waiting)} packet(s) wait for undelivered dependencies")
            if held:
                parts.append(f"{len(held)} dependency delivery(ies) wait for a source milestone to complete")
            if stuck:
                parts.append(f"{len(stuck)} packet(s) need attention: " + "; ".join(p["packet_key"] for p in stuck))
            if support_stuck:
                parts.append(f"{len(support_stuck)} architectural support assignment(s) need attention: " + "; ".join(f"{a['assignment_key']} ({a['state']})" for a in support_stuck))
            if stuck_entries:
                parts.append("the integration queue is blocked at entry " + ", ".join(str(e["entry_id"]) for e in stuck_entries[:1]) + " (nothing behind it is skipped)")
            text = "No further packet can start: " + ("; ".join(parts) or "nothing left to run")
        actions: tuple[ActivityAction, ...] = ()
        if any(a["state"] == "awaiting_disposition" for a in determinations):
            actions = tuple(ActivityAction(f"{activity_id}-disposition-{c}", label, "decision") for c, label in (
                ("continue_unaffected", "Continue unaffected work"), ("finish_safe_work", "Stop new starts and finish safe running work"),
                ("stop_affected_or_all", "Stop affected or all running work"), ("finish_current_for_replanning", "Finish current work and prioritize replanning")))
            text += ". Re-registration is required for some work: choose what happens to current work"
        if any(p["state"] == "limit_paused" for p in packets) or any(e["state"] == "limit_paused" for e in queue) or any(a["state"] == "limit_paused" for a in supports):
            actions = (ActivityAction(f"{activity_id}-grant", "Grant one extra review attempt", "decision"), ActivityAction(f"{activity_id}-remain", "Remain paused", "decision"))
            text += ". Review limit reached: grant one extra attempt or keep it paused"
        if state != row["state"] or self._current_waiting(activity_id) != text:
            with self.database.transaction() as tx:
                tx.execute("UPDATE service_executions SET state = ? WHERE activity_id = ? AND state IN ('running', 'blocked')", (state, activity_id))
                self._activity(tx, activity_id, state, text, actions)

    def _current_waiting(self, activity_id: str) -> str | None:
        found = self._read("SELECT waiting_reason FROM service_activities WHERE activity_id = ?", (activity_id,))
        return None if found is None else found["waiting_reason"]

    def project_view(self, project_id: str) -> dict[str, Any] | None:
        row = self._read("SELECT activity_id FROM service_executions WHERE project_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1", (project_id,))
        return None if row is None else self.view(str(row["activity_id"]))

    def configuration_view(self) -> dict[str, Any]:
        """What a start can choose from, read from the current configuration; a plain error when it is unusable."""
        try:
            config = execution_config.validate(self.config_source())
        except execution_config.ExecutionConfigError as error:
            return {"valid": False, "error": str(error), "manager_routes": [], "coder_routes": []}
        return {"valid": True, "error": None, "sha256": execution_config.digest(config),
                "manager_routes": [{"route_id": rid, "tool": r["tool"], "model": r["model"]} for rid, r in config["development_manager"]["routes"].items()],
                "coder_routes": [{"route_id": rid, "tool": r["tool"], "model": r["model"], "location": r["location"], "default": rid == config["coder_default_route_id"]} for rid, r in config["coder_routes"].items()]}

    def view(self, activity_id: str) -> dict[str, Any] | None:
        row = self._read("SELECT * FROM service_executions WHERE activity_id = ?", (activity_id,))
        if row is None:
            return None
        pending = json.loads(row["pending_json"] or "{}")
        version = self._read("SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
        activity = self._read("SELECT started_at, waiting_reason FROM service_activities WHERE activity_id = ?", (activity_id,))
        runs = self._rows(
            "SELECT r.run_id, r.assignment_id, r.state, r.kind, r.tool_version, r.model_id, r.active_seconds, r.failure_code, a.role, a.tool FROM service_agent_runs r "
            "JOIN service_agent_assignments a ON a.assignment_id = r.assignment_id WHERE a.activity_id = ? ORDER BY r.reserved_at", (activity_id,))
        packets = []
        for p in self._packets(activity_id):
            record = json.loads(p["record_json"])
            p_pending = self._packet_pending(p)
            reviews = self._rows("SELECT review_round, outcome, reviewer_tool, reviewer_model, reviewed_head, summary, findings_json, created_at FROM service_execution_reviews WHERE activity_id = ? AND packet_key = ? ORDER BY review_round", (activity_id, p["packet_key"]))
            plan = None if not p["plan_json"] else json.loads(p["plan_json"])
            seconds = {"coder": 0.0, "reviewer": 0.0}
            for run in runs:
                if run["assignment_id"].startswith(f"{activity_id}-{p['packet_key']}-code"):
                    seconds["coder"] += float(run["active_seconds"] or 0)
                elif run["assignment_id"].startswith(f"{activity_id}-{p['packet_key']}-review"):
                    seconds["reviewer"] += float(run["active_seconds"] or 0)
            packets.append({
                "key": p["packet_key"], "subject": p["subject"], "milestone": p["milestone_key"], "state": p["state"], "dependencies": json.loads(p["dependency_keys_json"]),
                "route": p["route_id"], "tool": p["tool"], "model": p["model"], "reason": p["reason"], "branch": p["branch"], "base_commit": p["base_commit"],
                "head_commit": p["head_commit"], "remote_verified": bool(p["remote_head"]) and p["remote_head"] == p["head_commit"], "permitted_paths": record.get("permitted_paths", []),
                "plan": None if plan is None else plan["plan"], "review": {"completed": p["rounds_used"], "limit": int(p["round_limit"]) + len(p_pending.get("grants", []))},
                "reviews": [{"round": r["review_round"], "outcome": r["outcome"], "reviewer": f"{r['reviewer_tool']} {r['reviewer_model']}", "head": r["reviewed_head"], "summary": r["summary"],
                             "blocking": sum(1 for f in json.loads(r["findings_json"]) if f["severity"] == "blocking"), "findings": json.loads(r["findings_json"])} for r in reviews],
                "changed_paths": (json.loads(p["result_json"])["changed_paths"] if p["result_json"] else []), "note": p["note"],
                "active_seconds": {k: round(v, 1) for k, v in seconds.items()},
            })
        measured = {"active_agent_seconds": round(sum(float(r["active_seconds"] or 0) for r in runs), 1),
                    "tokens": "not reported by the tools", "cost": "not reported by the tools", "context": "not reported by the tools"}
        events = self._rows("SELECT event_id, kind, packet_key, detail, handled FROM service_execution_events WHERE activity_id = ? ORDER BY event_id DESC LIMIT 20", (activity_id,))
        plans = self._rows("SELECT pass_number, run_id, accepted_json, rejected_json, created_at FROM service_execution_plans WHERE activity_id = ? ORDER BY pass_number", (activity_id,))
        actions: list[str] = []
        decisions = []
        for p in self._packets(activity_id):
            limit = self._packet_pending(p).get("limit")
            if p["state"] == "limit_paused" and limit:
                decisions.append({"target": "packet_review", "packet_key": p["packet_key"], "assignment_id": limit["assignment_id"], "round": limit["round"], **self._recommendation_fields(activity_id, limit["assignment_id"])})
        for e in self._queue(activity_id):
            limit = json.loads(e["pending_json"] or "{}").get("limit")
            if e["state"] == "limit_paused" and limit:
                decisions.append({"target": "integration_review", "packet_key": self._entry_subject(e), "assignment_id": limit["assignment_id"], "round": limit["round"], **self._recommendation_fields(activity_id, limit["assignment_id"])})
        for a in self._architects(activity_id, "support"):
            limit = json.loads(a["pending_json"] or "{}").get("limit")
            if a["state"] == "limit_paused" and limit:
                decisions.append({"target": "execution_support_fidelity_review", "packet_key": a["packet_key"], "assignment_id": a["assignment_key"], "round": limit["round"],
                                  "recommendation": limit["recommendation"], "rationale": limit["rationale"]})
        for g in self._architects(activity_id, "milestone_gap"):
            trigger, result = json.loads(g["trigger_json"]), json.loads(g["result_json"]) if g["result_json"] else None
            if trigger.get("exhausted") and result and result["owner_recommendation"] in ("grant_one", "remain_paused") and "owner_decision" not in json.loads(g["pending_json"] or "{}"):
                decisions.append({"target": "milestone_review", "packet_key": trigger["milestone_key"], "assignment_id": g["assignment_key"], "round": 0,
                                  "recommendation": result["owner_recommendation"], "rationale": result["rationale"]})
        for d in [*self.determination_view(activity_id), *[{**g, "determination_id": g["gap_id"], "result": self._gap_result(activity_id, g["gap_id"])} for g in self.gap_view(activity_id)]]:
            if d["state"] == "awaiting_disposition" and d["result"]:
                decisions.append({"target": "execution_work_disposition", "packet_key": ", ".join(d["result"]["affected_work"]), "assignment_id": d["determination_id"], "round": 0,
                                  "recommendation": d["result"]["disposition_recommendation"], "rationale": d["result"]["rationale"], "choices": list(DISPOSITION_CHOICES)})
        if decisions:
            actions.append("respond_to_owner_decision")
        open_questions = [q for q, i in pending.get("questions", {}).items() if not i.get("answered")]
        return {
            "activity_id": activity_id, "project_id": row["project_id"], "state": row["state"], "version": None if version is None else int(version["version"]),
            "waiting": None if activity is None else activity["waiting_reason"], "started_at": None if activity is None else activity["started_at"], "note": row["note"],
            "source_commit": row["source_commit"], "product_master": {"branch": row["master_branch"], "start_commit": row["master_commit"], "observed_at": row["observed_at"]},
            "confirmed_breakdown": {k: json.loads(row["confirmed_ref_json"])[k] for k in ("version", "commit", "manifest_path")},
            "configuration": {"sha256": row["config_sha256"], "bundle": json.loads(row["bundle_json"])},
            "manager": {"route_id": row["manager_route_id"], "tool": row["manager_tool"], "model": row["manager_model"], "passes": int(row["pass_number"]),
                        "planning": pending.get("manager_run") is not None, "understanding": pending.get("understanding"), "priorities": pending.get("priorities", []),
                        "blockers": pending.get("blockers", []), "checkpoint": pending.get("checkpoint")},
            "integration": self.integration_view(activity_id), "verification": self.verification_view(activity_id),
            "support": self.support_view(activity_id), "determinations": self.determination_view(activity_id), "gaps": self.gap_view(activity_id), "disposition": self.disposition_view(row),
            "packets": packets, "plans": [{"pass": p["pass_number"], "accepted": json.loads(p["accepted_json"]), "rejected": json.loads(p["rejected_json"]), "at": p["created_at"]} for p in plans],
            "events": events, "open_questions": open_questions, "measurements": measured, "actions": actions, "owner_decisions": decisions,
            "runs": [{"run_id": r["run_id"], "role": r["assignment_id"].rsplit("-", 2)[-2] if "-" in r["assignment_id"] else r["role"], "state": r["state"], "tool": r["tool"], "model": r["model_id"], "tool_version": r["tool_version"], "seconds": r["active_seconds"]} for r in runs],
        }

    # --------------------------------------------------------------- decisions

    def prepare_owner_decision(self, request: RequestLike) -> PreparedOperation:
        if request.project_id is None or request.activity_id is None or request.expected_version is None:
            raise ValueError("owner.decision needs project, activity and the displayed activity version")
        payload = dict(request.payload)
        if set(payload) != {"target", "choice", "assignment_id"}:
            raise ValueError("owner.decision payload must be target, choice and assignment_id")
        if payload["target"] == "execution_work_disposition":
            if payload["choice"] not in DISPOSITION_CHOICES:
                raise ValueError("execution_work_disposition takes choice " + ", ".join(DISPOSITION_CHOICES))
        elif payload["target"] not in {"packet_review", "integration_review", "execution_support_fidelity_review", "milestone_review"} or payload["choice"] not in {"grant_one", "remain_paused"}:
            raise ValueError("Execution accepts target packet_review, integration_review, execution_support_fidelity_review or milestone_review with choice grant_one or remain_paused, or execution_work_disposition")
        activity_id = request.activity_id

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = self._row(transaction, "SELECT * FROM service_executions WHERE activity_id = ? AND project_id = ?", (activity_id, request.project_id))
            if row is None:
                raise RequestRejection(404, "execution_not_found", "the Execution activity was not found", fields={"activity_id": activity_id})
            current = self._row(transaction, "SELECT version FROM entity_versions WHERE entity_id = ?", (activity_id,))
            if current is not None and int(current["version"]) != request.expected_version:
                raise RequestRejection(409, "stale_version", "the activity changed since it was displayed", fields={"activity_version": int(current["version"])})
            found = None
            if payload["target"] == "execution_work_disposition":
                return self._disposition_decision(transaction, request, row, payload, next_version)
            if payload["target"] in {"packet_review", "integration_review"}:
                self._limit_determination(transaction, activity_id, payload["assignment_id"])
            if payload["target"] == "integration_review":
                return self._integration_decision(transaction, request, row, payload, next_version)
            if payload["target"] == "milestone_review":
                return self._milestone_review_decision(transaction, request, row, payload, next_version)
            if payload["target"] == "execution_support_fidelity_review":
                return self._support_decision(transaction, request, row, payload, next_version)
            for candidate in self._row_list(transaction, "SELECT * FROM service_execution_packets WHERE activity_id = ? AND state = 'limit_paused'", (activity_id,)):
                if json.loads(candidate["pending_json"]).get("limit", {}).get("assignment_id") == payload["assignment_id"]:
                    found = candidate
            if found is None:
                raise RequestRejection(409, "no_decision_pending", "no review-limit decision is pending for that review assignment")
            pending = json.loads(found["pending_json"])
            grants = list(pending.get("grants", []))
            key = found["packet_key"]
            if payload["choice"] == "remain_paused":
                text = f"Owner chose to keep {key} paused at {found['rounds_used']} of {int(found['round_limit']) + len(grants)} review rounds. Nothing was approved and no count changed."
            else:
                grants.append({"request_id": request.request_id, "assignment_id": payload["assignment_id"], "granted_at": _now()})
                pending["grants"] = grants
                findings = json.loads(self._row(transaction, "SELECT findings_json FROM service_execution_reviews WHERE activity_id = ? AND packet_key = ? AND review_round = ?", (activity_id, key, found["rounds_used"]))["findings_json"])
                pending["correction"] = {"findings": [f for f in findings if f["severity"] == "blocking"], "round": int(found["rounds_used"])}
                pending.pop("limit", None)
                pending.pop("coder_run", None)
                transaction.execute("UPDATE service_execution_packets SET state = 'reserved', pending_json = ?, note = 'one extra review attempt granted', updated_at = ? WHERE activity_id = ? AND packet_key = ?", (canonical_json(pending), _now(), activity_id, key))
                text = f"Owner granted one extra review attempt for {key} (limit now {int(found['round_limit']) + len(grants)}); the base limit of {found['round_limit']} is unchanged and approval is not forced."
            self._activity(transaction, activity_id, "running", text, version=next_version)
            self._say(transaction, row["project_id"], activity_id, text)
            return OperationResult(data={"activity_id": activity_id, "decision": payload["choice"], "packet": key, "message": text}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

        return PreparedOperation(activity_id, "execution.review_decision_recorded", {"activity_id": activity_id}, apply)

    # ----------------------------------------------------------------- records

    def _event(self, tx: Transaction, activity_id: str, kind: str, packet_key: str | None, detail: str) -> None:
        number = int(tx.execute("SELECT COALESCE(MAX(event_id), 0) + 1 FROM service_execution_events WHERE activity_id = ?", (activity_id,)).fetchone()[0])
        tx.execute("INSERT INTO service_execution_events(activity_id, event_id, kind, packet_key, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)", (activity_id, number, kind, packet_key, detail, _now()))

    def _say(self, tx: Transaction, project_id: str, activity_id: str, text: str) -> None:
        self.records.append_conversation(tx, ConversationRecord(f"execution-{uuid.uuid4().hex}", project_id, "maestro", "status", text, _now(), activity_id))
        self._emit(tx, project_id, activity_id, "execution.updated", {"activity_id": activity_id})

    def _activity(self, tx: Transaction, activity_id: str, state: str | None, waiting: str | None, actions: tuple[ActivityAction, ...] | None = None, *, ended: bool = False, version: int | None = None) -> None:
        current = self._row(tx, "SELECT * FROM service_activities WHERE activity_id = ?", (activity_id,))
        assert current is not None
        existing = tuple(ActivityAction(r[0], r[1], r[2]) for r in tx.execute("SELECT action_id, label, kind FROM service_activity_actions WHERE activity_id = ? ORDER BY sequence", (activity_id,)).fetchall())
        record_version = int(current["version"])
        next_version = record_version + 1
        self.records.update_activity(
            tx,
            ActivityRecord(activity_id, current["project_id"], current["kind"], current["subject"], state or current["state"], next_version, waiting,
                           current["started_at"], _now() if ended else current["ended_at"], existing if actions is None else actions),
            expected_record_version=record_version,
        )
        tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version", (activity_id, next_version))

    def _resolve_question(self, tx: Transaction, question_id: str) -> None:
        q = self._row(tx, "SELECT * FROM service_questions WHERE question_id = ?", (question_id,))
        if q is not None and q["status"] == "answer_received":
            self.records.update_question(tx, QuestionRecord(question_id, q["project_id"], q["activity_id"], q["subject"], q["prompt"], q["requester"], "resolved", int(q["version"]) + 1), expected_record_version=int(q["version"]))
            tx.execute("INSERT INTO entity_versions(entity_id, version) VALUES (?, ?) ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version", (question_id, int(q["version"]) + 1))

    @staticmethod
    def _emit(tx: Transaction, project_id: str, activity_id: str, event_type: str, data: Mapping[str, object]) -> None:
        tx.execute(
            "INSERT INTO outbox_events(schema_version, event_id, occurred_at, project_id, activity_id, type, data_json) VALUES (1, ?, ?, ?, ?, ?, ?)",
            (f"execution-{uuid.uuid4().hex}", _now(), project_id, activity_id, event_type, canonical_json(data)),
        )

    @staticmethod
    def _row(tx: Transaction, sql: str, params: tuple[object, ...] = ()) -> dict[str, Any] | None:
        cursor = tx.execute(sql, params)
        found = cursor.fetchone()
        return None if found is None else {column[0]: value for column, value in zip(cursor.description, found)}

    @staticmethod
    def _row_list(tx: Transaction, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, Any]]:
        cursor = tx.execute(sql, params)
        names = [c[0] for c in cursor.description]
        return [dict(zip(names, r)) for r in cursor.fetchall()]

    def _read(self, sql: str, params: tuple[object, ...] = ()) -> dict[str, Any] | None:
        with self.database.read_connection() as connection:
            cursor = connection.execute(sql, params)
            found = cursor.fetchone()
            return None if found is None else {column[0]: value for column, value in zip(cursor.description, found)}

    def _rows(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, Any]]:
        with self.database.read_connection() as connection:
            cursor = connection.execute(sql, params)
            names = [c[0] for c in cursor.description]
            return [dict(zip(names, r)) for r in cursor.fetchall()]


class BlockedResult(ValueError):
    """The coder reports it could not finish; the packet stops for attention instead of going to review."""


def _dump(value: object) -> str:
    """Canonical JSON for any value (the shared helper accepts only objects)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
