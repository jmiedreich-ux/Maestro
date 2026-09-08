"""M4.10 — perform_merge, driven against a real git repository with a
real divergent branch (not the single-branch-direct-commit shape the
other M4 fixtures use, since a real merge needs real divergence to
exercise)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))

from support import TemporaryProjectRepository, run_git  # noqa: E402

from maestro.merge_executor import MergeFailed, perform_merge  # noqa: E402


class MergeExecutorTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository()
        self.base = self.repository.commit

    def tearDown(self):
        self.repository.close()

    def _branch_from_base(self, branch_name: str) -> None:
        run_git(self.repository.path, "checkout", "-b", branch_name, self.base)

    def test_a_real_divergent_branch_merges_cleanly_into_default(self):
        self._branch_from_base("codex/feature-1")
        target = self.repository.path / "feature.txt"
        target.write_text("real feature work\n")
        feature_head = self.repository.commit_all("real feature commit")

        merge_commit = perform_merge(str(self.repository.path), "main", feature_head)

        self.assertNotEqual(merge_commit, feature_head)
        self.assertNotEqual(merge_commit, self.base)
        log = run_git(self.repository.path, "log", "--format=%H", "main").stdout.split()
        self.assertIn(feature_head, log)
        self.assertIn(merge_commit, log)
        checked_out = run_git(
            self.repository.path, "rev-parse", "--abbrev-ref", "HEAD"
        ).stdout.strip()
        self.assertEqual(checked_out, "main")

    def test_a_head_already_reachable_from_default_returns_the_real_current_tip_unchanged(self):
        target = self.repository.path / "direct.txt"
        target.write_text("committed straight on main\n")
        direct_head = self.repository.commit_all("real direct commit on main")

        result = perform_merge(str(self.repository.path), "main", direct_head)

        self.assertEqual(result, direct_head)

    def test_a_real_conflict_raises_mergefailed_and_leaves_the_repo_clean(self):
        target = self.repository.path / "conflict.txt"
        target.write_text("main version\n")
        self.repository.commit_all("main writes conflict.txt")
        main_tip = self.repository.commit

        self._branch_from_base("codex/feature-2")
        target.write_text("feature version\n")
        feature_head = self.repository.commit_all("feature writes conflict.txt differently")

        run_git(self.repository.path, "checkout", "main")

        with self.assertRaises(MergeFailed):
            perform_merge(str(self.repository.path), "main", feature_head)

        status = run_git(self.repository.path, "status", "--porcelain").stdout
        self.assertEqual(status, "")
        current_tip = run_git(self.repository.path, "rev-parse", "main").stdout.strip()
        self.assertEqual(current_tip, main_tip)


if __name__ == "__main__":
    unittest.main()
