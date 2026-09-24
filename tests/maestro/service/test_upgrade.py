from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "maestro_upgrade", ROOT / "services" / "maestro" / "deploy" / "upgrade.py"
)
upgrade_module = importlib.util.module_from_spec(_SPEC)
sys.modules["maestro_upgrade"] = upgrade_module
_SPEC.loader.exec_module(upgrade_module)

LAUNCHER_TEMPLATE = (
    '#!/usr/bin/env python3\n'
    'CONFIG = Path("@CONFIG_FILE@")\n'
    'PROFILE_ROOT = Path("@DATA_DIR@")\n'
    'SERVICE_USER = "@SERVICE_USER@"\n'
    '# template {version}\n'
)


class UpgradeTests(unittest.TestCase):
    """Proves the upgrade logic on isolated trees with fake host actions only."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.tmp = Path(self.temporary.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "master")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.invalid")
        self.old = self.commit("1", tag="passed/one")
        self.root = self.tmp / "host"
        self.target = upgrade_module.UpgradeTarget(root=self.root, owner_token=self.root / "owner.token")
        self.package = self.root / "site-packages" / "maestro"
        self.package.mkdir(parents=True)
        (self.package / "marker.txt").write_text("1")
        self.target.deploy_dir.mkdir(parents=True)
        (self.target.deploy_dir / "maestro-agent-egress").write_text(LAUNCHER_TEMPLATE.format(version="1"))
        for path in (self.target.under(self.target.config).parent, self.target.under(self.target.launcher).parent, self.target.under(self.target.data_dir)):
            path.mkdir(parents=True, exist_ok=True)
        self.config = self.target.under(self.target.config)
        self.config.write_text("configured = true\n")
        launcher = LAUNCHER_TEMPLATE.format(version="1").replace("@CONFIG_FILE@", "/etc/maestro/agents.toml").replace("@DATA_DIR@", "/var/lib/maestro").replace("@SERVICE_USER@", "maestro")
        for path in (self.target.under(self.target.launcher), self.target.under(self.target.runner)):
            path.write_text(launcher)
        self.database = self.target.database_files()[0]
        self.database.write_text("database-rows")
        (self.root / "owner.token").write_text("owner-secret\n")
        self.target.revision_file.parent.mkdir(parents=True, exist_ok=True)
        self.target.revision_file.write_text(self.old + "\n")
        self.state = {"active": True, "auth_status": 200, "install_error": False}

    def git(self, *arguments: str) -> str:
        return subprocess.run(["git", "-C", str(self.repo), *arguments], check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, version: str, *, tag: str | None = None) -> str:
        service = self.repo / "services" / "maestro"
        (service / "deploy").mkdir(parents=True, exist_ok=True)
        (service / "marker.txt").write_text(version)
        (service / "deploy" / "maestro-agent-egress").write_text(LAUNCHER_TEMPLATE.format(version=version))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"version {version}")
        revision = self.git("rev-parse", "HEAD")
        if tag:
            self.git("tag", tag, revision)
        return revision

    def effects(self):
        state = self.state

        def run(command):
            if command[:2] == ["systemctl", "stop"]:
                state["active"] = False
            elif command[:2] == ["systemctl", "start"]:
                state["active"] = True
            elif command[:2] == ["systemctl", "is-active"]:
                return (0, "active\n") if state["active"] else (3, "inactive\n")
            return 0, ""

        def install_package(source):
            if state["install_error"]:
                raise upgrade_module.UpgradeError("package install failed")
            shutil.rmtree(self.package)
            self.package.mkdir()
            (self.package / "marker.txt").write_text((source / "marker.txt").read_text())
            shutil.copy2(source / "deploy" / "maestro-agent-egress", self.target.deploy_dir / "maestro-agent-egress")

        def http_status(url, token):
            if not token:
                return 401
            broken = (self.package / "marker.txt").read_text() == "2"
            return state["auth_status"] if broken else 200

        return upgrade_module.Effects(run, install_package, lambda: self.package, http_status, sleep=lambda seconds: None)

    def run_upgrade(self, revision):
        return upgrade_module.upgrade(self.repo, revision, self.target, self.effects())

    def test_upgrade_installs_only_code_and_keeps_configuration_and_data(self) -> None:
        new = self.commit("2", tag="passed/two")
        receipt = self.run_upgrade(new)
        self.assertEqual(receipt.outcome, "upgraded", receipt.checks)
        self.assertEqual((self.package / "marker.txt").read_text(), "2")
        self.assertIn("# template 2", self.target.under(self.target.launcher).read_text())
        self.assertIn('SERVICE_USER = "maestro"', self.target.under(self.target.launcher).read_text())
        self.assertEqual(self.config.read_text(), "configured = true\n")
        self.assertEqual(self.database.read_text(), "database-rows")
        self.assertEqual((self.root / "owner.token").read_text(), "owner-secret\n")
        self.assertEqual(upgrade_module.installed_revision(self.target), new)
        self.assertEqual(json.loads((Path(receipt.backup) / "receipt.json").read_text())["outcome"], "upgraded")

    def test_failed_smoke_check_restores_the_previous_installation(self) -> None:
        new = self.commit("2", tag="passed/two")
        self.state["auth_status"] = 500
        receipt = self.run_upgrade(new)
        self.assertEqual(receipt.outcome, "rolled_back")
        self.assertEqual((self.package / "marker.txt").read_text(), "1")
        self.assertIn("# template 1", self.target.under(self.target.launcher).read_text())
        self.assertIn("# template 1", (self.target.deploy_dir / "maestro-agent-egress").read_text())
        self.assertEqual(self.config.read_text(), "configured = true\n")
        self.assertEqual(upgrade_module.installed_revision(self.target), self.old)
        self.assertTrue(self.state["active"])
        self.assertIn("authenticated_read", {c["check"] for c in receipt.checks if c["status"] == "fail"})

    def test_failed_install_restores_the_previous_installation(self) -> None:
        new = self.commit("2", tag="passed/two")
        self.state["install_error"] = True
        receipt = self.run_upgrade(new)
        self.assertEqual(receipt.outcome, "rolled_back")
        self.assertEqual((self.package / "marker.txt").read_text(), "1")
        self.assertEqual(upgrade_module.installed_revision(self.target), self.old)

    def test_only_an_exact_passed_revision_on_master_is_installable(self) -> None:
        untagged = self.commit("2")
        with self.assertRaises(upgrade_module.UpgradeError):
            self.run_upgrade(untagged)
        with self.assertRaises(upgrade_module.UpgradeError):
            self.run_upgrade(untagged[:12])
        self.git("switch", "-q", "-c", "side", self.old)
        side = self.commit("3", tag="passed/side")
        self.git("switch", "-q", "master")
        with self.assertRaises(upgrade_module.UpgradeError):
            self.run_upgrade(side)
        self.assertEqual((self.package / "marker.txt").read_text(), "1")
        self.assertTrue(self.state["active"])

    def test_reinstalling_the_installed_revision_changes_nothing(self) -> None:
        receipt = self.run_upgrade(self.old)
        self.assertEqual(receipt.outcome, "already_installed")

    def test_watch_picks_the_newest_passed_revision_on_master_only(self) -> None:
        self.assertEqual(upgrade_module.latest_passed_revision(self.repo), self.old)
        self.git("switch", "-q", "-c", "side", self.old)
        self.commit("9", tag="passed/side")
        self.git("switch", "-q", "master")
        self.assertEqual(upgrade_module.latest_passed_revision(self.repo), self.old)
        new = self.commit("2", tag="passed/two")
        self.assertEqual(upgrade_module.latest_passed_revision(self.repo), new)


if __name__ == "__main__":
    unittest.main()
