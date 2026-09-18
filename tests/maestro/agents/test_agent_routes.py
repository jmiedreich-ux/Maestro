from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from maestro.agents import (
    AdapterObservation,
    AgentRouteError,
    AgentRoutePreflight,
    AgentRouteRegistry,
    InstalledAdapter,
    RoleSelections,
    RouteRequirements,
    RunningToolIdentity,
    ToolModelSelection,
    verify_running_identity,
)
from maestro.foundation import canonical_json
from maestro.service.processes import ProcessHandlerRegistry, ProcessProvider, ProcessSnapshot
from maestro.service.resources import BundleSnapshot


CODEX_MODEL = "openai/gpt-5.6-codex-2026-09-01"
CLAUDE_MODEL = "anthropic/claude-opus-4-1-20260805"
CODEX_ALIAS = "openai/gpt-latest"
CAPABILITIES = ("approved_network", "code_edit", "local_command", "repository_search")


class RecordingInspector:
    def __init__(self, observation: AdapterObservation) -> None:
        self.observation = observation
        self.calls: list[tuple[str, str]] = []

    def inspect(self, route, configuration_hash):
        self.calls.append((route.tool, configuration_hash))
        if self.observation.configuration_hash == "expected":
            return replace(self.observation, configuration_hash=configuration_hash)
        return self.observation


class AgentRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.codex_executable = self._executable("codex")
        self.claude_executable = self._executable("claude")
        self.routes = AgentRouteRegistry.from_mapping(
            {
                "codex": {
                    "executable": str(self.codex_executable),
                    "credential_profile": "credential-codex",
                    "settings_profile": "settings-codex",
                    "allowed_model_ids": [CODEX_MODEL, CODEX_ALIAS],
                },
                "claude_code": {
                    "executable": str(self.claude_executable),
                    "credential_profile": "credential-claude",
                    "settings_profile": "settings-claude",
                    "allowed_model_ids": [CLAUDE_MODEL],
                },
            }
        )
        self.adapters = {
            "codex": InstalledAdapter("codex", "openai", "cloud", CAPABILITIES),
            "claude_code": InstalledAdapter(
                "claude_code", "anthropic", "cloud", CAPABILITIES
            ),
        }
        self.codex_inspector = RecordingInspector(
            self._observation(
                "openai",
                (CODEX_MODEL, CODEX_ALIAS),
                {CODEX_MODEL: 131072, CODEX_ALIAS: 131072},
                "credential-codex",
                "settings-codex",
                aliases=(CODEX_ALIAS,),
            )
        )
        self.claude_inspector = RecordingInspector(
            self._observation(
                "anthropic",
                (CLAUDE_MODEL,),
                {CLAUDE_MODEL: 200000},
                "credential-claude",
                "settings-claude",
            )
        )
        self.profile_fingerprints = {
            "credential-codex": "1" * 64,
            "settings-codex": "2" * 64,
            "credential-claude": "3" * 64,
            "settings-claude": "4" * 64,
        }
        self.preflight = self._preflight()
        self.provider, self.snapshot = self._process()
        requirements = RouteRequirements(CAPABILITIES, ("local_ai_box", "cloud"), 32768)
        self.requirements = {
            "architect": requirements,
            "fidelity_reviewer": requirements,
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _executable(self, name: str) -> Path:
        path = self.root / name
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o700)
        return path

    def _observation(
        self,
        provider,
        models,
        contexts,
        credential,
        settings,
        *,
        aliases=(),
    ):
        return AdapterObservation(
            available=True,
            tool_version="1.2.3",
            provider=provider,
            model_ids=models,
            alias_model_ids=aliases,
            capabilities=CAPABILITIES,
            location="cloud",
            context_limits=contexts,
            authenticated=True,
            credential_profile=credential,
            settings_profile=settings,
            structured_output=True,
            exact_model_enforcement=True,
            substitution_disabled=True,
            configuration_hash="expected",
        )

    def _preflight(self):
        return AgentRoutePreflight(
            self.routes,
            {
                "codex": (self.adapters["codex"], self.codex_inspector),
                "claude_code": (self.adapters["claude_code"], self.claude_inspector),
            },
            credential_fingerprint=lambda reference: self.profile_fingerprints.get(reference),
            settings_fingerprint=lambda reference: self.profile_fingerprints.get(reference),
        )

    def _process(self):
        policies = {
            "initiation": "registration_intake_or_idle_update",
            "agent_session": "fixed_assignment_followups",
            "saved_outputs": "versioned_registration_package",
            "review": "bounded_independent_fidelity",
            "confirmation": "explicit_exact_candidate_activation",
            "recovery": "reconcile_preserved_registration",
        }
        provider = ProcessProvider(
            name="registration",
            bundle_reference="registration-process@1",
            validator=lambda definition: None,
            handlers={section: {policy: lambda snapshot: None} for section, policy in policies.items()},
            routes=("registration.start",),
            required_outputs=("registration_package",),
        )
        registry = ProcessHandlerRegistry()
        registry.register(provider)
        provider = registry.provider("registration")
        definition = {
            "agent_session": {
                "policy": "fixed_assignment_followups",
                "architect_role": "project_architect",
                "reviewer_role": "fidelity_reviewer",
            }
        }
        encoded = canonical_json(definition)
        snapshot = ProcessSnapshot(
            "registration",
            encoded,
            hashlib.sha256(encoded.encode()).hexdigest(),
            BundleSnapshot("registration-process@1", "processDefinition", (("schema.json", "0" * 64),)),
        )
        return provider, snapshot

    def test_process_caller_resolves_separate_exact_role_routes(self) -> None:
        resolved = self.preflight.resolve_process_roles(
            self.provider,
            self.snapshot,
            RoleSelections(
                ToolModelSelection("codex", CODEX_MODEL),
                ToolModelSelection("claude_code", CLAUDE_MODEL),
            ),
            self.requirements,
        )

        self.assertEqual(resolved.architect.requested_model_id, CODEX_MODEL)
        self.assertEqual(resolved.architect.provider, "openai")
        self.assertEqual(resolved.fidelity_reviewer.requested_model_id, CLAUDE_MODEL)
        self.assertEqual(resolved.fidelity_reviewer.provider, "anthropic")
        self.assertNotEqual(
            resolved.architect.configuration_hash,
            resolved.fidelity_reviewer.configuration_hash,
        )
        self.assertEqual(len(self.codex_inspector.calls), 1)
        self.assertEqual(len(self.claude_inspector.calls), 1)

        identity = RunningToolIdentity(
            "tool_metadata",
            "openai",
            CODEX_MODEL,
            "1.2.3",
            resolved.architect.configuration_hash,
        )
        self.assertIs(verify_running_identity(resolved.architect, identity), identity)

    def test_alias_or_unknown_model_is_rejected_without_fallback(self) -> None:
        with self.assertRaises(AgentRouteError) as caught:
            self.preflight.resolve(
                "architect",
                ToolModelSelection("codex", CODEX_ALIAS),
                self.requirements["architect"],
            )
        self.assertEqual(caught.exception.code, "model_alias")
        self.assertEqual(len(self.codex_inspector.calls), 1)
        self.assertEqual(len(self.claude_inspector.calls), 0)

        with self.assertRaises(AgentRouteError) as caught:
            self.preflight.resolve(
                "architect",
                ToolModelSelection("codex", "openai/not-configured-2026-01-01"),
                self.requirements["architect"],
            )
        self.assertEqual(caught.exception.code, "model_not_allowed")
        self.assertEqual(len(self.codex_inspector.calls), 1)
        self.assertEqual(len(self.claude_inspector.calls), 0)

    def test_unavailable_transport_or_profile_blocks_before_adapter_probe(self) -> None:
        self.codex_executable.chmod(0o600)
        with self.assertRaises(AgentRouteError) as caught:
            self.preflight.resolve(
                "architect",
                ToolModelSelection("codex", CODEX_MODEL),
                self.requirements["architect"],
            )
        self.assertEqual(caught.exception.code, "transport_unavailable")
        self.assertEqual(self.codex_inspector.calls, [])

        self.codex_executable.chmod(0o700)
        del self.profile_fingerprints["credential-codex"]
        with self.assertRaises(AgentRouteError) as caught:
            self.preflight.resolve(
                "architect",
                ToolModelSelection("codex", CODEX_MODEL),
                self.requirements["architect"],
            )
        self.assertEqual(caught.exception.code, "credential_unavailable")
        self.assertEqual(self.codex_inspector.calls, [])

    def test_live_unavailability_identity_and_enforcement_fail_closed(self) -> None:
        failures = (
            (replace(self.codex_inspector.observation, available=False, reason="offline"), "transport_unavailable"),
            (replace(self.codex_inspector.observation, provider="other"), "identity_mismatch"),
            (replace(self.codex_inspector.observation, capabilities=("code_edit",)), "capability_mismatch"),
            (replace(self.codex_inspector.observation, model_ids=()), "model_unavailable"),
            (replace(self.codex_inspector.observation, authenticated=False), "authentication_failed"),
            (replace(self.codex_inspector.observation, structured_output=False), "capability_missing"),
            (replace(self.codex_inspector.observation, substitution_disabled=False), "model_not_enforceable"),
            (replace(self.codex_inspector.observation, configuration_hash="f" * 64), "configuration_changed"),
        )
        original = self.codex_inspector.observation
        for observation, code in failures:
            with self.subTest(code=code):
                self.codex_inspector.observation = observation
                with self.assertRaises(AgentRouteError) as caught:
                    self.preflight.resolve(
                        "architect",
                        ToolModelSelection("codex", CODEX_MODEL),
                        self.requirements["architect"],
                    )
                self.assertEqual(caught.exception.code, code)
        self.codex_inspector.observation = original
        self.assertEqual(len(self.claude_inspector.calls), 0)

    def test_capability_location_and_context_requirements_are_enforced(self) -> None:
        cases = (
            (
                RouteRequirements(("code_edit", "unsupported_capability"), ("cloud",), 32768),
                "capability_missing",
            ),
            (RouteRequirements(("code_edit",), ("local_ai_box",), 32768), "location_not_allowed"),
            (RouteRequirements(("code_edit",), ("cloud",), 200000), "context_insufficient"),
        )
        for requirements, code in cases:
            with self.subTest(code=code), self.assertRaises(AgentRouteError) as caught:
                self.preflight.resolve(
                    "architect", ToolModelSelection("codex", CODEX_MODEL), requirements
                )
            self.assertEqual(caught.exception.code, code)

    def test_running_identity_must_be_tool_metadata_and_match_exact_route(self) -> None:
        resolved = self.preflight.resolve(
            "architect",
            ToolModelSelection("codex", CODEX_MODEL),
            self.requirements["architect"],
        )
        failures = (
            RunningToolIdentity(
                "agent_text", "openai", CODEX_MODEL, "1.2.3", resolved.configuration_hash
            ),
            RunningToolIdentity(
                "tool_metadata",
                "openai",
                "openai/different-model-2026-01-01",
                "1.2.3",
                resolved.configuration_hash,
            ),
            RunningToolIdentity(
                "tool_metadata", "openai", CODEX_MODEL, "1.2.4", resolved.configuration_hash
            ),
        )
        for identity in failures:
            with self.subTest(identity=identity), self.assertRaises(AgentRouteError):
                verify_running_identity(resolved, identity)

    def test_profile_change_produces_a_new_configuration_identity(self) -> None:
        first = self.preflight.resolve(
            "architect",
            ToolModelSelection("codex", CODEX_MODEL),
            self.requirements["architect"],
        )
        self.profile_fingerprints["credential-codex"] = "9" * 64
        second = self.preflight.resolve(
            "architect",
            ToolModelSelection("codex", CODEX_MODEL),
            self.requirements["architect"],
        )
        self.assertNotEqual(first.configuration_hash, second.configuration_hash)
        old_identity = RunningToolIdentity(
            "tool_metadata", "openai", CODEX_MODEL, "1.2.3", first.configuration_hash
        )
        with self.assertRaises(AgentRouteError) as caught:
            verify_running_identity(second, old_identity)
        self.assertEqual(caught.exception.code, "identity_mismatch")

    def test_process_operation_routes_do_not_mask_explicit_tool_selections(self) -> None:
        self.assertEqual(self.provider.routes, ("registration.start",))
        resolved = self.preflight.resolve_process_roles(
            self.provider,
            self.snapshot,
            RoleSelections(
                ToolModelSelection("codex", CODEX_MODEL),
                ToolModelSelection("claude_code", CLAUDE_MODEL),
            ),
            self.requirements,
        )
        self.assertEqual(resolved.architect.tool, "codex")
        self.assertEqual(resolved.fidelity_reviewer.tool, "claude_code")
        self.assertEqual(len(self.codex_inspector.calls), 1)
        self.assertEqual(len(self.claude_inspector.calls), 1)

    def test_both_explicit_selections_are_required(self) -> None:
        with self.assertRaises(AgentRouteError) as caught:
            RoleSelections(ToolModelSelection("codex", CODEX_MODEL), None)  # type: ignore[arg-type]
        self.assertEqual(caught.exception.code, "missing_selection")

    def test_closed_configuration_rejects_unknown_fields_and_tools(self) -> None:
        with self.assertRaises(AgentRouteError) as caught:
            AgentRouteRegistry.from_mapping(
                {
                    "codex": {
                        "executable": str(self.codex_executable),
                        "credential_profile": "credential-codex",
                        "settings_profile": "settings-codex",
                        "allowed_model_ids": [CODEX_MODEL],
                        "default_model": CODEX_MODEL,
                    }
                }
            )
        self.assertEqual(caught.exception.code, "unknown_field")

        with self.assertRaises(AgentRouteError) as caught:
            ToolModelSelection("qwen", "qwen/model")
        self.assertEqual(caught.exception.code, "unsupported_tool")


if __name__ == "__main__":
    unittest.main()
