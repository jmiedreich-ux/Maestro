"""Execution milestone gaps: a recorded milestone finding reaches its own bounded Project Architect assignment.

A finding (from milestone Quality Assurance or the milestone outcome review, through ``execution.record_finding``)
starts one read-only assignment over the assembled milestone. Its validated result routes an implementation defect
to the Integration Manager's correction, missing in-scope work to a correction supplement of bounded packets, and a
scope change to the Owner's work disposition. A supplement is validated, published as immutable bytes with a hash the
service stores outside the file, read back from the remote and only then activated; its packets are released to the
Development Manager as ordinary pending work. The assignment cannot approve a milestone, dispatch code, change scope
or start re-registration.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from maestro.agents.execution_contract import DETERMINATION_SCHEMA
from maestro.agents.transport import AgentAssignment
from maestro.foundation import DomainMigration, Transaction, canonical_json

from .agent_runs import AgentRunError, RunBuild
from .architecture_records import encode
from .registration_github import DestinationError
from .registry import OperationResult, PreparedOperation, RequestLike
from .requests import RequestRejection

GAP_MIGRATION = DomainMigration(
    domain="service_execution",
    version=4,
    identity="service-execution-v4-milestone-gaps",
    statements=(
        """
        CREATE TABLE service_execution_findings(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            finding_id TEXT NOT NULL,
            milestone_key TEXT NOT NULL,
            source TEXT NOT NULL CHECK(source IN ('quality_assurance', 'outcome_review')),
            subject TEXT NOT NULL,
            record_json TEXT NOT NULL,
            record_sha256 TEXT NOT NULL,
            state TEXT NOT NULL,
            gap_key TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, finding_id)
        )
        """,
        """
        CREATE TABLE service_execution_supplements(
            activity_id TEXT NOT NULL REFERENCES service_executions(activity_id),
            supplement_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            finding_id TEXT NOT NULL,
            milestone_key TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('validated', 'published', 'active', 'superseded')),
            record_json TEXT NOT NULL,
            record_sha256 TEXT NOT NULL,
            path TEXT NOT NULL,
            commit_sha TEXT,
            packets_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(activity_id, supplement_id, version)
        )
        """,
    ),
)

_OPEN = ("requested", "determining", "publishing")
_PACKET_KEY = __import__("re").compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


_GAP_TASK = """You are the Maestro milestone-gap Project Architect. A finding from milestone Quality Assurance or the milestone outcome review says the assembled milestone does not deliver what was confirmed. You decide where the correction belongs, inside the confirmed scope and direction. You are a new session for this finding, not the architecture loop and not the missing-specialist process. You cannot approve the milestone, dispatch code, change scope or start re-registration. Work only from this assignment, the files under input/ and the read-only source/ clone, which is the assembled milestone branch at {head}.

