"""Architecture breakdown records: prepared-output validation and versioned set building.

The architect supplies judgments (milestones, packets, dependencies, parallel opportunities, Quality
Assurance plans); the service checks them deterministically, assigns identities, versions and hashes,
and renders the records defined by ``docs/schemas/architecture-breakdown.schema.json``. A later output
set retains an unchanged record as a carried-forward reference and rewrites only changed records.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Mapping, Sequence

from maestro.foundation import canonical_json

from .architecture_records import ROOT, FoundationError, encode, sha256

BREAKDOWN_SCHEMA = "architecture_breakdown_v1"
CAPABILITIES = ("code_edit", "local_command", "repository_search", "image_inspection", "approved_network")
LOCATIONS = ("local_ai_box", "cloud")
MAX_PACKET_PATHS = 12
MAX_SCOPE_ITEMS = 8
_SAFE = re.compile(r"(?!/)(?!.*(?:^|/)\.\.?(?:/|$))(?!.*\\)[^\s].*\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
OUTPUT_RULES = {"exact": ["breakdown.json"], "patterns": []}
DIRS = {"milestone": "development-milestones", "packet": "work-packets", "qa_plan": "qa-plans"}
TYPES = {"milestone": "development_milestone", "packet": "work_packet", "qa_plan": "qa_plan"}
PREFIX = {"milestone": "milestone", "packet": "packet", "qa_plan": "qa-plan"}


class QaBindingError(FoundationError):
    """A plan selected setup the operator has not provisioned; the Owner must be told what to provide."""


# ----------------------------------------------------------------------------- QA binding catalog

def qa_catalog(binding: object) -> tuple[dict[str, Any], str | None]:
    """Validate an operator project binding; return its non-secret catalog and the hash of that snapshot (None when none is configured)."""
    empty = {"project_binding_hash": None, "environments": {}, "secrets": {}, "network_dependencies": {}}
    if binding is None:
        return empty, None
    if not isinstance(binding, Mapping):
        raise FoundationError("the project's QA binding must be a table")
    environments, secrets, network = binding.get("environments", {}), binding.get("secrets", {}), binding.get("network_dependencies", {})
    if not all(isinstance(t, Mapping) for t in (environments, secrets, network)):
        raise FoundationError("the project's QA binding tables must be tables")
    catalog: dict[str, Any] = {"environments": {}, "secrets": {}, "network_dependencies": {}}
    for name, env in environments.items():
        if not isinstance(env, Mapping) or env.get("classification") != "test":
            raise FoundationError(f"QA environment {name} must be classified test")
        variables = env.get("variables", {})
        if not isinstance(variables, Mapping) or not all(isinstance(k, str) and isinstance(v, str) for k, v in variables.items()):
            raise FoundationError(f"QA environment {name} variables must be a text map")
        catalog["environments"][name] = {"classification": "test", "variables": dict(variables), "secret_names": sorted(env.get("secret_names", [])),
                                         "network_dependency_names": sorted(env.get("network_dependency_names", []))}
    for name, secret in secrets.items():
        if not isinstance(secret, Mapping) or secret.get("classification") != "test" or not secret.get("credential_ref") or not secret.get("environment_variable"):
            raise FoundationError(f"QA secret {name} must be classified test with a credential_ref and environment_variable")
        catalog["secrets"][name] = {"classification": "test", "environment_variable": secret["environment_variable"]}
    for name, dep in network.items():
        if not isinstance(dep, Mapping) or not dep.get("host") or not dep.get("protocol") or not isinstance(dep.get("ports"), list):
            raise FoundationError(f"QA network dependency {name} needs host, protocol and ports")
        catalog["network_dependencies"][name] = {"host": dep["host"], "protocol": dep["protocol"], "ports": list(dep["ports"])}
    for name, env in catalog["environments"].items():
        for kind, table, field in (("secret", "secrets", "secret_names"), ("network dependency", "network_dependencies", "network_dependency_names")):
            unknown = [n for n in env[field] if n not in catalog[table]]
            if unknown:
                raise FoundationError(f"QA environment {name} names {kind} {', '.join(unknown)}, which the binding does not define")
    digest = sha256(canonical_json(catalog).encode("utf-8"))
    return {**catalog, "project_binding_hash": digest}, digest


# ----------------------------------------------------------------------------- prepared-output validation

def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FoundationError(f"{name} must be nonempty text")
    return value.strip()


def _texts(value: object, name: str, *, minimum: int = 0, limit: int | None = None) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise FoundationError(f"{name} must be a list of nonempty text")
    if len(value) < minimum:
        raise FoundationError(f"{name} needs at least {minimum} entr{'y' if minimum == 1 else 'ies'}")
    if limit is not None and len(value) > limit:
        raise FoundationError(f"{name} has {len(value)} entries; the limit is {limit}. Split the work into smaller bounded packets")
    return [v.strip() for v in value]


def _keys(value: object, name: str, known: set[str], *, own: str | None = None) -> list[str]:
    items = _texts(value, name)
    for item in items:
        if item not in known:
            raise FoundationError(f"{name} names {item}, which is not a local_key in this breakdown")
        if item == own:
            raise FoundationError(f"{name} names its own record {item}")
    if len(set(items)) != len(items):
        raise FoundationError(f"{name} lists a key twice")
    return items


def _exact(item: object, fields: set[str], name: str) -> Mapping[str, Any]:
    if not isinstance(item, Mapping) or set(item) != fields:
        raise FoundationError(f"{name} needs exactly: {', '.join(sorted(fields))}")
    return item


def _criteria(value: object, name: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise FoundationError(f"{name} must be a nonempty list")
    return [{k: _text(_exact(c, {"subject", "expected_result", "pass_boundary", "verification"}, f"{name} entry")[k], f"{name}.{k}") for k in ("subject", "expected_result", "pass_boundary", "verification")} for c in value]


def _safe_path(value: object, name: str) -> str:
    path = _text(value, name)
    if not _SAFE.fullmatch(path):
        raise FoundationError(f"{name} {path!r} must be a relative repository path without .. or backslashes")
    return path.strip("/")


def _covers(paths: Sequence[str], target: str) -> bool:
    return any(target == p or target.startswith(p.rstrip("/") + "/") for p in paths)


def _overlap(a: str, b: str) -> bool:
    a, b = a.rstrip("/"), b.rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def _cycle(edges: Mapping[str, Sequence[str]], label: str) -> None:
    state: dict[str, int] = {}

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 2:
            return
        if state.get(node) == 1:
            raise FoundationError(f"{label} dependencies form a cycle: {' -> '.join(trail[trail.index(node):] + [node])}")
        state[node] = 1
        for nxt in edges.get(node, ()):
            visit(nxt, trail + [node])
        state[node] = 2

    for key in edges:
        visit(key, [])


def _reach(edges: Mapping[str, Sequence[str]], start: str) -> set[str]:
    seen: set[str] = set()
    stack = list(edges.get(start, ()))
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(edges.get(node, ()))
    return seen


def validate_breakdown(
    document: object, *, outcome_ids: set[str], required_outcomes: set[str], finding_ids: set[str], specialist_keys: set[str],
    catalog: Mapping[str, Any], source_sha: Callable[[str], str | None],
) -> dict[str, Any]:
    """Deterministic checks of required fields, identities, dependencies, paths, bounds and QA selections; message names the rule and record."""
    if not isinstance(document, Mapping) or set(document) != {"schema", "summary", "decisions", "milestones", "packets"} or document["schema"] != BREAKDOWN_SCHEMA:
        raise FoundationError(f"breakdown.json must contain exactly schema ({BREAKDOWN_SCHEMA}), summary, decisions, milestones and packets")
    _text(document["summary"], "breakdown.summary")
    raw_milestones, raw_packets = document["milestones"], document["packets"]
    if not isinstance(raw_milestones, list) or not raw_milestones or not isinstance(raw_packets, list) or not raw_packets:
        raise FoundationError("breakdown needs at least one milestone and one packet")
    packet_keys = [str(p.get("local_key")) if isinstance(p, Mapping) else "" for p in raw_packets]
    milestone_keys = [str(m.get("local_key")) if isinstance(m, Mapping) else "" for m in raw_milestones]
    for label, keys in (("milestone", milestone_keys), ("packet", packet_keys)):
        if any(not k.strip() for k in keys) or len(set(keys)) != len(keys):
            raise FoundationError(f"every {label} needs a unique nonempty local_key")
    if set(milestone_keys) & set(packet_keys):
        raise FoundationError("milestone and packet local_keys must be distinct")
    pkeys, mkeys = set(packet_keys), set(milestone_keys)

    packets: list[dict[str, Any]] = []
    for raw in raw_packets:
        key = raw["local_key"]
        name = f"packet {key}"
        fields = {"local_key", "subject", "purpose", "milestone_key", "outcome_ids", "included_scope", "exclusions", "permitted_paths", "specialist_key", "finding_ids",
                  "dependency_keys", "shared_code_constraints", "parallel_with_keys", "execution_requirements", "completion_criteria", "verification", "essential_failure_checks", "required_outputs"}
        raw = _exact(raw, fields, name)
        if raw["milestone_key"] not in mkeys:
            raise FoundationError(f"{name} milestone_key {raw['milestone_key']!r} is not a milestone local_key")
        ids = _texts(raw["outcome_ids"], f"{name} outcome_ids", minimum=1)
        bad = [i for i in ids if i not in outcome_ids]
        if bad:
            raise FoundationError(f"{name} outcome_ids names {', '.join(bad)}, which are not confirmed outcome record ids")
        paths = [_safe_path(p, f"{name} permitted_paths") for p in raw["permitted_paths"]] if isinstance(raw["permitted_paths"], list) and raw["permitted_paths"] else _fail(f"{name} permitted_paths must be a nonempty list")
        if len(paths) > MAX_PACKET_PATHS:
            raise FoundationError(f"{name} permits {len(paths)} paths; the limit is {MAX_PACKET_PATHS}. Split it into smaller bounded packets")
        if raw["specialist_key"] not in specialist_keys:
            raise FoundationError(f"{name} specialist_key {raw['specialist_key']!r} is not a specialist local_key from the project structure ({', '.join(sorted(specialist_keys))})")
        found = _texts(raw["finding_ids"], f"{name} finding_ids")
        unknown = [f for f in found if f not in finding_ids]
        if unknown:
            raise FoundationError(f"{name} finding_ids names {', '.join(unknown)}, which are not saved findings ({', '.join(sorted(finding_ids))})")
        execution = _exact(raw["execution_requirements"], {"required_capabilities", "allowed_locations", "minimum_context_tokens"}, f"{name} execution_requirements")
        capabilities, locations = _texts(execution["required_capabilities"], f"{name} required_capabilities"), _texts(execution["allowed_locations"], f"{name} allowed_locations", minimum=1)
        if any(c not in CAPABILITIES for c in capabilities) or len(set(capabilities)) != len(capabilities):
            raise FoundationError(f"{name} required_capabilities must be distinct values of: {', '.join(CAPABILITIES)}")
        if any(l not in LOCATIONS for l in locations) or len(set(locations)) != len(locations):
            raise FoundationError(f"{name} allowed_locations must be distinct values of: {', '.join(LOCATIONS)}")
        tokens = execution["minimum_context_tokens"]
        if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 1:
            raise FoundationError(f"{name} minimum_context_tokens must be a positive integer")
        outputs = []
        if not isinstance(raw["required_outputs"], list) or not raw["required_outputs"]:
            raise FoundationError(f"{name} required_outputs must be a nonempty list")
        for out in raw["required_outputs"]:
            out = _exact(out, {"subject", "path", "format", "schema_ref"}, f"{name} required_outputs entry")
            path = _safe_path(out["path"], f"{name} required_outputs.path")
            if not _covers(paths, path):
                raise FoundationError(f"{name} required output {path} is outside its permitted_paths")
            schema_ref = out["schema_ref"]
            if schema_ref is not None:
                schema_ref = _text(schema_ref, f"{name} required_outputs.schema_ref")
            outputs.append({"subject": _text(out["subject"], f"{name} required_outputs.subject"), "path": path, "format": _text(out["format"], f"{name} required_outputs.format"), "schema_ref": schema_ref})
        packets.append({
            "local_key": key, "subject": _text(raw["subject"], f"{name} subject"), "purpose": _text(raw["purpose"], f"{name} purpose"), "milestone_key": raw["milestone_key"],
            "outcome_ids": ids, "included_scope": _texts(raw["included_scope"], f"{name} included_scope", minimum=1, limit=MAX_SCOPE_ITEMS),
            "exclusions": _texts(raw["exclusions"], f"{name} exclusions"), "permitted_paths": paths, "specialist_key": raw["specialist_key"], "finding_ids": found,
            "dependency_keys": _keys(raw["dependency_keys"], f"{name} dependency_keys", pkeys, own=key), "shared_code_constraints": _texts(raw["shared_code_constraints"], f"{name} shared_code_constraints"),
            "parallel_with_keys": _keys(raw["parallel_with_keys"], f"{name} parallel_with_keys", pkeys, own=key),
            "execution_requirements": {"required_capabilities": capabilities, "allowed_locations": locations, "minimum_context_tokens": tokens},
            "completion_criteria": _criteria(raw["completion_criteria"], f"{name} completion_criteria"),
            "verification": _texts(raw["verification"], f"{name} verification", minimum=1),
            "essential_failure_checks": _texts(raw["essential_failure_checks"], f"{name} essential_failure_checks", minimum=1), "required_outputs": outputs,
        })
    by_key = {p["local_key"]: p for p in packets}
    pdeps = {p["local_key"]: p["dependency_keys"] for p in packets}
    _cycle(pdeps, "packet")
    for p in packets:
        related = _reach(pdeps, p["local_key"])
        for other in p["parallel_with_keys"]:
            if other in related or p["local_key"] in _reach(pdeps, other):
                raise FoundationError(f"packet {p['local_key']} is listed as parallel with {other}, but one depends on the other")
            shared = [(a, b) for a in p["permitted_paths"] for b in by_key[other]["permitted_paths"] if _overlap(a, b)]
            if shared and not (p["shared_code_constraints"] and by_key[other]["shared_code_constraints"]):
                raise FoundationError(f"packets {p['local_key']} and {other} are parallel but both permit {shared[0][0]}; state the shared-code boundary in shared_code_constraints of both or make one depend on the other")

    milestones: list[dict[str, Any]] = []
    for raw in raw_milestones:
        key = raw["local_key"]
        name = f"milestone {key}"
        raw = _exact(raw, {"local_key", "subject", "outcome", "outcome_ids", "included_scope", "exclusions", "packet_keys", "dependency_keys", "integration_points", "completion_criteria", "qa_plan"}, name)
        ids = _texts(raw["outcome_ids"], f"{name} outcome_ids", minimum=1)
        bad = [i for i in ids if i not in outcome_ids]
        if bad:
            raise FoundationError(f"{name} outcome_ids names {', '.join(bad)}, which are not confirmed outcome record ids")
        members = _keys(raw["packet_keys"], f"{name} packet_keys", pkeys)
        if not members:
            raise FoundationError(f"{name} needs at least one packet")
        actual = sorted(p["local_key"] for p in packets if p["milestone_key"] == key)
        if sorted(members) != actual:
            raise FoundationError(f"{name} packet_keys {sorted(members)} must equal the packets that name it as milestone_key {actual}")
        for p in packets:
            if p["milestone_key"] == key and not set(p["outcome_ids"]) <= set(ids):
                raise FoundationError(f"packet {p['local_key']} serves outcomes its milestone {key} does not list")
        plan = _qa_plan(raw["qa_plan"], f"{name} qa_plan", catalog, by_key, set(members), source_sha)
        milestones.append({
            "local_key": key, "subject": _text(raw["subject"], f"{name} subject"), "outcome": _text(raw["outcome"], f"{name} outcome"), "outcome_ids": ids,
            "included_scope": _texts(raw["included_scope"], f"{name} included_scope", minimum=1), "exclusions": _texts(raw["exclusions"], f"{name} exclusions"),
            "packet_keys": members, "dependency_keys": _keys(raw["dependency_keys"], f"{name} dependency_keys", mkeys, own=key),
            "integration_points": _texts(raw["integration_points"], f"{name} integration_points"), "completion_criteria": _criteria(raw["completion_criteria"], f"{name} completion_criteria"),
            "qa_plan": plan,
        })
    _cycle({m["local_key"]: m["dependency_keys"] for m in milestones}, "milestone")
    covered_by_milestone = {i for m in milestones for i in m["outcome_ids"]}
    covered_by_packet = {i for p in packets for i in p["outcome_ids"]}
    for label, covered in (("development milestone", covered_by_milestone), ("work packet", covered_by_packet)):
        missing = sorted(required_outcomes - covered)
        if missing:
            raise FoundationError(f"no {label} covers these confirmed milestone outcomes: {', '.join(missing)}")
    for m in milestones:
        for dep in m["dependency_keys"]:
            mine = {k for k in pkeys if by_key[k]["milestone_key"] == m["local_key"]}
            theirs = {k for k in pkeys if by_key[k]["milestone_key"] == dep}
            if any(_reach(pdeps, k) & mine for k in theirs):
                raise FoundationError(f"milestone {dep} depends on milestone {m['local_key']} through packets, but {m['local_key']} lists {dep} as its dependency")
    decisions = _decisions(document["decisions"], pkeys | mkeys, finding_ids)
    return {"summary": document["summary"].strip(), "decisions": decisions, "milestones": milestones, "packets": packets}


def _fail(message: str):  # noqa: ANN202 - raises
    raise FoundationError(message)


def _decisions(value: object, known: set[str], finding_ids: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise FoundationError("breakdown.decisions must be a list (empty when no routine technical choice needed recording)")
    result, seen = [], set()
    for item in value:
        item = _exact(item, {"local_key", "subject", "answer", "rationale", "affected_keys", "finding_ids"}, "each breakdown decision")
        key = _text(item["local_key"], "decision.local_key")
        if key in seen:
            raise FoundationError(f"decision local_key {key} is used twice")
        seen.add(key)
        affected = _keys(item["affected_keys"], f"decision {key} affected_keys", known)
        found = _texts(item["finding_ids"], f"decision {key} finding_ids")
        if any(f not in finding_ids for f in found):
            raise FoundationError(f"decision {key} finding_ids names a finding that is not saved")
        result.append({"local_key": key, "subject": _text(item["subject"], f"decision {key} subject"), "answer": _text(item["answer"], f"decision {key} answer"),
                       "rationale": _text(item["rationale"], f"decision {key} rationale"), "affected_keys": affected, "finding_ids": found})
    return result


def _plan_command(item: object, name: str, extra: set[str], selected: set[str], by_key: Mapping[str, Any], members: set[str], source_sha: Callable[[str], str | None]) -> dict[str, Any]:
    fields = {"subject", "command", "script_path", "script_sha256", "environment_ref", "planned_by_packet_key"} | extra
    item = _exact(item, fields, name)
    command = _texts(item["command"], f"{name} command", minimum=1)
    path, digest, env, planned = item["script_path"], item["script_sha256"], item["environment_ref"], item["planned_by_packet_key"]
    if env is not None and env not in selected:
        raise FoundationError(f"{name} environment_ref {env!r} is not among the plan's environment_refs")
    if path is not None:
        path = _safe_path(path, f"{name} script_path")
        actual = source_sha(path)
        if actual is not None:
            if digest != actual:
                raise FoundationError(f"{name} script_sha256 must be the hash of {path} at the assigned source commit ({actual})")
            if planned is not None:
                raise FoundationError(f"{name} script {path} already exists, so planned_by_packet_key must be null")
        else:
            if digest is not None or planned is None:
                raise FoundationError(f"{name} script {path} does not exist in the source: give script_sha256 null and name the packet that creates it in planned_by_packet_key")
            if planned not in members or not _covers(by_key[planned]["permitted_paths"], path):
                raise FoundationError(f"{name} script {path} must be created by a packet of the same milestone whose permitted_paths cover it")
    elif digest is not None or planned is not None:
        raise FoundationError(f"{name} names no script_path, so script_sha256 and planned_by_packet_key must be null")
    if not _SHA.fullmatch(digest or "0" * 64):
        raise FoundationError(f"{name} script_sha256 must be a lowercase SHA-256 or null")
    return {"subject": _text(item["subject"], f"{name} subject"), "command": command, "script_path": path, "script_sha256": digest, "environment_ref": env, "planned_by_packet_key": planned}


def _qa_plan(value: object, name: str, catalog: Mapping[str, Any], by_key: Mapping[str, Any], members: set[str], source_sha: Callable[[str], str | None]) -> dict[str, Any]:
    value = _exact(value, {"setup_steps", "support_processes", "environment_refs", "secret_refs", "allowed_network_dependencies", "project_binding_hash", "data_requirements", "checks", "artifact_requirements", "cleanup_steps", "reset_check"}, name)
    envs, secrets, network = (_texts(value[k], f"{name} {k}") for k in ("environment_refs", "secret_refs", "allowed_network_dependencies"))
    for label, chosen, table in (("environment", envs, "environments"), ("secret", secrets, "secrets"), ("network dependency", network, "network_dependencies")):
        unknown = [c for c in chosen if c not in catalog[table]]
        if unknown:
            raise QaBindingError(f"{name} selects {label} {', '.join(unknown)}, which the operator's QA catalog does not provide (available: {', '.join(sorted(catalog[table])) or 'none'}); ask the Owner what the operator must provision")
    allowed_secrets = {s for e in envs for s in catalog["environments"][e]["secret_names"]}
    allowed_network = {n for e in envs for n in catalog["environments"][e]["network_dependency_names"]}
    if any(s not in allowed_secrets for s in secrets) or any(n not in allowed_network for n in network):
        raise QaBindingError(f"{name} selects a secret or network dependency that none of its selected environments permits")
    expected = catalog.get("project_binding_hash") if (envs or secrets or network) else None
    if value["project_binding_hash"] != expected:
        raise FoundationError(f"{name} project_binding_hash must be {expected!r} ({'the catalog hash, because environments, secrets or network dependencies are selected' if expected else 'null for a self-contained plan'})")
    data = []
    for entry in value["data_requirements"] if isinstance(value["data_requirements"], list) else _fail(f"{name} data_requirements must be a list"):
        entry = _exact(entry, {"subject", "dataset_or_generator", "sha256", "classification", "sanitization", "setup_operation", "real_input_path", "expected_result", "capability_path", "planned_by_packet_key"}, f"{name} data requirement")
        if entry["classification"] not in {"test", "synthetic", "sanitized_copy"}:
            raise FoundationError(f"{name} data requirement classification must be test, synthetic or sanitized_copy")
        if (entry["sha256"] is None) == (entry["planned_by_packet_key"] is None) or (entry["sha256"] is not None and not _SHA.fullmatch(str(entry["sha256"]))):
            raise FoundationError(f"{name} data requirement {entry['subject']!r} needs a SHA-256, or null with planned_by_packet_key naming the packet that creates the data")
        if entry["planned_by_packet_key"] is not None and entry["planned_by_packet_key"] not in members:
            raise FoundationError(f"{name} data requirement planned_by_packet_key must be a packet of the same milestone")
        data.append({k: (_text(entry[k], f"{name} data.{k}") if k not in {"sha256", "planned_by_packet_key"} else entry[k]) for k in entry})
    checks = []
    for check in value["checks"] if isinstance(value["checks"], list) and value["checks"] else _fail(f"{name} checks must be a nonempty list"):
        check = _exact(check, {"subject", "user_journey", "failure_cases", "required_artifacts"}, f"{name} check")
        checks.append({"subject": _text(check["subject"], f"{name} check subject"), "user_journey": _text(check["user_journey"], f"{name} check user_journey"),
                       "failure_cases": _texts(check["failure_cases"], f"{name} check failure_cases", minimum=1), "required_artifacts": _texts(check["required_artifacts"], f"{name} check required_artifacts")})
    setup = [_plan_command(s, f"{name} setup step", set(), set(envs), by_key, members, source_sha) for s in value["setup_steps"]] if isinstance(value["setup_steps"], list) else _fail(f"{name} setup_steps must be a list")
    support = [_plan_command(s, f"{name} support process", {"health_condition", "port_rule"}, set(envs), by_key, members, source_sha) for s in value["support_processes"]] if isinstance(value["support_processes"], list) else _fail(f"{name} support_processes must be a list")
    for s, raw in zip(support, value["support_processes"]):
        s["health_condition"], s["port_rule"] = _text(raw["health_condition"], f"{name} support health_condition"), _text(raw["port_rule"], f"{name} support port_rule")
    return {"setup_steps": setup, "support_processes": support, "environment_refs": envs, "secret_refs": secrets, "allowed_network_dependencies": network,
            "project_binding_hash": value["project_binding_hash"], "data_requirements": data, "checks": checks,
            "artifact_requirements": _texts(value["artifact_requirements"], f"{name} artifact_requirements"), "cleanup_steps": _texts(value["cleanup_steps"], f"{name} cleanup_steps", minimum=1),
            "reset_check": _text(value["reset_check"], f"{name} reset_check")}


# ----------------------------------------------------------------------------- record building

def _ref(record: Mapping[str, Any]) -> dict[str, Any]:
    return {"id": record["id"], "subject": record["subject"], "version": record["version"], "path": record["path"]}


def assign_ids(checked: Mapping[str, Any], known: Mapping[tuple[str, str], str]) -> dict[tuple[str, str], str]:
    """Stable identities: a local key keeps its saved id; a new key takes the next number of its kind."""
    ids = dict(known)
    for kind, items in (("milestone", checked["milestones"]), ("packet", checked["packets"])):
        used = {int(v.rsplit("-", 1)[1]) for (k, _), v in ids.items() if k == kind}
        for item in items:
            if (kind, item["local_key"]) not in ids:
                number = max(used, default=0) + 1
                used.add(number)
                ids[(kind, item["local_key"])] = f"{PREFIX[kind]}-{number}"
    for m in checked["milestones"]:
        ids[("qa_plan", m["local_key"])] = f"qa-plan-{ids[('milestone', m['local_key'])].rsplit('-', 1)[1]}"
    return ids


def build_breakdown_set(
    *, project_id: str, activity_id: str, version: int, registration_ref: Mapping[str, Any], source_commit: str, decision_version: int, outcomes: Sequence[Mapping[str, Any]],
    checked: Mapping[str, Any], ids: Mapping[tuple[str, str], str], previous: Mapping[str, Mapping[str, Any]], carried_foundation: Sequence[Mapping[str, Any]], prior_decisions: Mapping[str, Any],
    owner_decisions: Sequence[Mapping[str, Any]], owner_id: str, finding_refs: Mapping[str, Mapping[str, Any]], role_refs: Mapping[str, Mapping[str, Any]], document_refs: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, bytes], dict[str, Any], str, dict[str, dict[str, Any]]]:
    """Return (repository files, manifest, manifest path, record states). ``previous`` maps record id to its last published state.

    A record is rewritten when its authored content changed or it refers to a rewritten record (its links carry
    versions); every other record is carried forward by its exact earlier reference.
    """
    base = f"{ROOT}/versions/{version}"
    by_id = {o["id"]: o for o in outcomes}
    common = {"schema_version": 1, "project_id": project_id, "activity_id": activity_id, "registration_ref": dict(registration_ref), "source_commit": source_commit}
    mid = lambda key: ids[("milestone", key)]  # noqa: E731
    pid = lambda key: ids[("packet", key)]  # noqa: E731
    qid = lambda key: ids[("qa_plan", key)]  # noqa: E731
    subjects = {mid(m["local_key"]): m["subject"] for m in checked["milestones"]}
    subjects.update({pid(p["local_key"]): p["subject"] for p in checked["packets"]})
    subjects.update({qid(m["local_key"]): f"Quality Assurance plan for {m['subject']}" for m in checked["milestones"]})
    kinds = {mid(m["local_key"]): "milestone" for m in checked["milestones"]} | {pid(p["local_key"]): "packet" for p in checked["packets"]} | {qid(m["local_key"]): "qa_plan" for m in checked["milestones"]}
    # authored bodies use bare ids for links; versions are filled in after the rewrite set is known
    bodies: dict[str, dict[str, Any]] = {}
    links: dict[str, list[str]] = {}
    for m in checked["milestones"]:
        i = mid(m["local_key"])
        bodies[i] = {"outcome": m["outcome"], "outcome_ids": sorted(m["outcome_ids"]), "included_scope": m["included_scope"], "exclusions": m["exclusions"], "integration_points": m["integration_points"],
                     "completion_criteria": [{"id": f"criterion-{n}", **c, "accepted_exception": None} for n, c in enumerate(m["completion_criteria"], 1)], "subject": m["subject"]}
        links[i] = [pid(k) for k in m["packet_keys"]] + [qid(m["local_key"])] + [mid(k) for k in m["dependency_keys"]]
        q = m["qa_plan"]
        qi = qid(m["local_key"])
        bodies[qi] = {"subject": subjects[qi], "plan": q}
        links[qi] = [i] + [pid(x) for x in _planned(q)]
    for p in checked["packets"]:
        i = pid(p["local_key"])
        bodies[i] = {k: p[k] for k in ("subject", "purpose", "outcome_ids", "included_scope", "exclusions", "permitted_paths", "specialist_key", "finding_ids", "shared_code_constraints", "execution_requirements", "verification", "essential_failure_checks", "required_outputs")}
        bodies[i]["completion_criteria"] = [{"id": f"criterion-{n}", **c, "accepted_exception": None} for n, c in enumerate(p["completion_criteria"], 1)]
        links[i] = [mid(p["milestone_key"])] + [pid(k) for k in p["dependency_keys"]] + [pid(k) for k in p["parallel_with_keys"]]
    authored = {i: sha256(canonical_json({"body": b, "links": sorted(links[i])}).encode()) for i, b in bodies.items()}
    rewrite = {i for i in bodies if i not in previous or previous[i]["authored_sha256"] != authored[i]}
    while True:
        grown = {i for i in bodies if i not in rewrite and any(t in rewrite for t in links[i])}
        if not grown:
            break
        rewrite |= grown
    final = {i: (previous[i]["version"] + 1 if i in previous and i in rewrite else previous[i]["version"] if i in previous else 1) for i in bodies}
    paths = {i: f"{DIRS[kinds[i]]}/{i}.json" for i in bodies}
    lref = lambda i: {"id": i, "subject": subjects[i], "version": final[i], "path": paths[i]}  # noqa: E731

    records: dict[str, dict[str, Any]] = {}
    for m in checked["milestones"]:
        i = mid(m["local_key"])
        b = bodies[i]
        records[i] = {**common, "id": i, "subject": m["subject"], "version": final[i], "outcome": b["outcome"], "project_outcome_refs": [dict(by_id[o]) for o in b["outcome_ids"]],
                      "included_scope": b["included_scope"], "exclusions": b["exclusions"], "work_packet_refs": [lref(pid(k)) for k in m["packet_keys"]], "qa_plan_ref": lref(qid(m["local_key"])),
                      "dependencies": [lref(mid(k)) for k in m["dependency_keys"]], "integration_points": b["integration_points"], "completion_criteria": b["completion_criteria"]}
        q = m["qa_plan"]
        qi = qid(m["local_key"])
        plan = dict(q)
        for field in ("setup_steps", "support_processes"):
            plan[field] = [{**{k: v for k, v in s.items() if k != "planned_by_packet_key"}, "planned_by_packet_ref": None if s["planned_by_packet_key"] is None else lref(pid(s["planned_by_packet_key"]))} for s in q[field]]
        plan["data_requirements"] = [{**{k: v for k, v in d.items() if k != "planned_by_packet_key"}, "planned_by_packet_ref": None if d["planned_by_packet_key"] is None else lref(pid(d["planned_by_packet_key"]))} for d in q["data_requirements"]]
        records[qi] = {**common, "id": qi, "subject": subjects[qi], "version": final[qi], "milestone_ref": lref(i), **plan}
    for p in checked["packets"]:
        i = pid(p["local_key"])
        b = bodies[i]
        role = role_refs[p["specialist_key"]]
        records[i] = {**common, "id": i, "subject": p["subject"], "version": final[i], "purpose": p["purpose"], "project_outcome_refs": [dict(by_id[o]) for o in b["outcome_ids"]],
                      "development_milestone_ref": lref(mid(p["milestone_key"])), "included_scope": b["included_scope"], "exclusions": b["exclusions"], "permitted_paths": b["permitted_paths"],
                      "starting_context": {"source_commit": source_commit, "document_refs": [dict(r) for r in document_refs], "finding_refs": [dict(finding_refs[f]) for f in b["finding_ids"]], "specialist_role_ref": dict(role)},
                      "dependencies": [lref(pid(k)) for k in p["dependency_keys"]], "shared_code_constraints": b["shared_code_constraints"],
                      "parallel_opportunities": [lref(pid(k)) for k in p["parallel_with_keys"]], "execution_requirements": b["execution_requirements"], "completion_criteria": b["completion_criteria"],
                      "verification": b["verification"], "essential_failure_checks": b["essential_failure_checks"], "required_outputs": b["required_outputs"]}
    files: dict[str, bytes] = {}
    inventory: list[dict[str, Any]] = []
    for i in sorted(rewrite):
        path = f"{base}/{paths[i]}"
        files[path] = encode(records[i])
        deps = sorted((lref(t) for t in links[i]), key=lambda r: (r["path"], r["id"], r["version"]))
        inventory.append({"record_type": TYPES[kinds[i]], "id": i, "subject": subjects[i], "version": final[i], "path": paths[i], "sha256": sha256(files[path]), "commit": None, "dependencies": deps})
    # decisions snapshot: always part of the set; entries keep their identity and change version only when their content changes
    entries = [dict(e) for e in prior_decisions["decisions"]]
    seen_questions = {e["source_question_id"] for e in entries if e["source_question_id"]}
    inv_ref = {"id": "investigation", "subject": "Code investigation", "version": 1, "path": "investigation.json"}
    for owner in owner_decisions:
        if owner["question_id"] not in seen_questions:
            entries.append({"id": f"decision-{len(entries) + 1}", "subject": owner["subject"], "version": 1, "source_question_id": owner["question_id"], "source_finding_ref": None,
                            "answer": owner["answer"], "authority": {"kind": "owner", "identity": owner_id}, "affected_items": [inv_ref], "rationale": owner["rationale"]})
    for d in checked["decisions"]:
        keys = d["affected_keys"]
        affected = [lref(mid(k)) if ("milestone", k) in ids else lref(pid(k)) for k in keys]
        entry = {"id": f"breakdown-decision-{re.sub(r'[^a-z0-9]+', '-', d['local_key'].lower()).strip('-')}", "subject": d["subject"], "version": 1, "source_question_id": None,
                 "source_finding_ref": dict(finding_refs[d["finding_ids"][0]]) if d["finding_ids"] else None, "answer": d["answer"],
                 "authority": {"kind": "architect", "identity": "project_architect"}, "affected_items": affected or [inv_ref], "rationale": d["rationale"]}
        index = next((n for n, e in enumerate(entries) if e["id"] == entry["id"]), None)
        if index is None:
            entries.append(entry)
        else:
            entry["version"] = entries[index]["version"]
            if entries[index] != entry:
                entry["version"] += 1
                entries[index] = entry
    decisions_version = int(prior_decisions["version"]) + (0 if entries == prior_decisions["decisions"] else 1)
    decisions_record = {**common, "id": "decisions", "subject": "Architecture decisions", "version": decisions_version, "decision_version": f"d{decision_version}", "decisions": entries}
    files[f"{base}/decisions.json"] = encode(decisions_record)
    dec_ref = {"id": "decisions", "subject": "Architecture decisions", "version": decisions_version, "path": "decisions.json"}
    inventory.append({"record_type": "decisions", "id": "decisions", "subject": "Architecture decisions", "version": decisions_version, "path": "decisions.json",
                      "sha256": sha256(files[f"{base}/decisions.json"]), "commit": None, "dependencies": [inv_ref]})
    inventory.sort(key=lambda e: (e["path"], e["id"]))
    carried = [dict(c) for c in carried_foundation]
    for i in sorted(bodies):
        if i not in rewrite:
            state = previous[i]
            carried.append({"record_ref": {"id": i, "subject": subjects[i], "version": final[i], "path": state["repo_path"], "sha256": state["sha256"], "commit": state["commit"]},
                            "validated_registration_ref": dict(registration_ref), "validated_source_commit": source_commit, "reason": "Unchanged by this amendment and none of the records it links to changed."})
    carried.sort(key=lambda c: (c["record_ref"]["path"], c["record_ref"]["id"], c["record_ref"]["version"]))
    input_refs = sorted((dict(o) for o in outcomes), key=lambda r: (r["path"], r["id"], r["version"]))
    content = {"registration_ref": dict(registration_ref), "source_commit": source_commit, "decision_version": f"d{decision_version}", "decision_ref": dec_ref,
               "input_refs": input_refs, "carried_forward": carried, "inventory": inventory}
    manifest = {**common, "version": version, "id": "manifest", "subject": "Architecture breakdown manifest", "stage": "breakdown", "decision_version": f"d{decision_version}",
                "input_refs": input_refs, "reviewed_content_hash": sha256(canonical_json(content).encode("utf-8")), "inventory": inventory, "carried_forward": carried, "decision_ref": dec_ref}
    manifest_path = f"{base}/manifest.json"
    files[manifest_path] = encode(manifest)
    states = {i: {"record_id": i, "kind": kinds[i], "version": final[i], "authored_sha256": authored[i], "repo_path": f"{base}/{paths[i]}" if i in rewrite else previous[i]["repo_path"],
                  "sha256": next(e["sha256"] for e in inventory if e["id"] == i) if i in rewrite else previous[i]["sha256"], "set_version": version if i in rewrite else previous[i]["set_version"],
                  "subject": subjects[i], "rewritten": i in rewrite} for i in bodies}
    return files, manifest, manifest_path, states


def _planned(plan: Mapping[str, Any]) -> list[str]:
    keys = [s["planned_by_packet_key"] for s in list(plan["setup_steps"]) + list(plan["support_processes"]) + list(plan["data_requirements"]) if s["planned_by_packet_key"]]
    return sorted(set(keys))


def summary(states: Mapping[str, Mapping[str, Any]], checked: Mapping[str, Any], ids: Mapping[tuple[str, str], str]) -> dict[str, Any]:
    """A plain view of the breakdown for the CLI: milestones with their packets, dependencies and parallel opportunities."""
    def pid(key: str) -> str:
        return ids[("packet", key)]
    packets = {pid(p["local_key"]): p for p in checked["packets"]}
    return {
        "milestones": [{"id": ids[("milestone", m["local_key"])], "subject": m["subject"], "outcome_ids": m["outcome_ids"], "packets": [pid(k) for k in m["packet_keys"]],
                        "depends_on": [ids[("milestone", k)] for k in m["dependency_keys"]], "qa_plan": ids[("qa_plan", m["local_key"])]} for m in checked["milestones"]],
        "packets": [{"id": i, "subject": p["subject"], "milestone": ids[("milestone", p["milestone_key"])], "depends_on": [pid(k) for k in p["dependency_keys"]],
                     "parallel_with": [pid(k) for k in p["parallel_with_keys"]], "specialist": p["specialist_key"]} for i, p in packets.items()],
        "versions": {i: s["version"] for i, s in states.items()},
    }
