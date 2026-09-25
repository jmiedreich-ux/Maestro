"""The ``execution`` configuration snapshot: validated once when an Execution activity starts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

_ADAPTER_TOOLS = {"local_qwen_qwen_cli": "qwen", "codex_cli": "codex", "claude_code_cli": "claude_code"}
_CAPABILITIES = frozenset({"code_edit", "local_command", "repository_search", "image_inspection", "approved_network"})
_TOOLS = frozenset({"codex", "claude_code", "qwen"})


class ExecutionConfigError(ValueError):
    pass


def _positive(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ExecutionConfigError(f"execution.{name} must be a positive integer")
    return value


def _pair(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("tool") not in _TOOLS or not isinstance(value.get("model"), str) or not value["model"]:
        raise ExecutionConfigError(f"execution.{name} needs a supported tool and an exact model")
    return {"tool": value["tool"], "model": value["model"], "run_timeout_seconds": _positive(value.get("run_timeout_seconds"), f"{name}.run_timeout_seconds")}


def _routes(value: object, name: str) -> dict[str, Any]:
    """Primary and backup routes for a Project Architect or fidelity reviewer role: both required and distinct."""
    if not isinstance(value, Mapping):
        raise ExecutionConfigError(f"execution.{name} needs primary and backup routes")
    result: dict[str, Any] = {}
    for slot in ("primary", "backup"):
        route = value.get(slot)
        if not isinstance(route, Mapping) or route.get("tool") not in {"codex", "claude_code"} or not isinstance(route.get("model"), str) or not route["model"]:
            raise ExecutionConfigError(f"execution.{name}.{slot} needs tool codex or claude_code and an exact model")
        result[slot] = {"tool": route["tool"], "model": route["model"]}
    if (result["primary"]["tool"], result["primary"]["model"]) == (result["backup"]["tool"], result["backup"]["model"]):
        raise ExecutionConfigError(f"execution.{name} primary and backup must be different tool and model pairs")
    result["run_timeout_seconds"] = _positive(value.get("run_timeout_seconds"), f"{name}.run_timeout_seconds")
    return result


def _support(table: object) -> dict[str, Any] | None:
    if table is None:
        return None
    if not isinstance(table, Mapping):
        raise ExecutionConfigError("execution.architectural_support must be a table")
    reviews = table.get("maximum_fidelity_reviews", 2)
    return {"architect": _routes(table.get("architect"), "architectural_support.architect"),
            "fidelity_reviewer": _routes(table.get("fidelity_reviewer"), "architectural_support.fidelity_reviewer"),
            "maximum_fidelity_reviews": _positive(reviews, "architectural_support.maximum_fidelity_reviews")}


def _qa(table: object) -> dict[str, Any] | None:
    """Isolated Quality Assurance settings: service-owned directories, retention, timeouts and the operator's test-only project bindings."""
    if table is None:
        return None
    if not isinstance(table, Mapping):
        raise ExecutionConfigError("execution.qa must be a table")
    for name in ("environment_root", "artifact_root"):
        if not isinstance(table.get(name), str) or not table[name].startswith("/"):
            raise ExecutionConfigError(f"execution.qa.{name} must be an absolute path")
    bindings: dict[str, Any] = {}
    for project_id, binding in (table.get("project_bindings") or {}).items():
        environments = binding.get("environments", {}) if isinstance(binding, Mapping) else None
        if not isinstance(environments, Mapping):
            raise ExecutionConfigError(f"execution.qa.project_bindings.{project_id} needs environments")
        clean_environments = {}
        for name, environment in environments.items():
            if not isinstance(environment, Mapping) or environment.get("classification") != "test":
                raise ExecutionConfigError(f"execution.qa.project_bindings.{project_id}.environments.{name} must be classified test; production bindings are rejected")
            variables = environment.get("variables", {})
            if not isinstance(variables, Mapping) or not all(isinstance(k, str) and isinstance(v, str) for k, v in variables.items()):
                raise ExecutionConfigError(f"execution.qa.project_bindings.{project_id}.environments.{name}.variables must map names to text")
            clean_environments[name] = {"classification": "test", "variables": dict(variables), "secret_names": sorted(environment.get("secret_names", [])), "network_dependency_names": sorted(environment.get("network_dependency_names", []))}
        secrets = {}
        for name, secret in (binding.get("secrets") or {}).items():
            if not isinstance(secret, Mapping) or secret.get("classification") != "test" or not isinstance(secret.get("credential_ref"), str) or not isinstance(secret.get("environment_variable"), str):
                raise ExecutionConfigError(f"execution.qa.project_bindings.{project_id}.secrets.{name} needs classification test, a credential_ref and an environment_variable")
            secrets[name] = {"classification": "test", "credential_ref": secret["credential_ref"], "environment_variable": secret["environment_variable"]}
        networks = {}
        for name, dependency in (binding.get("network_dependencies") or {}).items():
            if not isinstance(dependency, Mapping) or not all(isinstance(dependency.get(k), str) for k in ("host", "protocol")) or not isinstance(dependency.get("ports"), list):
                raise ExecutionConfigError(f"execution.qa.project_bindings.{project_id}.network_dependencies.{name} needs a host, protocol and ports")
            networks[name] = {"host": dependency["host"], "protocol": dependency["protocol"], "ports": sorted(dependency["ports"])}
        bindings[project_id] = {"environments": clean_environments, "secrets": secrets, "network_dependencies": networks}
    patterns = table.get("secret_patterns", [])
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ExecutionConfigError("execution.qa.secret_patterns must be a list of regular expressions")
    return {"environment_root": table["environment_root"], "artifact_root": table["artifact_root"], "project_bindings": bindings, "secret_patterns": patterns,
            "artifact_retention_days_after_close": _positive(table.get("artifact_retention_days_after_close", 30), "qa.artifact_retention_days_after_close"),
            "setup_timeout_seconds": _positive(table.get("setup_timeout_seconds", 300), "qa.setup_timeout_seconds"),
            "maximum_artifact_bytes": _positive(table.get("maximum_artifact_bytes", 20_000_000), "qa.maximum_artifact_bytes")}


