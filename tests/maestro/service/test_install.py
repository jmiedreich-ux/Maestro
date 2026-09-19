from __future__ import annotations

import hashlib
import importlib
import importlib.util
import io
import json
import os
import pwd
import sqlite3
import stat
import sys
import tempfile
import threading
import tomllib
import types
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "maestro"))

from maestro.service.activities import ProjectRecord
from maestro.service.main import (
    InstalledServiceServer,
    ServiceConfigurationError,
    build_application,
    load_settings,
    main,
)
from maestro.service.registry import (
    OperationHandler,
    OperationRegistry,
    OperationResult,
    PreparedOperation,
)
from maestro.service.requests import RequestService
from maestro.terminal.connection import TerminalConnection


OWNER_TOKEN = "a" * 64
INSTALLER_PATH = ROOT / "services" / "maestro" / "deploy" / "install.py"
UNIT_PATH = ROOT / "services" / "maestro" / "deploy" / "maestro.service"
PYPROJECT_PATH = ROOT / "services" / "maestro" / "pyproject.toml"
EGRESS_HELPER_PATH = ROOT / "services" / "maestro" / "deploy" / "maestro-agent-egress"
EGRESS_SUDOERS_PATH = (
    ROOT / "services" / "maestro" / "deploy" / "maestro-agent-egress.sudoers"
)


