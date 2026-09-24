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


def validate(table: object) -> dict[str, Any]:
    """The normalized configuration with defaults applied, or a plain error naming the missing or invalid setting."""
    if not isinstance(table, Mapping):
        raise ExecutionConfigError("the execution settings are not configured")
    outputs = table.get("saved_outputs")
    if not isinstance(outputs, Mapping) or outputs.get("schema") != "execution@1":
        raise ExecutionConfigError('execution.saved_outputs.schema must be "execution@1"')
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
    manager_pair = None
    if isinstance(table.get("integration_manager"), Mapping):
        manager_pair = _pair(table["integration_manager"], "integration_manager")
        if manager_pair["tool"] not in {"codex", "claude_code"}:
            raise ExecutionConfigError("execution.integration_manager needs tool codex or claude_code")
    reviews = table.get("reviews", {})
    integration_rounds = 2
    if isinstance(reviews, Mapping) and isinstance(reviews.get("integration"), Mapping):
        integration_rounds = reviews["integration"].get("maximum_completed_rounds", 2)
    rounds = reviews.get("packet", {}).get("maximum_completed_rounds", 2) if isinstance(reviews, Mapping) and isinstance(reviews.get("packet", {}), Mapping) else 2
    recovery = table.get("recovery", {}) if isinstance(table.get("recovery", {}), Mapping) else {}
    return {
        "schema": "execution@1",
        "development_manager": {"routes": routes, "run_timeout_seconds": _positive(manager.get("run_timeout_seconds"), "development_manager.run_timeout_seconds")},
        "reviewers": {"packet": reviewer},
        "coder_default_route_id": default,
        "coder_routes": coder_routes,
        "reviews": {"packet": {"maximum_completed_rounds": _positive(rounds, "reviews.packet.maximum_completed_rounds")},
                    "integration": {"maximum_completed_rounds": _positive(integration_rounds, "reviews.integration.maximum_completed_rounds")}},
        # Optional: without them the Integration Manager uses the Development Manager's route and integration review uses the packet reviewers.
        **({"integration_manager": manager_pair} if manager_pair else {}),
        **({"integration_reviewers": integration_reviewer} if integration_reviewer else {}),
        "recovery": {"automatic_recovery_attempts": recovery.get("automatic_recovery_attempts", 2), "manual_retry_attempts": recovery.get("manual_retry_attempts", 1)},
    }


def digest(config: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
