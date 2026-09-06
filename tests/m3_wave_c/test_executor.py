from __future__ import annotations

import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from maestro.executor import (
    ExecutorError,
    ExecutorPreflight,
    LocalQwenExecutorAdapter,
)


def _init_repo(path: Path) -> str:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@local"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "local-test"], cwd=path, check=True)
    (path / "README.md").write_text("real\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, check=True, capture_output=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, check=True, capture_output=True, text=True
    ).stdout.strip()


def _write_fake_worker(path: Path, script: str) -> Path:
    binary = path / "fake-worker.sh"
    binary.write_text(script)
    binary.chmod(binary.stat().st_mode | stat.S_IEXEC)
    return binary


class LocalQwenExecutorAdapterTests(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.worktree_path = Path(self._temporary.name) / "worktree"
        self.worktree_path.mkdir()
        self.base_commit = _init_repo(self.worktree_path)

    def tearDown(self):
        self._temporary.cleanup()

    def _preflight(self) -> ExecutorPreflight:
        return ExecutorPreflight(
            base_commit=self.base_commit,
            worktree_path=self.worktree_path,
            allowed_paths=("src/**",),
            forbidden_paths=("package.json",),
            model_identity="fake-worker-1",
        )

    def test_a_real_completed_attempt_with_a_commit_reports_the_real_diff(self):
        binary = _write_fake_worker(
            self.worktree_path.parent,
            "#!/bin/sh\n"
            f"cd {self.worktree_path}\n"
            "echo 'real content' > src-file.txt\n"
            "git add src-file.txt\n"
            "git commit -m 'real change' >/dev/null\n"
            "echo done\n",
        )
        adapter = LocalQwenExecutorAdapter(qwen_binary=str(binary))
        handle = adapter.submit(self._preflight(), "irrelevant for the fake worker")

        for _ in range(50):
            if not adapter.observe(handle).running:
                break
            time.sleep(0.05)

        observation = adapter.observe(handle)
        self.assertFalse(observation.running)
        self.assertEqual(observation.exit_code, 0)

        evidence = adapter.retrieve_evidence(handle, branch_name="feature/real")
        self.assertTrue(evidence.completed)
        self.assertEqual(evidence.changed_files, ("src-file.txt",))
        self.assertIsNotNone(evidence.commit_sha)
        self.assertNotEqual(evidence.commit_sha, self.base_commit)
        self.assertIn("done", evidence.raw_output)

    def test_an_attempt_that_makes_no_commit_reports_no_changed_files(self):
        binary = _write_fake_worker(
            self.worktree_path.parent, "#!/bin/sh\necho 'nothing to do'\n"
        )
        adapter = LocalQwenExecutorAdapter(qwen_binary=str(binary))
        handle = adapter.submit(self._preflight(), "irrelevant")

        for _ in range(50):
            if not adapter.observe(handle).running:
                break
            time.sleep(0.05)

        evidence = adapter.retrieve_evidence(handle, branch_name="feature/real")
        self.assertEqual(evidence.changed_files, ())
        self.assertIsNone(evidence.commit_sha)

    def test_a_real_nonzero_exit_is_reported_as_not_completed(self):
        binary = _write_fake_worker(self.worktree_path.parent, "#!/bin/sh\nexit 1\n")
        adapter = LocalQwenExecutorAdapter(qwen_binary=str(binary))
        handle = adapter.submit(self._preflight(), "irrelevant")

        for _ in range(50):
            if not adapter.observe(handle).running:
                break
            time.sleep(0.05)

        evidence = adapter.retrieve_evidence(handle, branch_name="feature/real")
        self.assertFalse(evidence.completed)

    def test_retrieve_evidence_before_finishing_raises(self):
        binary = _write_fake_worker(self.worktree_path.parent, "#!/bin/sh\nsleep 2\n")
        adapter = LocalQwenExecutorAdapter(qwen_binary=str(binary))
        handle = adapter.submit(self._preflight(), "irrelevant")
        try:
            with self.assertRaises(ExecutorError):
                adapter.retrieve_evidence(handle, branch_name="feature/real")
        finally:
            adapter.cancel(handle)

    def test_cancel_stops_a_real_running_process(self):
        binary = _write_fake_worker(self.worktree_path.parent, "#!/bin/sh\nsleep 30\n")
        adapter = LocalQwenExecutorAdapter(qwen_binary=str(binary))
        handle = adapter.submit(self._preflight(), "irrelevant")
        self.assertTrue(adapter.observe(handle).running)

        adapter.cancel(handle)
        for _ in range(50):
            if not adapter.observe(handle).running:
                break
            time.sleep(0.05)
        self.assertFalse(adapter.observe(handle).running)

    def test_observe_on_an_unknown_handle_raises(self):
        adapter = LocalQwenExecutorAdapter()
        with self.assertRaises(ExecutorError):
            adapter.observe("never-submitted")

    def test_submit_against_a_missing_worktree_raises(self):
        adapter = LocalQwenExecutorAdapter()
        preflight = ExecutorPreflight(
            base_commit=self.base_commit,
            worktree_path=self.worktree_path / "does-not-exist",
            allowed_paths=(),
            forbidden_paths=(),
            model_identity="fake-worker-1",
        )
        with self.assertRaises(ExecutorError):
            adapter.submit(preflight, "irrelevant")


if __name__ == "__main__":
    unittest.main()
