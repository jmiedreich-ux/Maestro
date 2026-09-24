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
CODEX_DESTINATIONS = (
    {"hostname": "api.openai.com", "port": 443},
    {"hostname": "chatgpt.com", "port": 443},
)
CLAUDE_DESTINATIONS = ({"hostname": "api.anthropic.com", "port": 443},)


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
                    "permitted_destinations": list(CODEX_DESTINATIONS),
                },
                "claude_code": {
                    "executable": str(self.claude_executable),
                    "credential_profile": "credential-claude",
                    "settings_profile": "settings-claude",
                    "allowed_model_ids": [CLAUDE_MODEL],
                    "permitted_destinations": list(CLAUDE_DESTINATIONS),
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
        self.assertEqual(
            tuple(
                (destination.hostname, destination.port)
                for destination in resolved.architect.permitted_destinations
            ),
            (("api.openai.com", 443), ("chatgpt.com", 443)),
        )
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

    def test_destination_change_produces_a_new_configuration_identity(self) -> None:
        first = self.preflight.resolve(
            "architect",
            ToolModelSelection("codex", CODEX_MODEL),
            self.requirements["architect"],
        )
        self.routes = AgentRouteRegistry.from_mapping(
            {
                "codex": {
                    "executable": str(self.codex_executable),
                    "credential_profile": "credential-codex",
                    "settings_profile": "settings-codex",
                    "allowed_model_ids": [CODEX_MODEL, CODEX_ALIAS],
                    "permitted_destinations": [
                        {"hostname": "api.openai.com", "port": 8443}
                    ],
                }
            }
        )
        second = self._preflight().resolve(
            "architect",
            ToolModelSelection("codex", CODEX_MODEL),
            self.requirements["architect"],
        )
        self.assertNotEqual(first.configuration_hash, second.configuration_hash)
        self.assertEqual(second.permitted_destinations[0].port, 8443)

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
                        "permitted_destinations": list(CODEX_DESTINATIONS),
                        "default_model": CODEX_MODEL,
                    }
                }
            )
        self.assertEqual(caught.exception.code, "unknown_field")

        with self.assertRaises(AgentRouteError) as caught:
            ToolModelSelection("gemini", "gemini/model")
        self.assertEqual(caught.exception.code, "unsupported_tool")
        self.assertEqual(ToolModelSelection("qwen", "qwen3.6:27b").tool, "qwen")

    def test_destination_policy_rejects_absent_empty_wildcard_and_malformed_entries(self) -> None:
        base = {
            "executable": str(self.codex_executable),
            "credential_profile": "credential-codex",
            "settings_profile": "settings-codex",
            "allowed_model_ids": [CODEX_MODEL],
            "permitted_destinations": list(CODEX_DESTINATIONS),
        }
        cases = (
            (
                {
                    key: value
                    for key, value in base.items()
                    if key != "permitted_destinations"
                },
                "missing_field",
            ),
            ({**base, "permitted_destinations": []}, "invalid_configuration"),
            (
                {**base, "permitted_destinations": [{"hostname": "*.openai.com", "port": 443}]},
                "invalid_configuration",
            ),
            (
                {**base, "permitted_destinations": [{"hostname": "API.OPENAI.COM", "port": 443}]},
                "invalid_configuration",
            ),
            (
                {
                    **base,
                    "permitted_destinations": [
                        {"hostname": "https://api.openai.com", "port": 443}
                    ],
                },
                "invalid_configuration",
            ),
            (
                {**base, "permitted_destinations": [{"hostname": "api.openai.com", "port": True}]},
                "invalid_configuration",
            ),
            (
                {**base, "permitted_destinations": [{"hostname": "api.openai.com", "port": 0}]},
                "invalid_configuration",
            ),
            (
                {
                    **base,
                    "permitted_destinations": [
                        CODEX_DESTINATIONS[0],
                        CODEX_DESTINATIONS[0],
                    ],
                },
                "invalid_configuration",
            ),
        )
        for configuration, code in cases:
            with self.subTest(configuration=configuration), self.assertRaises(
                AgentRouteError
            ) as caught:
                AgentRouteRegistry.from_mapping({"codex": configuration})
            self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()