def _load_installer():
    specification = importlib.util.spec_from_file_location("maestro_deploy_install", INSTALLER_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


installer = _load_installer()


def _saved_request(_request) -> PreparedOperation:
    return PreparedOperation(
        entity_id="installation-restart-proof",
        event_type="installation.request_saved",
        event_data={"saved": True},
        apply=lambda _transaction, _version: OperationResult(data={"saved": True}),
    )


class LinuxInstallationTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.operator_home = self.root / "home" / "operator"
        self.operator_home.mkdir(parents=True)
        self.schema_source = self.root / "package" / "schemas" / "sample" / "1"
        self.schema_source.mkdir(parents=True)
        (self.schema_source / "schema.json").write_text(
            '{"$schema":"https://json-schema.org/draft/2020-12/schema"}',
            encoding="utf-8",
        )
        self.paths = installer.InstallationPaths.build(self.root, self.operator_home)
        self.configuration = installer.Installation(
            paths=self.paths,
            operator=installer.Account("operator", 1100, 1100),
            service=installer.Account("maestro", 1101, 1101),
            agent=installer.Account("maestro-agent", 1102, 1102),
            service_executable=Path("/opt/maestro/bin/maestro-service"),
            owner_id="owner-local",
            port=8787,
            schema_sources=(self.schema_source,),
            production=False,
        )

    def install(self) -> None:
        with mock.patch.object(installer.secrets, "token_hex", return_value=OWNER_TOKEN):
            installer.install(self.configuration)

    def test_staged_install_has_exact_paths_permissions_and_no_plaintext_service_secret(self) -> None:
        self.install()

        token = self.paths.owner_token.read_text(encoding="ascii")
        service_config = self.paths.config_file.read_text(encoding="utf-8")
        cli_config = self.paths.cli_config.read_text(encoding="utf-8")
        unit = self.paths.unit_file.read_text(encoding="utf-8")
        egress_helper = installer._render_egress_helper(
            EGRESS_HELPER_PATH.read_text(encoding="utf-8"),
            config_file=self.paths.config_file,
            data_dir=self.paths.data_dir,
            service_user=self.configuration.service.name,
        )
        egress_sudoers = installer._render_egress_sudoers(
            EGRESS_SUDOERS_PATH.read_text(encoding="utf-8"),
            self.configuration.service.name,
        )

        self.assertEqual(OWNER_TOKEN, token)
        self.assertEqual(0o600, stat.S_IMODE(self.paths.owner_token.stat().st_mode))
        self.assertEqual(0o700, stat.S_IMODE(self.paths.operator_config_dir.stat().st_mode))
        self.assertEqual(0o640, stat.S_IMODE(self.paths.config_file.stat().st_mode))
        self.assertEqual(0o711, stat.S_IMODE(self.paths.workspace_dir.stat().st_mode))
        self.assertEqual(
            self.root / "usr" / "local" / "libexec" / "maestro-agent-egress",
            self.paths.egress_launcher,
        )
        self.assertEqual(
            self.root / "usr" / "local" / "libexec" / "maestro-agent-egress-run",
            self.paths.egress_runner,
        )
        self.assertEqual(
            self.root / "etc" / "sudoers.d" / "maestro-agent-egress",
            self.paths.egress_sudoers,
        )
        self.assertEqual(
            egress_helper, self.paths.egress_launcher.read_text(encoding="utf-8")
        )
        self.assertEqual(
            egress_helper, self.paths.egress_runner.read_text(encoding="utf-8")
        )
        self.assertEqual(0o755, stat.S_IMODE(self.paths.egress_launcher.stat().st_mode))
        self.assertEqual(0o755, stat.S_IMODE(self.paths.egress_runner.stat().st_mode))
        self.assertEqual(
            egress_sudoers, self.paths.egress_sudoers.read_text(encoding="utf-8")
        )
        self.assertEqual(0o440, stat.S_IMODE(self.paths.egress_sudoers.stat().st_mode))
        self.assertEqual(
            "maestro ALL=(root) NOPASSWD: /usr/local/libexec/maestro-agent-egress *\n",
            egress_sudoers,
        )
        self.assertIn(f"CONFIG = Path({json.dumps(str(self.paths.config_file))})", egress_helper)
        self.assertIn(f"PROFILE_ROOT = Path({json.dumps(str(self.paths.data_dir))})", egress_helper)
        self.assertIn('SERVICE_USER = "maestro"', egress_helper)
        self.assertIn("--ro-bind-data", egress_helper)
        self.assertIn("--uid", egress_helper)
        self.assertNotIn("@", egress_helper)
        self.assertNotIn(OWNER_TOKEN, service_config)
        self.assertIn(hashlib.sha256(OWNER_TOKEN.encode("ascii")).hexdigest(), service_config)
        self.assertIn(str(self.paths.owner_token), cli_config)
        self.assertIn("User=maestro", unit)
        self.assertIn("Restart=on-failure", unit)
        self.assertIn("ProtectHome=true", unit)
        self.assertNotIn("@", unit)
        self.assertTrue((self.paths.schema_dir / "sample" / "1" / "schema.json").is_file())
        self.assertTrue((self.paths.schema_dir / installer.SCHEMA_MANIFEST_NAME).is_file())

        settings = load_settings(self.paths.config_file)
        self.assertEqual(self.paths.data_dir / "maestro.sqlite3", settings.storage.path)
        self.assertEqual("maestro-agent", settings.agent_user)
        build_application(settings)
        self.assertTrue(settings.storage.path.is_file())

    def test_real_loopback_read_survives_client_exit_and_service_restart(self) -> None:
        self.install()
        settings = load_settings(self.paths.config_file)
        application = build_application(settings)
        with application.database.transaction() as transaction:
            application.activities.create_project(
                transaction,
                ProjectRecord("project-saved", "Saved project", "ready", 1),
            )
        request_service = RequestService(
            application.database,
            application.authenticator,
            OperationRegistry((OperationHandler("registration.start", _saved_request),)),
        )
        request_service.submit(
            f"Bearer {OWNER_TOKEN}",
            {
                "request_id": "request-saved",
                "operation": "registration.start",
                "project_id": None,
                "activity_id": None,
                "question_id": None,
                "expected_version": None,
                "payload": {},
            },
        )

        first = self._start_server(application)
        try:
            with self.assertRaises(urllib.error.HTTPError) as rejected:
                urllib.request.urlopen(first + "/api/v1/workspace", timeout=2)
            self.assertEqual(401, rejected.exception.code)

            response = self._workspace(first)
            self.assertEqual("project-saved", response["data"]["projects"][0]["project_id"])
            self.paths.cli_config.write_text(
                f'service_url = "{first}"\n'
                f'owner_credential_file = "{self.paths.owner_token}"\n',
                encoding="utf-8",
            )
            self.paths.cli_config.chmod(0o600)
            metadata = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
            module_name, function_name = metadata["project"]["scripts"]["maestro"].split(":")
            terminal_entry = getattr(importlib.import_module(module_name), function_name)
            output = io.StringIO()
            self.assertEqual(
                0,
                terminal_entry(
                    argv=[],
                    connection_factory=lambda: TerminalConnection(
                        environ={
                            "XDG_CONFIG_HOME": str(self.operator_home / ".config")
                        }
                    ),
                    input_stream=io.StringIO("/exit\n"),
                    output_stream=output,
                ),
            )
            self.assertIn("service work continues", output.getvalue())
            # The installed terminal entry disconnected; service work remains reachable.
            self.assertEqual(200, self._workspace(first)["status"])
        finally:
            self._stop_server()

        second_application = build_application(settings)
        second = self._start_server(second_application)
        try:
            response = self._workspace(second)
            self.assertEqual("project-saved", response["data"]["projects"][0]["project_id"])
            receipt_request = urllib.request.Request(
                second + "/api/v1/requests/request-saved",
                headers={"Authorization": f"Bearer {OWNER_TOKEN}"},
            )
            with urllib.request.urlopen(receipt_request, timeout=2) as receipt_response:
                receipt = json.load(receipt_response)["receipt"]
            self.assertEqual("completed", receipt["status"])
            self.assertEqual({"saved": True}, receipt["result"])
        finally:
            self._stop_server()

    def test_bad_config_storage_and_schema_fail_before_readiness(self) -> None:
        self.install()
        malformed = self.root / "bad.toml"
        malformed.write_text("[owner\n", encoding="utf-8")
        malformed.chmod(0o600)
        with self.assertRaises(ServiceConfigurationError):
            load_settings(malformed)

        value = self.paths.config_file.read_text(encoding="utf-8")
        missing_storage = self.root / "missing-storage.toml"
        missing_storage.write_text(
            value.replace(str(self.paths.data_dir), str(self.root / "absent")),
            encoding="utf-8",
        )
        missing_storage.chmod(0o600)
        self.assertEqual(1, main(["--config", str(missing_storage), "--check-ready"]))

        unsupported = self.root / "unsupported.sqlite3"
        connection = sqlite3.connect(unsupported)
        connection.execute("CREATE TABLE unrelated(value TEXT)")
        connection.commit()
        connection.close()
        unsupported_config = self.root / "unsupported.toml"
        unsupported_config.write_text(
            value.replace(str(self.paths.data_dir / "maestro.sqlite3"), str(unsupported)),
            encoding="utf-8",
        )
        unsupported_config.chmod(0o600)
        self.assertEqual(1, main(["--config", str(unsupported_config), "--check-ready"]))
        with sqlite3.connect(unsupported) as check:
            self.assertEqual([("unrelated",)], check.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='unrelated'"
            ).fetchall())

        corrupt = self.root / "corrupt.sqlite3"
        corrupt.write_bytes(b"not a SQLite database")
        corrupt_config = self.root / "corrupt.toml"
        corrupt_config.write_text(
            value.replace(str(self.paths.data_dir / "maestro.sqlite3"), str(corrupt)),
            encoding="utf-8",
        )
        corrupt_config.chmod(0o600)
        self.assertEqual(1, main(["--config", str(corrupt_config), "--check-ready"]))

        linked = self.root / "linked-bundle"
        linked.symlink_to(self.schema_source, target_is_directory=True)
        broken = installer.Installation(
            **{**self.configuration.__dict__, "schema_sources": (linked,)}
        )
        with self.assertRaises(installer.InstallationError):
            installer.install(broken, replace=True)

    def test_safety_rejects_real_targets_and_collapsed_identities(self) -> None:
        outside = self.root.parent
        with self.assertRaises(installer.InstallationError):
            installer.InstallationPaths.build(self.root, outside)

        collapsed = installer.Installation(
            **{
                **self.configuration.__dict__,
                "agent": installer.Account("maestro-agent", 1101, 1102),
            }
        )
        with self.assertRaises(installer.InstallationError):
            collapsed.validate()

        supplementary = installer.Installation(
            **{
                **self.configuration.__dict__,
                "agent": installer.Account(
                    "maestro-agent", 1102, 1102, frozenset({1101})
                ),
            }
        )
        with self.assertRaisesRegex(
            installer.InstallationError, "supplementary member.*maestro"
        ):
            supplementary.validate()

        self.assertEqual(
            1,
            installer.main(
                [
                    "--root",
                    str(self.root),
                    "--operator-home",
                    str(self.operator_home),
                ]
            ),
        )
        self.assertFalse((self.root / "etc" / "maestro").exists())

    def test_credential_replacement_preserves_and_verifies_immutable_schemas(self) -> None:
        self.install()
        installed_schema = self.paths.schema_dir / "sample" / "1" / "schema.json"
        manifest = self.paths.schema_dir / installer.SCHEMA_MANIFEST_NAME
        original_schema = installed_schema.read_bytes()
        original_manifest = manifest.read_bytes()
        original_inode = installed_schema.stat().st_ino

        replacement_token = "b" * 64
        with mock.patch.object(
            installer.secrets, "token_hex", return_value=replacement_token
        ):
            installer.install(self.configuration, replace=True)

        service_config = self.paths.config_file.read_text(encoding="utf-8")
        self.assertEqual(replacement_token, self.paths.owner_token.read_text(encoding="ascii"))

        self.assertIn(
            hashlib.sha256(replacement_token.encode("ascii")).hexdigest(),
            service_config,
        )
        self.assertNotIn(OWNER_TOKEN, service_config)
        self.assertEqual(original_schema, installed_schema.read_bytes())
        self.assertEqual(original_manifest, manifest.read_bytes())
        self.assertEqual(original_inode, installed_schema.stat().st_ino)

        self.schema_source.joinpath("schema.json").write_text(
            '{"changed":true}', encoding="utf-8"
        )
        with self.assertRaisesRegex(installer.InstallationError, "conflicts"):
            installer.install(self.configuration, replace=True)
        self.assertEqual(replacement_token, self.paths.owner_token.read_text(encoding="ascii"))

        self.schema_source.joinpath("schema.json").write_bytes(original_schema)
        installed_schema.unlink()
        with self.assertRaisesRegex(installer.InstallationError, "conflict|missing"):
            installer.install(self.configuration, replace=True)
        self.assertEqual(replacement_token, self.paths.owner_token.read_text(encoding="ascii"))

    def test_installed_host_verifier_reports_unavailable_evidence_as_nonpassing(self) -> None:
        output = io.StringIO()
        completed = installer.subprocess.CompletedProcess([], 1, b"", b"unavailable")
        with (
            mock.patch.object(installer, "_account", side_effect=KeyError("missing")),
            mock.patch.object(installer.subprocess, "run", return_value=completed),
            mock.patch.object(installer.Path, "exists", return_value=False),
            redirect_stderr(output),
        ):
            result = installer.verify_installed_host(None)
        self.assertEqual(2, result)
        self.assertIn("UNTESTED:", output.getvalue())
        self.assertIn("--operator-user is required", output.getvalue())
        self.assertIn("controlled crash/restart", output.getvalue())

    def test_package_and_unit_publish_the_two_independent_entry_points(self) -> None:
        metadata = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
        scripts = metadata["project"]["scripts"]
        data_files = metadata["tool"]["setuptools"]["data-files"]
        package_data = metadata["tool"]["setuptools"]["package-data"]
        self.assertEqual("maestro.terminal.main:main", scripts["maestro"])
        self.assertEqual("maestro.service.main:main", scripts["maestro-service"])
        self.assertIn("deploy/maestro.service", data_files["share/maestro/deploy"])
        self.assertIn("deploy/maestro-agent-egress", data_files["share/maestro/deploy"])
        self.assertIn(
            "deploy/maestro-agent-egress.sudoers", data_files["share/maestro/deploy"]
        )
        self.assertIn("**/*.json", package_data["maestro"])
        unit = UNIT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("maestro.cli", unit)
        self.assertIn("WantedBy=multi-user.target", unit)

    def test_egress_runner_rejects_unapproved_caller_mounts(self) -> None:
        helper_source = installer._render_egress_helper(
            EGRESS_HELPER_PATH.read_text(encoding="utf-8"),
            config_file=self.paths.config_file,
            data_dir=self.paths.data_dir,
            service_user="maestro",
        )
        egress = types.ModuleType("guarded_maestro_agent_egress")
        exec(compile(helper_source, str(EGRESS_HELPER_PATH), "exec"), egress.__dict__)
        workspace = self.paths.workspace_dir / "project" / "activity" / "runs" / "run-guard"

        for mount in (
            ("--bind", "/etc/shadow", "/sandbox/shadow"),
            ("--ro-bind", "/etc/shadow", "/sandbox/shadow"),
            ("--bind-try", "/etc/shadow", "/sandbox/shadow"),
        ):
            with self.subTest(mount=mount), redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as failed:
                egress.profile_data_mounts(
                    [egress.BWRAP, *mount, "--", "/usr/bin/true"],
                    self.paths.workspace_dir,
                    "run-guard",
                    Path("/run/maestro/agent-egress/run-guard/hosts"),
                    "claude_code",
                    Path("/usr/bin/true"),
                )
            self.assertEqual(64, failed.exception.code)

        with mock.patch.object(egress, "_open_workspace_mount", side_effect=(57, 58)):
            rewritten, descriptors = egress.profile_data_mounts(
                [
                    egress.BWRAP,
                    "--ro-bind",
                    str(workspace / "source"),
                    str(workspace / "source"),
                    "--bind",
                    str(workspace / "output"),
                    str(workspace / "output"),
                    "--",
                    "/usr/bin/true",
                ],
                self.paths.workspace_dir,
                "run-guard",
                Path("/run/maestro/agent-egress/run-guard/hosts"),
                "claude_code",
                Path("/usr/bin/true"),
            )
        self.assertEqual((57, 58), descriptors)
        self.assertEqual("--ro-bind-fd", rewritten[1])
        self.assertEqual("--bind-fd", rewritten[4])

    def test_egress_launcher_passes_the_selected_route_to_the_runner(self) -> None:
        helper_source = installer._render_egress_helper(
            EGRESS_HELPER_PATH.read_text(encoding="utf-8"),
            config_file=self.paths.config_file,
            data_dir=self.paths.data_dir,
            service_user="maestro",
        )
        egress = types.ModuleType("guarded_maestro_agent_egress")
        exec(compile(helper_source, str(EGRESS_HELPER_PATH), "exec"), egress.__dict__)
        configuration = {
            "tools": {
                "codex": {
                    "permitted_destinations": [{"hostname": "api.openai.com", "port": 443}]
                }
            }
        }
        hosts = Path("/run/maestro/agent-egress/run-guard/hosts")
        with (
            mock.patch.object(egress, "load_configuration", return_value=configuration),
            mock.patch.object(egress, "load_agent_account"),
            mock.patch.object(egress, "resolve", return_value=([], [])),
            mock.patch.object(egress, "write_hosts", return_value=hosts),
        ):
            command = egress.outer_command(
                "codex", "run-guard", [egress.BWRAP, "--", "/configured/codex"]
            )
        runner = command.index(egress.RUNNER)
        self.assertEqual("codex", command[runner + 1])
        self.assertEqual("maestro-agent-run-guard", command[runner + 2])
        self.assertEqual(str(hosts), command[runner + 3])

    def test_egress_runner_allows_only_the_configured_tool_runtime_self_mounts(self) -> None:
        helper_source = installer._render_egress_helper(
            EGRESS_HELPER_PATH.read_text(encoding="utf-8"),
            config_file=self.paths.config_file,
            data_dir=self.paths.data_dir,
            service_user="maestro",
        )
        egress = types.ModuleType("guarded_maestro_agent_egress")
        exec(compile(helper_source, str(EGRESS_HELPER_PATH), "exec"), egress.__dict__)
        tool_directory = self.root / "generated-tools"
        tool_directory.mkdir()
        executable = tool_directory / "codex"
        companion = tool_directory / "codex-code-mode-host"
        sensitive = self.root / "service-data" / "agent-config.toml"
        sensitive.parent.mkdir()
        for path in (executable, companion, sensitive):
            path.write_text("fixture", encoding="ascii")
        executable.chmod(0o700)
        companion.chmod(0o700)
        configured_executable = egress.load_route_executable(
            {"tools": {"codex": {"executable": str(executable)}}}, "codex"
        )
        self.assertEqual(executable.resolve(), configured_executable)

        rewritten, descriptors = egress.profile_data_mounts(
            [
                egress.BWRAP,
                "--ro-bind",
                str(executable),
                str(executable),
                "--ro-bind",
                str(companion),
                str(companion),
                "--",
                str(executable),
            ],
            self.paths.workspace_dir,
            "run-guard",
            Path("/run/maestro/agent-egress/run-guard/hosts"),
            "codex",
            configured_executable,
        )
        self.assertEqual((), descriptors)
        self.assertEqual(str(executable), rewritten[2])
        self.assertEqual(str(companion), rewritten[5])

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failed:
            egress.profile_data_mounts(
                [
                    egress.BWRAP,
                    "--ro-bind",
                    str(executable),
                    str(executable),
                    "--ro-bind",
                    str(sensitive),
                    str(sensitive),
                    "--",
                    str(executable),
                ],
                self.paths.workspace_dir,
                "run-guard",
                Path("/run/maestro/agent-egress/run-guard/hosts"),
                "codex",
                configured_executable,
            )
        self.assertEqual(64, failed.exception.code)

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failed:
            egress.profile_data_mounts(
                [
                    egress.BWRAP,
                    "--ro-bind",
                    str(sensitive),
                    str(sensitive),
                    "--",
                    str(sensitive),
                ],
                self.paths.workspace_dir,
                "run-guard",
                Path("/run/maestro/agent-egress/run-guard/hosts"),
                "codex",
                configured_executable,
            )
        self.assertEqual(64, failed.exception.code)

    def test_egress_runner_rejects_agent_uid_alias_of_service(self) -> None:
        helper_source = installer._render_egress_helper(
            EGRESS_HELPER_PATH.read_text(encoding="utf-8"),
            config_file=self.paths.config_file,
            data_dir=self.paths.data_dir,
            service_user="maestro",
        )
        egress = types.ModuleType("guarded_maestro_agent_egress")
        exec(compile(helper_source, str(EGRESS_HELPER_PATH), "exec"), egress.__dict__)
        service = types.SimpleNamespace(pw_uid=2101)
        alias = types.SimpleNamespace(pw_uid=2101)
        with (
            mock.patch.object(
                egress.pwd,
                "getpwnam",
                side_effect=lambda name: {"maestro": service, "agent-alias": alias}[name],
            ),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as failed,
        ):
            egress.load_agent_account({"service": {"agent_user": "agent-alias"}})
        self.assertEqual(64, failed.exception.code)

    @unittest.skipUnless(os.geteuid() == 0, "requires a disposable root-owned staged test")
    def test_egress_runner_mounts_service_workspace_before_running_as_agent(self) -> None:
        """A root runner mounts service-only sources, then bwrap applies the agent identity."""
        # Use distinct host identities.  The service UID becomes unmapped in
        # Bubblewrap's user namespace, which is the real access regression.
        agent = pwd.getpwnam("daemon")
        service = pwd.getpwnam("nobody")
        # The agent cannot traverse the protected service-data parent.  The
        # root guard must therefore hand Bubblewrap only validated open
        # workspace descriptors, rather than relaxing this ancestor.
        os.chmod(self.root, 0o750)
        profile = self.paths.data_dir / ".codex" / "auth.json"
        profile.parent.mkdir(parents=True)
        profile.write_text("staged-profile", encoding="ascii")
        profile.chmod(0o600)
        os.chown(profile, service.pw_uid, service.pw_gid)
        workspace = self.paths.workspace_dir / "project" / "activity" / "runs" / "run-agent"
        profile_target = workspace / "scratch" / "home" / ".codex" / "auth.json"
        workspace.mkdir(parents=True)
        source_directory = workspace / "source"
        source_directory.mkdir(mode=0o505)
        source = source_directory / "service-owned-source.txt"
        source.write_text("assigned source", encoding="ascii")
        source.chmod(0o404)
        os.chown(source_directory, service.pw_uid, service.pw_gid)
        os.chown(source, service.pw_uid, service.pw_gid)
        input_directory = workspace / "input"
        input_directory.mkdir(mode=0o505)
        input_file = input_directory / "assigned-input.txt"
        input_file.write_text("assigned input", encoding="ascii")
        input_file.chmod(0o404)
        os.chown(input_directory, service.pw_uid, service.pw_gid)
        os.chown(input_file, service.pw_uid, service.pw_gid)
        assignment = workspace / "assignment.json"
        assignment.write_text('{"assignment":"exact"}', encoding="ascii")
        assignment.chmod(0o404)
        os.chown(assignment, service.pw_uid, service.pw_gid)
        # Service-owned workspace ancestors reveal no entries, but Bubblewrap
        # must be able to traverse this assigned run after its user-namespace
        # identity transition.
        for directory in (
            self.paths.workspace_dir,
            self.paths.workspace_dir / "project",
            self.paths.workspace_dir / "project" / "activity",
            self.paths.workspace_dir / "project" / "activity" / "runs",
            workspace,
        ):
            directory.chmod(0o701)
        evidence_directory = workspace / "output"
        evidence_directory.mkdir()
        evidence_directory.chmod(0o707)
        os.chown(evidence_directory, service.pw_uid, service.pw_gid)
        evidence = evidence_directory / "result.json"
        scratch_directory = workspace / "scratch"
        scratch_directory.mkdir()
        scratch_directory.chmod(0o707)
        os.chown(scratch_directory, service.pw_uid, service.pw_gid)
        scratch_evidence = scratch_directory / "result.txt"
        hosts = self.root / "hosts"
        hosts.write_text("127.0.0.1 localhost\n", encoding="ascii")
        configuration = self.root / "egress-agents.toml"
        executable = Path("/usr/bin/python3").resolve()
        configuration.write_text(
            f'workspace_root = "{self.paths.workspace_dir}"\n\n'
            '[service]\nagent_user = "daemon"\n\n'
            f'[tools.codex]\nexecutable = "{executable}"\n',
            encoding="utf-8",
        )
        configuration.chmod(0o600)
        database = self.paths.data_dir / "maestro.sqlite3"
        database.write_text("staged database", encoding="ascii")
        database.chmod(0o600)
        self.paths.owner_token.parent.mkdir(parents=True)
        self.paths.owner_token.write_text("staged owner credential", encoding="ascii")
        self.paths.owner_token.chmod(0o600)
        protected_targets = (
            str(configuration),
            str(database),
            str(self.paths.owner_token),
        )
        helper_source = installer._render_egress_helper(
            EGRESS_HELPER_PATH.read_text(encoding="utf-8"),
            config_file=configuration,
            data_dir=self.paths.data_dir,
            service_user="nobody",
        )
        egress = types.ModuleType("staged_maestro_agent_egress")
        exec(compile(helper_source, str(EGRESS_HELPER_PATH), "exec"), egress.__dict__)

        directories = {
            evidence_directory,
            Path("/protected"),
            profile_target.parent,
            source_directory,
            input_directory,
            scratch_directory,
        }
        for directory in tuple(directories):
            current = Path("/")
            for part in directory.parts[1:]:
                current /= part
                directories.add(current)
        child = (
            "import json, os, sys; from pathlib import Path; "
            "Path(sys.argv[1]).write_text(json.dumps({'uid': os.geteuid(), "
            "'profile': Path(sys.argv[3]).is_file() and bool(Path(sys.argv[3]).read_bytes()), "
            "'source': Path(sys.argv[4]).read_text(), 'input': Path(sys.argv[5]).read_text(), "
            "'assignment': Path(sys.argv[6]).read_text(), "
            "'denied': [not os.access(path, os.R_OK) for path in sys.argv[7:]]})); "
            "Path(sys.argv[2]).write_text('scratch writable')"
        )
        sandbox = [
            egress.BWRAP,
            "--unshare-user",
            "--unshare-pid",
            "--tmpfs",
            "/",
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--ro-bind",
            str(source_directory),
            str(source_directory),
            "--ro-bind",
            str(input_directory),
            str(input_directory),
            "--ro-bind",
            str(assignment),
            str(assignment),
            "--bind",
            str(evidence_directory),
            str(evidence_directory),
            "--bind",
            str(scratch_directory),
            str(scratch_directory),
            "--ro-bind",
            str(profile),
            str(profile_target),
        ]
        for directory in sorted(directories):
            sandbox.extend(("--dir", str(directory)))
        sandbox.extend(
            (
                "--",
                str(executable),
                "-c",
                child,
                str(evidence_directory / "result.json"),
                str(scratch_evidence),
                str(profile_target),
                str(source),
                str(input_file),
                str(assignment),
                *protected_targets,
            )
        )
        with (
            mock.patch.object(egress, "nft_apply"),
            mock.patch.object(egress, "nft_remove"),
            mock.patch.object(
                egress.sys,
                "argv",
                [
                    "maestro-agent-egress-run",
                    "codex",
                    "maestro-agent-run-agent",
                    str(hosts),
                    "127.0.0.1:443",
                    "--",
                    *sandbox,
                ],
            ),
            self.assertRaises(SystemExit) as completed,
        ):
            egress.run_inner()
        self.assertEqual(0, completed.exception.code)
        observed = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(agent.pw_uid, observed["uid"])
        self.assertTrue(observed["profile"])
        self.assertEqual("assigned source", observed["source"])
        self.assertEqual("assigned input", observed["input"])
        self.assertEqual('{"assignment":"exact"}', observed["assignment"])
        self.assertEqual([True, True, True], observed["denied"])
        self.assertEqual(0o505, stat.S_IMODE(source_directory.stat().st_mode))
        self.assertEqual(0o707, stat.S_IMODE(evidence_directory.stat().st_mode))
        self.assertEqual("scratch writable", scratch_evidence.read_text(encoding="ascii"))

    def _start_server(self, application) -> str:
        server = InstalledServiceServer(application, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.server = server
        self.server_thread = thread
        host, port = server.address
        return f"http://{host}:{port}"

    def _stop_server(self) -> None:
        self.server.shutdown()
        self.server_thread.join(timeout=3)
        self.assertFalse(self.server_thread.is_alive())

    @staticmethod
    def _workspace(base_url: str) -> dict[str, object]:
        request = urllib.request.Request(
            base_url + "/api/v1/workspace",
            headers={"Authorization": f"Bearer {OWNER_TOKEN}"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            value = json.load(response)
            value["status"] = response.status
            return value


if __name__ == "__main__":
    unittest.main()
