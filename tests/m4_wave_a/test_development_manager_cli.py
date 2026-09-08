"""`maestro development-manager-loop` -- the real, actually-startable
entrypoint for the M4 driver loop, exercised as a real subprocess
against a real fixture-built runtime dir."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ClaimedPacketFixture  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MAESTRO_SRC = REPO_ROOT / "services" / "maestro"


class DevelopmentManagerCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

    def tearDown(self):
        self.fixture.close()

    def test_a_real_cycle_runs_once_over_the_cli_and_prints_a_real_report(self):
        target = self.fixture.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real change\n")
        head = self.fixture.repository.commit_all("real owned-path change")
        self.fixture.finish_succeeded(head)

        result = subprocess.run(
            [
                sys.executable, "-m", "maestro.cli", "development-manager-loop",
                "--run-id", "run-1", "--repository", str(self.fixture.repository.path),
                "--default-branch", "main", "--reconstruction-command", "echo reconstruct",
                "--runtime-dir", str(self.fixture.config.runtime_dir),
            ],
            cwd=str(MAESTRO_SRC), env={"PYTHONPATH": str(MAESTRO_SRC), "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["reviewed"], ["packet-1"])

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(packet["state"], "AwaitingReview")


if __name__ == "__main__":
    unittest.main()