class EnvironmentPreflightTests(unittest.TestCase):
    """Unit checks of the aggregate preflight logic. These use fake executables and
    prove report shape only; they are not evidence that the real host is ready."""

    def setUp(self) -> None:
        import subprocess

        from maestro.agents import preflight

        self.preflight = preflight
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        for command in (
            ["git", "init", "-q", "-b", "main"],
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
             "commit", "-q", "--allow-empty", "-m", "seed"],
        ):
            subprocess.run(command, cwd=self.repo, check=True, capture_output=True)
        self.workspaces = self.root / "workspaces"
        self.workspaces.mkdir()
        self.executable = self.root / "fake-claude"
        self.executable.write_text("#!/bin/sh\necho '9.9.9 (Fake Claude)'\n")
        self.executable.chmod(0o755)
        self.config = self.root / "agents.toml"
        self.config.write_text(
            "[tools.claude_code]\n"
            f'executable = "{self.executable}"\n'
            'credential_profile = "claude_max"\n'
            'settings_profile = "claude_max_v1"\n'
            'allowed_model_ids = ["claude-opus-4-6"]\n'
            'permitted_destinations = [{ hostname = "api.anthropic.com", port = 443 }]\n'
        )
        self.credential = self.root / "credentials.json"
        self.write_credential(expires_at=4_000_000_000_000)

    def write_credential(self, *, expires_at: int) -> None:
        import json

        self.credential.write_text(
            json.dumps(
                {"claudeAiOauth": {"accessToken": "SECRET-TOKEN-VALUE", "refreshToken": "SECRET-REFRESH", "expiresAt": expires_at}}
            )
        )

    def profile(self, **changes):
        base = dict(
            name="test feature",
            repository=self.repo,
            revision="HEAD",
            agents_config=self.config,
            workspace_root=self.workspaces,
            tools=(("claude_code", "claude-opus-4-6"),),
            credential_files={"claude_code": self.credential},
        )
        base.update(changes)
        return self.preflight.FeatureProfile(**base)

    def probes(self, *, now_ms: int = 1_000_000_000_000, repo=None, app=None):
        real = self.preflight.host_probes()
        return self.preflight.EnvironmentProbes(
            real.run, lambda: now_ms, lambda path: repo, lambda: app
        )

    def missing(self, report) -> set[str]:
        return {f"{r.category}/{r.check}" for r in report.blocking}

    def test_every_category_is_reported_even_when_all_targets_are_absent(self) -> None:
        profile = self.profile(
            repository=self.root / "no-repo",
            agents_config=self.root / "no-agents.toml",
            workspace_root=self.root / "no-workspaces",
            credential_files={},
        )
        report = self.preflight.run_environment_preflight(profile, self.probes())
        self.assertEqual(
            {r.category for r in report.results}, set(self.preflight.ENVIRONMENT_CATEGORIES)
        )
        self.assertFalse(report.passed)
        missing = self.missing(report)
        self.assertIn("source_and_workspace/repository", missing)
        self.assertIn("agent_routes/agents_toml", missing)
        self.assertIn("source_and_workspace/workspace_root", missing)
        self.assertGreaterEqual(len(report.blocking), 3)
        for category in self.preflight.ENVIRONMENT_CATEGORIES:
            self.assertIn(f"[{category}]", report.render())

    def test_baseline_passes_and_service_checks_are_excluded_with_a_reason(self) -> None:
        report = self.preflight.run_environment_preflight(self.profile(), self.probes())
        self.assertEqual(self.missing(report), set(), report.render())
        excluded = [r for r in report.results if r.status == self.preflight.EXCLUDED]
        self.assertTrue(excluded)
        self.assertTrue(all(r.detail for r in excluded))

    def test_removed_prerequisite_blocks_and_restoring_it_passes_again(self) -> None:
        self.executable.chmod(0o644)
        blocked = self.preflight.run_environment_preflight(self.profile(), self.probes())
        self.assertIn("agent_routes/claude_code_executable", self.missing(blocked))
        self.assertIn("claude_code_executable", blocked.render())
        self.executable.chmod(0o755)
        restored = self.preflight.run_environment_preflight(self.profile(), self.probes())
        self.assertTrue(restored.passed, restored.render())

    def test_expired_claude_oauth_is_reported_without_printing_secrets(self) -> None:
        self.write_credential(expires_at=1_000)
        report = self.preflight.run_environment_preflight(self.profile(), self.probes())
        self.assertIn("identity_and_credentials/claude_oauth", self.missing(report))
        rendered = report.render() + str(report.as_dict())
        self.assertIn("expired", rendered)
        self.assertNotIn("SECRET", rendered)

    def test_dirty_checkout_is_reported(self) -> None:
        (self.repo / "untracked.txt").write_text("x")
        report = self.preflight.run_environment_preflight(self.profile(), self.probes())
        self.assertIn("source_and_workspace/clean_checkout", self.missing(report))

    def test_bare_mirror_has_no_working_tree_to_be_dirty(self) -> None:
        import subprocess

        bare = self.root / "mirror.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(self.repo), str(bare)], check=True, capture_output=True)
        report = self.preflight.run_environment_preflight(
            self.profile(repository=bare), self.probes()
        )
        self.assertNotIn("source_and_workspace/clean_checkout", self.missing(report))
        self.assertEqual(self.missing(report), set(), report.render())

    def test_github_administration_and_protected_branch_are_separate_checks(self) -> None:
        repo = {"private": True, "permissions": {"pull": True, "push": True}}
        profile = self.profile(
            github_repository="owner/name",
            require_app_administration_read=True,
            require_protected_branch=True,
        )
        report = self.preflight.run_environment_preflight(
            profile, self.probes(repo=repo, app={"administration": "write"})
        )
        missing = self.missing(report)
        self.assertNotIn("github_and_test_targets/app_administration_read", missing)
        self.assertNotIn("github_and_test_targets/write_access", missing)
        self.assertIn("github_and_test_targets/protected_branch_case", missing)
        no_admin = self.preflight.run_environment_preflight(
            profile, self.probes(repo=repo, app={"contents": "write"})
        )
        self.assertIn("github_and_test_targets/app_administration_read", self.missing(no_admin))

    def test_service_required_feature_reports_an_inactive_service(self) -> None:
        report = self.preflight.run_environment_preflight(
            self.profile(needs_service=True),
            self.preflight.EnvironmentProbes(
                lambda command: (3, "inactive\n") if command[0] == "systemctl" else self.preflight.host_probes().run(command),
                lambda: 1_000_000_000_000,
                lambda path: None,
                lambda: None,
            ),
        )
        self.assertIn("service_and_network/service_state", self.missing(report))

    def test_local_qwen_route_needs_its_model_served_locally(self) -> None:
        node = self.root / "fake-node"
        node.write_text("#!/bin/sh\necho 'v22.0.0'\n")
        node.chmod(0o755)
        self.config.write_text(
            self.config.read_text()
            + "\n[tools.qwen]\n"
            + f'executable = "{node}"\n'
            + 'credential_profile = "local_ollama"\n'
            + 'settings_profile = "qwen_local_v1"\n'
            + 'allowed_model_ids = ["qwen3.6:27b"]\n'
            + 'permitted_destinations = [{ hostname = "127.0.0.1", port = 11434 }]\n'
        )
        settings = self.root / "qwen-settings.json"
        settings.write_text("{}")
        profile = self.profile(
            tools=(("qwen", "qwen3.6:27b"),), credential_files={"qwen": settings}
        )
        real = self.preflight.host_probes()

        def probes(models):
            def http_json(url):
                if url.endswith("/api/version"):
                    return {"version": "0.32.15"}
                return {"models": [{"name": name} for name in models]}

            return self.preflight.EnvironmentProbes(
                real.run, lambda: 1_000_000_000_000, lambda path: None, lambda: None, http_json
            )

        served = self.preflight.run_environment_preflight(profile, probes(["qwen3.6:27b"]))
        self.assertEqual(self.missing(served), set(), served.render())
        self.assertIn("qwen_backend", served.render())
        absent = self.preflight.run_environment_preflight(profile, probes(["other:1b"]))
        self.assertIn("agent_routes/qwen_backend", self.missing(absent))

    def test_progress_channel_needs_a_delivered_receipt(self) -> None:
        log = self.root / "receipts.log"
        log.write_text("")
        empty = self.preflight.run_environment_preflight(
            self.profile(progress_log=log, require_progress_channel=True), self.probes()
        )
        self.assertIn("observability_and_smoke/progress_channel", self.missing(empty))
        log.write_text("[2026-09-23T21:42:07-04:00] sent heartbeat\n")
        delivered = self.preflight.run_environment_preflight(self.profile(progress_log=log), self.probes())
        self.assertNotIn("observability_and_smoke/progress_channel", self.missing(delivered))