def validate(table: object) -> dict[str, Any]:
    """The normalized configuration with defaults applied, or a plain error naming the missing or invalid setting."""
    if not isinstance(table, Mapping):
        raise ExecutionConfigError("the execution settings are not configured")
    outputs = table.get("saved_outputs")
    if not isinstance(outputs, Mapping) or outputs.get("schema") not in {"execution@1", "execution@2", "execution@3"}:
        raise ExecutionConfigError('execution.saved_outputs.schema must be "execution@1", "execution@2" or "execution@3"')
    manager = table.get("development_manager")
    if not isinstance(manager, Mapping) or not isinstance(manager.get("routes"), Mapping) or not manager["routes"]:
        raise ExecutionConfigError("execution.development_manager.routes needs at least one named route")
    routes: dict[str, Any] = {}
    for route_id, route in manager["routes"].items():
        if not isinstance(route, Mapping) or route.get("tool") not in {"codex", "claude_code"} or not isinstance(route.get("model"), str) or not route["model"]:
            raise ExecutionConfigError(f"execution.development_manager.routes.{route_id} needs tool codex or claude_code and an exact model")
        routes[route_id] = {k: route[k] for k in ("tool", "model", "backup_route_id") if k in route}
    coders = table.get("coder_routes")
    if not isinstance(coders, Mapping) or not coders:
        raise ExecutionConfigError("execution.coder_routes needs at least one route")
    coder_routes: dict[str, Any] = {}
    for route_id, route in coders.items():
        if not isinstance(route, Mapping) or route.get("adapter") not in _ADAPTER_TOOLS or not isinstance(route.get("model"), str) or not route["model"]:
            raise ExecutionConfigError(f"execution.coder_routes.{route_id} needs a supported adapter and an exact model")
        capabilities = route.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities or not set(capabilities) <= _CAPABILITIES:
            raise ExecutionConfigError(f"execution.coder_routes.{route_id}.capabilities must be a nonempty list of known capabilities")
        if route.get("location") not in {"local_ai_box", "cloud"}:
            raise ExecutionConfigError(f"execution.coder_routes.{route_id}.location must be local_ai_box or cloud")
        coder_routes[route_id] = {
            "adapter": route["adapter"], "tool": _ADAPTER_TOOLS[route["adapter"]], "model": route["model"], "location": route["location"],
            "capabilities": sorted(set(capabilities)), "context_limit_tokens": _positive(route.get("context_limit_tokens"), f"coder_routes.{route_id}.context_limit_tokens"),
            "maximum_concurrent_runs": _positive(route.get("maximum_concurrent_runs"), f"coder_routes.{route_id}.maximum_concurrent_runs"),
            "run_timeout_seconds": _positive(route.get("run_timeout_seconds"), f"coder_routes.{route_id}.run_timeout_seconds"),
            **({"backup_route_id": route["backup_route_id"]} if "backup_route_id" in route else {}),
        }
    default = table.get("coder_default_route_id")
    if default not in coder_routes:
        raise ExecutionConfigError("execution.coder_default_route_id must name a configured coder route")
    reviewers = table.get("reviewers")
    packet = reviewers.get("packet") if isinstance(reviewers, Mapping) else None
    if not isinstance(packet, Mapping):
        raise ExecutionConfigError("execution.reviewers.packet needs primary and backup routes")
    reviewer = {"primary": _pair(packet.get("primary"), "reviewers.packet.primary")}
    if "backup" in packet:
        reviewer["backup"] = _pair(packet["backup"], "reviewers.packet.backup")
        if (reviewer["backup"]["tool"], reviewer["backup"]["model"]) == (reviewer["primary"]["tool"], reviewer["primary"]["model"]):
            raise ExecutionConfigError("execution.reviewers.packet primary and backup must differ")
    integration_reviewer = None
    if isinstance(reviewers, Mapping) and isinstance(reviewers.get("integration"), Mapping):
        integration = reviewers["integration"]
        integration_reviewer = {"primary": _pair(integration.get("primary"), "reviewers.integration.primary")}
        if "backup" in integration:
            integration_reviewer["backup"] = _pair(integration["backup"], "reviewers.integration.backup")
    milestone_reviewer = None
    if isinstance(reviewers, Mapping) and isinstance(reviewers.get("milestone"), Mapping):
        milestone = reviewers["milestone"]
        milestone_reviewer = {"primary": _pair(milestone.get("primary"), "reviewers.milestone.primary")}
        if "backup" in milestone:
            milestone_reviewer["backup"] = _pair(milestone["backup"], "reviewers.milestone.backup")
    quality_assurance = None
    if isinstance(table.get("quality_assurance"), Mapping):
        quality_assurance = _pair(table["quality_assurance"], "quality_assurance")
        if quality_assurance["tool"] not in {"codex", "claude_code"}:
            raise ExecutionConfigError("execution.quality_assurance needs tool codex or claude_code")
    manager_pair = None
    if isinstance(table.get("integration_manager"), Mapping):
        manager_pair = _pair(table["integration_manager"], "integration_manager")
        if manager_pair["tool"] not in {"codex", "claude_code"}:
            raise ExecutionConfigError("execution.integration_manager needs tool codex or claude_code")
    reviews = table.get("reviews", {})
    integration_rounds = 2
    if isinstance(reviews, Mapping) and isinstance(reviews.get("integration"), Mapping):
        integration_rounds = reviews["integration"].get("maximum_completed_rounds", 2)
    milestone_rounds = reviews["milestone"].get("maximum_completed_rounds", 3) if isinstance(reviews, Mapping) and isinstance(reviews.get("milestone"), Mapping) else 3
    rounds = reviews.get("packet", {}).get("maximum_completed_rounds", 2) if isinstance(reviews, Mapping) and isinstance(reviews.get("packet", {}), Mapping) else 2
    recovery = table.get("recovery", {}) if isinstance(table.get("recovery", {}), Mapping) else {}
    support = _support(table.get("architectural_support"))
    qa = _qa(table.get("qa"))
    gap = _routes(table["milestone_gap_architect"], "milestone_gap_architect") if table.get("milestone_gap_architect") is not None else None
    return {
        "schema": "execution@3",
        "development_manager": {"routes": routes, "run_timeout_seconds": _positive(manager.get("run_timeout_seconds"), "development_manager.run_timeout_seconds")},
        "reviewers": {"packet": reviewer},
        "coder_default_route_id": default,
        "coder_routes": coder_routes,
        "reviews": {"packet": {"maximum_completed_rounds": _positive(rounds, "reviews.packet.maximum_completed_rounds")},
                    "integration": {"maximum_completed_rounds": _positive(integration_rounds, "reviews.integration.maximum_completed_rounds")},
                    "milestone": {"maximum_completed_rounds": _positive(milestone_rounds, "reviews.milestone.maximum_completed_rounds")}},
        # Optional: without them the Integration Manager uses the Development Manager's route and integration review uses the packet reviewers.
        **({"architectural_support": support} if support else {}),
        **({"milestone_gap_architect": gap} if gap else {}),
        **({"integration_manager": manager_pair} if manager_pair else {}),
        **({"integration_reviewers": integration_reviewer} if integration_reviewer else {}),
        # Optional: without them a finished milestone waits, with a plain blocker, for Quality Assurance and outcome review to be configured.
        **({"milestone_reviewers": milestone_reviewer} if milestone_reviewer else {}),
        **({"quality_assurance": quality_assurance} if quality_assurance else {}),
        **({"qa": qa} if qa else {}),
        "recovery": {"automatic_recovery_attempts": recovery.get("automatic_recovery_attempts", 2), "manual_retry_attempts": recovery.get("manual_retry_attempts", 1)},
    }


def digest(config: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