1. Read input/finding.json (the exact finding and its evidence), input/milestone.json (the milestone outcome and its packets with their state and permitted paths), input/packets.json, input/supplements.json (correction supplements that already exist), input/limits.json (remaining review allowances) and input/execution.json. Verify the finding against source/ yourself.
2. Choose exactly one determination. implementation_defect: the confirmed design and packets cover the behavior and the code is wrong; give the smallest correction for the Integration Manager in `minimum_correction`. in_scope_supplement: needed work is missing but is within the confirmed scope and direction; give the bounded correction in `supplement` (scope_explanation and packets). reregistration_required: the correction would change outcomes, dependencies, responsibilities or the architectural direction; list the affected packet keys in `affected_work` and recommend a work disposition in `disposition_recommendation` (continue_unaffected, finish_safe_work, stop_affected_or_all or finish_current_for_replanning).
3. Supplement rules: each packet has a unique lowercase-hyphen key that does not collide with an existing packet, a subject, a purpose, implementation_ownership (the source area or component that owns the change), permitted_paths that stay inside paths the milestone's confirmed packets already permit (no leading slash, no .., nothing broader than needed), dependencies naming existing or supplement packet keys (no cycles), completion_criteria that state the observable corrected behavior, and essential_failure_checks. Do not restate a confirmed packet or change an outcome.
4. {owner_line}
5. Always give a plain rationale and the affected packet keys or milestone in `affected_work`. result is completed.
Copy contract_version (1), assignment_id, run_id, session_id, project_id, activity_id, role, source_commit and decision_version exactly from assignment.json. Return only the structured response."""

_OWNER_LIMIT = "The milestone review allowance is exhausted. Set owner_recommendation to grant_one or remain_paused; it grants nothing."
_OWNER_NONE = "No allowance is exhausted, so owner_recommendation must be null."


class GapMixin:
    """Milestone-gap behavior of ``ExecutionService``."""

    # -------------------------------------------------------------- findings

    def prepare_record_finding(self, request: RequestLike) -> PreparedOperation:
        """Save one milestone finding and its gap assignment; the milestone Quality Assurance and outcome review producers call this same operation."""
        payload = dict(request.payload)
        if request.project_id is None or request.activity_id is None or request.question_id is not None:
            raise ValueError("execution.record_finding needs a project and the Execution activity")
        if set(payload) != {"milestone_key", "source", "subject", "explanation", "impact", "requested_correction", "evidence", "review_limit_exhausted"}:
            raise ValueError("execution.record_finding payload must be milestone_key, source, subject, explanation, impact, requested_correction, evidence and review_limit_exhausted")
        if payload["source"] not in ("quality_assurance", "outcome_review"):
            raise ValueError("source must be quality_assurance or outcome_review")
        for name in ("milestone_key", "subject", "explanation", "impact", "requested_correction"):
            if not isinstance(payload[name], str) or not payload[name].strip():
                raise ValueError(f"{name} must be nonempty text")
        if not isinstance(payload["evidence"], list) or not all(isinstance(e, str) and e for e in payload["evidence"]) or not payload["evidence"]:
            raise ValueError("evidence must be a nonempty list of text statements or locations")
        if not isinstance(payload["review_limit_exhausted"], bool):
            raise ValueError("review_limit_exhausted must be true or false")
        activity_id = request.activity_id
        project_id = request.project_id
        record = {k: payload[k] for k in ("milestone_key", "source", "subject", "explanation", "impact", "requested_correction", "evidence", "review_limit_exhausted")}

        def apply(transaction: Transaction, next_version: int) -> OperationResult:
            row = self._row(transaction, "SELECT * FROM service_executions WHERE activity_id = ? AND project_id = ?", (activity_id, project_id))
            if row is None or row["state"] not in ("running", "blocked", "paused"):
                raise RequestRejection(404, "execution_not_open", "no unfinished Execution activity matches", fields={"activity_id": activity_id})
            milestone = self._row(transaction, "SELECT * FROM service_execution_milestones WHERE activity_id = ? AND milestone_key = ?", (activity_id, record["milestone_key"]))
            if milestone is None:
                raise RequestRejection(409, "unknown_milestone", "the confirmed breakdown has no such milestone", fields={"milestone_key": record["milestone_key"]})
            digest = hashlib.sha256(canonical_json(record).encode()).hexdigest()
            duplicate = self._row(transaction, "SELECT finding_id FROM service_execution_findings WHERE activity_id = ? AND record_sha256 = ? AND state != 'closed'", (activity_id, digest))
            if duplicate is not None:
                return OperationResult(data={"activity_id": activity_id, "finding_id": duplicate["finding_id"], "duplicate": True}, status="accepted", project_id=project_id, activity_id=activity_id)
            finding_id, gap_key = self._route_finding(transaction, row, project_id, activity_id, record, digest)
            return OperationResult(data={"activity_id": activity_id, "finding_id": finding_id, "gap_assignment": gap_key, "duplicate": False}, status="accepted", project_id=project_id, activity_id=activity_id)

        return PreparedOperation(f"execution-finding-{request.request_id}", "execution.finding_recorded", {"activity_id": activity_id}, apply)

    def _route_finding(self, transaction: Transaction, row: Mapping[str, Any], project_id: str, activity_id: str, record: Mapping[str, Any], digest: str) -> tuple[str, str]:
        """Save a finding and its milestone-gap assignment in the caller's transaction (the recording operation and milestone verification share it)."""
        number = 1 + int(self._row(transaction, "SELECT COUNT(*) AS n FROM service_execution_findings WHERE activity_id = ?", (activity_id,))["n"])
        finding_id = f"finding-{number}"
        gap_key = f"gap-{finding_id}"
        config, note = self._gap_config(row)
        state = "requested" if config else "blocked_route"
        now = _now()
        transaction.execute("INSERT INTO service_execution_findings(activity_id, finding_id, milestone_key, source, subject, record_json, record_sha256, state, gap_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'routed', ?, ?)",
                            (activity_id, finding_id, record["milestone_key"], record["source"], record["subject"][:200], canonical_json(record), digest, gap_key, now))
        transaction.execute(
            "INSERT INTO service_execution_architect(activity_id, assignment_key, kind, packet_key, subject, trigger_json, state, version, config_json, pending_json, review_limit, note, created_at, updated_at) "
            "VALUES (?, ?, 'milestone_gap', NULL, ?, ?, ?, 1, ?, '{}', 0, ?, ?, ?)",
            (activity_id, gap_key, f"Milestone gap for {finding_id}: {record['subject'][:160]}", canonical_json({"finding_id": finding_id, "milestone_key": record["milestone_key"], "exhausted": record["review_limit_exhausted"]}),
             state, canonical_json(config or {}), note, now, now))
        self._say(transaction, project_id, activity_id, f"Milestone finding {finding_id} ({record['source'].replace('_', ' ')}) recorded for milestone {record['milestone_key']}: {record['subject'][:300]}. "
                  + (f"Milestone-gap assignment {gap_key} is queued for the Project Architect." if config else f"{note}."))
        return finding_id, gap_key

    def _finding(self, activity_id: str, finding_id: str) -> dict[str, Any]:
        found = self._read("SELECT * FROM service_execution_findings WHERE activity_id = ? AND finding_id = ?", (activity_id, finding_id))
        assert found is not None
        return found

    # ------------------------------------------------------------- advancing

    def _advance_gaps(self, row: Mapping[str, Any]) -> None:
        for arch in self._architects(row["activity_id"], "milestone_gap"):
            try:
                if arch["state"] in ("requested", "determining"):
                    self._support_step(row, arch, "gap_run", self._gap_start, self._gap_accept)
                elif arch["state"] == "publishing":
                    self._supplement_publish(row, arch)
            except (AgentRunError, DestinationError) as error:
                if isinstance(error, DestinationError) and (error.code == "github_unreachable" or (isinstance(error.fields.get("status"), int) and error.fields["status"] >= 500)):
                    continue
                self._support_block(row, arch, f"{getattr(error, 'code', type(error).__name__)}: {error}")

    def _gap_inputs(self, row: Mapping[str, Any], arch: Mapping[str, Any]) -> dict[str, bytes]:
        activity_id = row["activity_id"]
        trigger = json.loads(arch["trigger_json"])
        finding = self._finding(activity_id, trigger["finding_id"])
        milestone = self._milestones(activity_id)[trigger["milestone_key"]]
        packets = [p for p in self._packets(activity_id) if p["milestone_key"] == trigger["milestone_key"]]
        listing = [{"key": p["packet_key"], "subject": p["subject"], "state": p["state"], "dependencies": json.loads(p["dependency_keys_json"]),
                    **{k: v for k, v in json.loads(p["record_json"]).items() if k in {"purpose", "permitted_paths", "completion_criteria", "essential_failure_checks", "required_outputs"}}} for p in packets]
        supplements = [{"supplement_id": s["supplement_id"], "version": s["version"], "finding_id": s["finding_id"], "state": s["state"], "packets": json.loads(s["packets_json"])}
                       for s in self._rows("SELECT * FROM service_execution_supplements WHERE activity_id = ? ORDER BY supplement_id, version", (activity_id,))]
        return {
            "finding.json": _json({"finding_id": finding["finding_id"], **json.loads(finding["record_json"])}),
            "milestone.json": _json({"key": milestone["milestone_key"], "subject": milestone["subject"], "record": json.loads(milestone["record_json"]), "branch": milestone["branch"], "head_commit": milestone["head_commit"]}),
            "packets.json": _json(listing), "supplements.json": _json(supplements),
            "limits.json": _json({"milestone_review_allowance_exhausted": bool(trigger.get("exhausted")), "note": "the milestone review count is owned by milestone review and is not reset by a supplement"}),
            "execution.json": _json({"activity_id": activity_id, "repository": row["repository"], "confirmed_breakdown": {k: json.loads(row["confirmed_ref_json"])[k] for k in ("version", "commit", "manifest_path")}}),
        }

    def _gap_start(self, row: Mapping[str, Any], arch: dict[str, Any], recovery_note: str | None) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], arch["assignment_key"]
        route = self._support_route(arch, "architect")
        pending = json.loads(self._architect(activity_id, key)["pending_json"])
        trigger = json.loads(arch["trigger_json"])
        milestone = self._milestones(activity_id)[trigger["milestone_key"]]
        head = milestone["head_commit"] or row["source_commit"]
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        mirror = self._mirror(row["project_id"])
        destination.fetch_source(row["repository"], head, mirror)
        assignment_id = f"{activity_id}-{key}-architect"
        note = "" if not recovery_note else f"\nThe previous run's output was rejected: {recovery_note}. Fix exactly that."
        task = _GAP_TASK.format(head=head[:12], owner_line=_OWNER_LIMIT if trigger.get("exhausted") else _OWNER_NONE) + note
        inputs = self._gap_inputs(row, arch)

        def build(run_id: str) -> RunBuild:
            assignment = AgentAssignment(
                project_id=row["project_id"], activity_id=activity_id, assignment_id=assignment_id, run_id=run_id, parent_assignment_id=None, role="milestone_gap_architect",
                role_responsibilities=("Route one milestone finding to a defect correction, a bounded in-scope supplement or Owner disposition; never approve, dispatch or change scope.",),
                task=task, source_commit=head, decision_version=key,
                instructions={"session_id": run_id, "claude_tools": ["Read", "Glob", "Grep"], "task_kind": "milestone_gap", "gap": key},
                permitted_actions=("read_source",), writable_locations=("output", "scratch"), limits={"run_timeout_seconds": route["run_timeout_seconds"]},
                clarification_conditions=("Missing information changes the determination.",), response_schema=DETERMINATION_SCHEMA, contract="execution",
            )
            return RunBuild(assignment, mirror, inputs, None)

        self._launch(row, pending, "gap_run", assignment_id, route["tool"], route["model"], route["run_timeout_seconds"], recovery_note is not None, build, "milestone_gap_architect",
                     save=lambda _a, p: self._save_architect(activity_id, key, p))
        pending["architect"] = {"tool": route["tool"], "model": route["model"]}
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = 'determining', pending_json = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?", (canonical_json(pending), _now(), activity_id, key))
            self._say(tx, row["project_id"], activity_id, f"Milestone-gap assignment {key}: architect {route['tool']} {route['model']} ({route['slot']} route) started on the assembled milestone at {head[:12]}.")

    # ---------------------------------------------------------- validation

    def _validate_supplement(self, row: Mapping[str, Any], arch: Mapping[str, Any], supplement: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Deterministic checks; a message names exactly what to fix. Returns the normalized packet definitions."""
        trigger = json.loads(arch["trigger_json"])
        packets = {p["packet_key"]: p for p in self._packets(row["activity_id"])}
        confirmed = [p for p in packets.values() if p["milestone_key"] == trigger["milestone_key"]]
        allowed = sorted({path.strip("/") for p in confirmed for path in json.loads(p["record_json"]).get("permitted_paths", [])})
        if not str(supplement["scope_explanation"]).strip():
            raise ValueError("scope_explanation must say why the work stays within confirmed scope and direction")
        keys = [p["key"] for p in supplement["packets"]]
        if len(set(keys)) != len(keys):
            raise ValueError("a packet key is repeated in the supplement")
        normalized: list[dict[str, Any]] = []
        for definition in supplement["packets"]:
            key = definition["key"]
            if not _PACKET_KEY.match(key):
                raise ValueError(f"packet key {key} must be lowercase words joined by hyphens")
            if key in packets:
                raise ValueError(f"packet key {key} collides with an existing packet; choose a new key")
            for field in ("subject", "purpose", "implementation_ownership"):
                if not str(definition[field]).strip():
                    raise ValueError(f"packet {key} needs a {field}")
            for field in ("permitted_paths", "completion_criteria"):
                if not definition[field] or not all(isinstance(x, str) and x.strip() for x in definition[field]):
                    raise ValueError(f"packet {key} needs a nonempty list of {field.replace('_', ' ')}")
            for path in definition["permitted_paths"]:
                clean = path.strip("/")
                if path.startswith("/") or ".." in path.split("/") or clean in ("", ".", "*") or "*" in clean:
                    raise ValueError(f"packet {key} path {path!r} is not a bounded repository-relative path")
                if not any(clean == a or clean.startswith(a + "/") for a in allowed):
                    raise ValueError(f"packet {key} path {path} is outside the paths the milestone's confirmed packets permit ({', '.join(allowed)}); a wider path is a scope change that needs re-registration")
            for dependency in definition["dependencies"]:
                if dependency not in packets and dependency not in keys:
                    raise ValueError(f"packet {key} depends on {dependency}, which is neither an existing packet nor in this supplement")
            normalized.append({k: definition[k] for k in ("key", "subject", "purpose", "implementation_ownership", "permitted_paths", "dependencies", "completion_criteria", "essential_failure_checks")})
        graph = {d["key"]: [x for x in d["dependencies"] if x in keys] for d in normalized}
        seen: set[str] = set()

        def visit(node: str, path: tuple[str, ...]) -> None:
            if node in path:
                raise ValueError("the supplement's dependencies contain a cycle: " + " -> ".join((*path, node)))
            if node in seen:
                return
            for nxt in graph[node]:
                visit(nxt, (*path, node))
            seen.add(node)

        for node in graph:
            visit(node, ())
        return normalized

    def _defect_correction(self, tx: Transaction, row: Mapping[str, Any], trigger: Mapping[str, Any], result: Mapping[str, Any]) -> str:
        """An implementation defect becomes one pending correction packet in the milestone; normal review and the integration queue carry it."""
        activity_id = row["activity_id"]
        siblings = [p for p in self._packets(activity_id) if p["milestone_key"] == trigger["milestone_key"]]
        base = json.loads(siblings[0]["record_json"]) if siblings else {}
        paths = sorted({path for p in siblings for path in json.loads(p["record_json"]).get("permitted_paths", [])})
        finding = json.loads(self._finding(activity_id, trigger["finding_id"])["record_json"])
        key = f"correct-{trigger['finding_id']}"
        correction = str(result["minimum_correction"] or finding["requested_correction"])
        record = {
            "id": key, "subject": f"Correct: {finding['subject']}"[:200], "purpose": correction, "permitted_paths": paths, "dependencies": [],
            "completion_criteria": [correction], "essential_failure_checks": [finding["requested_correction"]], "required_outputs": [], "parallel_opportunities": [],
            "shared_code_constraints": base.get("shared_code_constraints", []), "execution_requirements": base.get("execution_requirements", {}),
            "starting_context": {k: v for k, v in (base.get("starting_context") or {}).items() if k == "specialist_role_ref"},
            "defect_ref": {"finding_id": trigger["finding_id"], "milestone_key": trigger["milestone_key"]},
        }
        limit = json.loads(row["config_json"])["reviews"]["packet"]["maximum_completed_rounds"]
        added = tx.execute(
            "INSERT OR IGNORE INTO service_execution_packets(activity_id, packet_key, subject, record_json, record_sha256, milestone_key, dependency_keys_json, state, round_limit, updated_at) VALUES (?, ?, ?, ?, ?, ?, '[]', 'pending', ?, ?)",
            (activity_id, key, record["subject"], canonical_json(record), hashlib.sha256(canonical_json(record).encode()).hexdigest(), trigger["milestone_key"], limit, _now()),
        ).rowcount
        if added != 1:
            raise AgentRunError("stale_finding", f"the correction packet {key} already exists")
        return key

    def _milestone_review_decision(self, tx: Transaction, request: RequestLike, row: Mapping[str, Any], payload: Mapping[str, Any], next_version: int) -> OperationResult:
        """The Owner's typed choice when a milestone review allowance is exhausted; it is saved for milestone review, which owns the count, and approves nothing."""
        activity_id = row["activity_id"]
        arch = self._row(tx, "SELECT * FROM service_execution_architect WHERE activity_id = ? AND assignment_key = ? AND kind = 'milestone_gap' AND result_json IS NOT NULL", (activity_id, payload["assignment_id"]))
        trigger = json.loads(arch["trigger_json"]) if arch is not None else {}
        pending = json.loads(arch["pending_json"] or "{}") if arch is not None else {}
        if arch is None or not trigger.get("exhausted") or json.loads(arch["result_json"])["owner_recommendation"] not in ("grant_one", "remain_paused") or "owner_decision" in pending:
            raise RequestRejection(409, "no_decision_pending", "no milestone review-limit decision is pending for that gap assignment")
        pending["owner_decision"] = {"choice": payload["choice"], "request_id": request.request_id, "decided_at": _now()}
        tx.execute("UPDATE service_execution_architect SET pending_json = ?, updated_at = ? WHERE activity_id = ? AND assignment_key = ?", (canonical_json(pending), _now(), activity_id, arch["assignment_key"]))
        text = (f"Owner granted one extra milestone review attempt for milestone {trigger['milestone_key']} (finding {trigger['finding_id']}); the grant approves nothing and does not reset the count." if payload["choice"] == "grant_one"
                else f"Owner chose to keep milestone {trigger['milestone_key']} review paused for finding {trigger['finding_id']}; nothing was approved and no count changed.")
        self._event(tx, activity_id, "milestone_review_decision", None, text[:400])
        self._activity(tx, activity_id, "running", text, version=next_version)
        self._say(tx, row["project_id"], activity_id, text)
        return OperationResult(data={"activity_id": activity_id, "decision": payload["choice"], "milestone": trigger["milestone_key"], "message": text}, status="accepted", project_id=row["project_id"], activity_id=activity_id)

    def _gap_accept(self, row: Mapping[str, Any], arch: dict[str, Any], pending: dict[str, Any], current: Mapping[str, str]) -> None:
        assert self.runs is not None
        activity_id, key = row["activity_id"], arch["assignment_key"]
        response = self.runs.response(current["run_id"]) or {}
        trigger = json.loads(arch["trigger_json"])
        if response.get("result") != "completed":
            self._support_block(row, arch, "the architect asked a question; a milestone-gap determination needs more information than this assignment can ask for")
            return
        known = {p["packet_key"] for p in self._packets(activity_id)} | set(self._milestones(activity_id))
        kind = response["determination"]
        problem = None
        normalized: list[dict[str, Any]] = []
        if trigger.get("exhausted") and response["owner_recommendation"] not in ("grant_one", "remain_paused"):
            problem = "an exhausted milestone review allowance needs owner_recommendation grant_one or remain_paused"
        elif not trigger.get("exhausted") and response["owner_recommendation"] is not None:
            problem = "no allowance is exhausted, so owner_recommendation must be null"
        elif any(k not in known for k in response["affected_work"]):
            problem = "affected_work names something that is not a packet or milestone of this Execution"
        elif kind == "reregistration_required" and not response["affected_work"]:
            problem = "a re-registration result lists the affected packets"
        elif kind == "in_scope_supplement":
            try:
                normalized = self._validate_supplement(row, arch, response["supplement"])
            except ValueError as error:
                problem = str(error)
        if problem:
            self._reject_support_result(row, arch, pending, current, "gap_run", problem, self._gap_start)
            return
        pending.pop("gap_run", None)
        pending.pop("last_recovery_detail", None)
        result = {k: response[k] for k in ("determination", "rationale", "interpretation", "minimum_correction", "affected_work", "owner_recommendation", "disposition_recommendation")}
        result.update({"run_id": current["run_id"], "supplement": None if kind != "in_scope_supplement" else {"scope_explanation": response["supplement"]["scope_explanation"], "packets": normalized}})
        if kind == "in_scope_supplement":
            state = "publishing"
        elif kind == "reregistration_required":
            state = "awaiting_disposition"
        else:
            state = "decided"
        with self.database.transaction() as tx:
            tx.execute("UPDATE service_execution_architect SET state = ?, result_json = ?, pending_json = ?, note = NULL, updated_at = ? WHERE activity_id = ? AND assignment_key = ?",
                       (state, canonical_json(result), canonical_json(pending), _now(), activity_id, key))
            if kind == "implementation_defect":
                correction_key = self._defect_correction(tx, row, trigger, result)
                tx.execute("UPDATE service_execution_findings SET state = 'defect_routed' WHERE activity_id = ? AND finding_id = ?", (activity_id, trigger["finding_id"]))
                self._event(tx, activity_id, "gap_defect", None, f"{key}: implementation defect for milestone {trigger['milestone_key']}, correction packet {correction_key} is pending; minimum correction: {str(result['minimum_correction'])[:300]}")
            if kind == "reregistration_required":
                tx.execute("UPDATE service_execution_findings SET state = 'reregistration_required' WHERE activity_id = ? AND finding_id = ?", (activity_id, trigger["finding_id"]))
            summary = (f"implementation defect; correction packet {correction_key} is pending and follows normal review and integration: {result['minimum_correction']}" if kind == "implementation_defect"
                       else f"a bounded supplement of {len(normalized)} packet(s) is validated and published next" if kind == "in_scope_supplement"
                       else f"re-registration is required for {', '.join(result['affected_work'])}; recommended disposition {result['disposition_recommendation']}")
            self._say(tx, row["project_id"], activity_id, f"Milestone-gap determination {key} ({kind}) for {trigger['finding_id']}: {str(result['rationale'])[:300]}. {summary[:400]}"
                      + (f" Architect recommendation to the Owner: {result['owner_recommendation']}." if result["owner_recommendation"] else ""))

    # ---------------------------------------------------------- publication

    def _supplement_files(self, row: Mapping[str, Any], arch: Mapping[str, Any], result: Mapping[str, Any], supplement_id: str, version: int) -> tuple[str, dict[str, Any]]:
        trigger = json.loads(arch["trigger_json"])
        pending = json.loads(arch["pending_json"] or "{}")
        confirmed = json.loads(row["confirmed_ref_json"])
        record = {
            "schema_version": 1, "project_id": row["project_id"], "activity_id": row["activity_id"], "supplement_id": supplement_id, "version": version,
            "registration": {"activity_id": row["registration_activity_id"]},
            "confirmed_breakdown": {k: confirmed[k] for k in ("version", "commit", "manifest_path", "manifest_sha256") if k in confirmed},
            "milestone_key": trigger["milestone_key"], "finding": {"finding_id": trigger["finding_id"], **{k: v for k, v in json.loads(self._finding(row["activity_id"], trigger["finding_id"])["record_json"]).items() if k in {"source", "subject", "requested_correction"}}},
            "scope_explanation": result["supplement"]["scope_explanation"], "packets": result["supplement"]["packets"],
            "dependency_changes": [{"packet": p["key"], "depends_on": p["dependencies"]} for p in result["supplement"]["packets"]],
            "architect": {"assignment": f"{row['activity_id']}-{arch['assignment_key']}-architect", "run_id": result["run_id"], **(pending.get("architect") or {})},
            "validation": {"result": "valid", "checks": ["unique packet keys", "bounded paths inside the milestone's confirmed permitted paths", "dependencies exist without cycles", "finding is open and unchanged"]},
        }
        path = f".maestro/execution/{row['activity_id']}/supplements/{supplement_id}/versions/{version}/supplement.json"
        return path, record

    def _supplement_publish(self, row: Mapping[str, Any], arch: dict[str, Any]) -> None:
        activity_id, key = row["activity_id"], arch["assignment_key"]
        trigger = json.loads(arch["trigger_json"])
        result = json.loads(arch["result_json"])
        finding = self._finding(activity_id, trigger["finding_id"])
        if finding["state"] not in ("routed",):
            self._support_block(row, arch, f"the finding {trigger['finding_id']} is {finding['state']}, so this supplement is stale")
            return
        supplement_id = f"supplement-{trigger['finding_id'].split('-')[-1]}"
        version = 1
        path, record = self._supplement_files(row, arch, result, supplement_id, version)
        data = encode(record)
        digest = hashlib.sha256(data).hexdigest()
        destination = self._destination(self.profiles[json.loads(row["profile_json"])["profile"]])
        branch = self._publication_branch(row)
        operation_id = f"{activity_id}-{supplement_id}-v{version}-publish"
        if self._read("SELECT 1 AS n FROM service_execution_journal WHERE operation_id = ?", (operation_id,)) is None:
            self._journal_begin(row, operation_id, supplement_id, "supplement_publish", branch, digest, destination.head(row["repository"], branch))
        try:
            commit = destination.publish(row["repository"], branch, {path: data}, f"Execution {activity_id}: correction supplement {supplement_id} version {version}")
        except DestinationError as error:
            if error.code in {"github_unreachable", "publication_failed", "branch_unverifiable"}:
                raise
            self._journal_end(operation_id, "failed", None, f"{error.code}: {error}"[:300])
            raise
        destination.verify_files(row["repository"], commit, {path: data})
        if hashlib.sha256(destination.read_file(row["repository"], commit, path) or b"").hexdigest() != digest:
            raise DestinationError("verification_failed", "the published supplement bytes do not match the journaled hash")
        packets_by_key = {p["packet_key"]: p for p in self._packets(activity_id)}
        milestone_packets = [p for p in packets_by_key.values() if p["milestone_key"] == trigger["milestone_key"]]
        limit = json.loads(row["config_json"])["reviews"]["packet"]["maximum_completed_rounds"]
        now = _now()
        with self.database.transaction() as tx:
            current = self._row(tx, "SELECT state FROM service_execution_findings WHERE activity_id = ? AND finding_id = ?", (activity_id, trigger["finding_id"]))
            if current is None or current["state"] != "routed":
                raise AgentRunError("stale_finding", f"the finding {trigger['finding_id']} changed before activation")
            tx.execute("UPDATE service_execution_journal SET state = 'verified', remote_after = ? WHERE operation_id = ?", (commit, operation_id))
            added = tx.execute(
                "INSERT OR IGNORE INTO service_execution_supplements(activity_id, supplement_id, version, finding_id, milestone_key, state, record_json, record_sha256, path, commit_sha, packets_json, created_at) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)",
                (activity_id, supplement_id, version, trigger["finding_id"], trigger["milestone_key"], canonical_json(record), digest, path, commit, _dump([p["key"] for p in record["packets"]]), now),
            ).rowcount
            if added != 1:
                raise AgentRunError("stale_finding", f"the supplement {supplement_id} version {version} already exists")
            for definition in record["packets"]:
                sibling = next((p for p in milestone_packets if any(a.strip("/") == b.strip("/") or a.strip("/").startswith(b.strip("/") + "/") for a in definition["permitted_paths"] for b in json.loads(p["record_json"]).get("permitted_paths", []))), None)
                base = json.loads(sibling["record_json"]) if sibling is not None else {}
                packet_record = {
                    "id": definition["key"], "subject": definition["subject"], "purpose": definition["purpose"], "implementation_ownership": definition["implementation_ownership"], "permitted_paths": definition["permitted_paths"], "dependencies": definition["dependencies"],
                    "completion_criteria": definition["completion_criteria"], "essential_failure_checks": definition["essential_failure_checks"], "required_outputs": [], "parallel_opportunities": [],
                    "shared_code_constraints": base.get("shared_code_constraints", []), "execution_requirements": base.get("execution_requirements", {}),
                    "starting_context": {k: v for k, v in (base.get("starting_context") or {}).items() if k == "specialist_role_ref"},
                    "supplement_ref": {"supplement_id": supplement_id, "version": version, "path": path, "sha256": digest, "commit": commit, "finding_id": trigger["finding_id"], "milestone_key": trigger["milestone_key"]},
                }
                added = tx.execute(
                    "INSERT OR IGNORE INTO service_execution_packets(activity_id, packet_key, subject, record_json, record_sha256, milestone_key, dependency_keys_json, state, round_limit, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)",
                    (activity_id, definition["key"], definition["subject"], canonical_json(packet_record), hashlib.sha256(canonical_json(packet_record).encode()).hexdigest(), trigger["milestone_key"], _dump(definition["dependencies"]), limit, now),
                ).rowcount
                if added != 1:
                    raise AgentRunError("stale_finding", f"the packet {definition['key']} was created by another supplement before this one activated")
            tx.execute("UPDATE service_execution_findings SET state = 'supplement_active' WHERE activity_id = ? AND finding_id = ?", (activity_id, trigger["finding_id"]))
            tx.execute("UPDATE service_execution_architect SET state = 'active', note = NULL, updated_at = ? WHERE activity_id = ? AND assignment_key = ? AND state = 'publishing'", (now, activity_id, key))
            self._event(tx, activity_id, "supplement_active", None, f"{supplement_id}: {len(record['packets'])} correction packet(s) for milestone {trigger['milestone_key']} ({', '.join(p['key'] for p in record['packets'])}) are pending; schedule them")
            self._say(tx, row["project_id"], activity_id,
                      f"Correction supplement {supplement_id} version {version} is active: published at {path} in {commit[:12]} (SHA-256 {digest[:12]}, bytes verified on the remote) for finding {trigger['finding_id']}. "
                      f"Its {len(record['packets'])} packet(s) are released to the Development Manager as pending work; the confirmed breakdown and the milestone review count are unchanged.")
            self._emit(tx, row["project_id"], activity_id, "execution.supplement_active", {"supplement": supplement_id, "packets": [p["key"] for p in record["packets"]], "commit": commit})

    # ----------------------------------------------------------------- view

    def gap_view(self, activity_id: str) -> list[dict[str, Any]]:
        views = []
        for arch in self._architects(activity_id, "milestone_gap"):
            pending = json.loads(arch["pending_json"] or "{}")
            trigger = json.loads(arch["trigger_json"])
            result = json.loads(arch["result_json"]) if arch["result_json"] else None
            finding = self._read("SELECT * FROM service_execution_findings WHERE activity_id = ? AND finding_id = ?", (activity_id, trigger["finding_id"]))
            supplements = self._rows("SELECT supplement_id, version, state, path, record_sha256, commit_sha, packets_json FROM service_execution_supplements WHERE activity_id = ? AND finding_id = ?", (activity_id, trigger["finding_id"]))
            views.append({
                "gap_id": arch["assignment_key"], "finding_id": trigger["finding_id"], "milestone": trigger["milestone_key"], "state": arch["state"], "note": arch["note"],
                "finding": None if finding is None else {"state": finding["state"], "source": finding["source"], "subject": finding["subject"]},
                "architect": pending.get("architect"), "determination": None if result is None else result["determination"],
                "rationale": None if result is None else result["rationale"], "recommendation": None if result is None else result["owner_recommendation"],
                "supplements": [{"supplement_id": s["supplement_id"], "version": s["version"], "state": s["state"], "path": s["path"], "sha256": s["record_sha256"], "commit": s["commit_sha"], "packets": json.loads(s["packets_json"])} for s in supplements],
            })
        return views
