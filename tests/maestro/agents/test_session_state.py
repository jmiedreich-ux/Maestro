import tempfile
import unittest
from pathlib import Path

from maestro.agents.session_state import SessionUse, harvest, project_key, seed


class SessionStateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.session = SessionUse("s1", self.root / "state", None, "assigned")

    def test_codex_history_is_saved_and_restored_to_a_new_home(self):
        first = self.root / "home1"
        (first / ".codex/sessions/2026/09/24").mkdir(parents=True)
        (first / ".codex/sessions/2026/09/24/rollout-x.jsonl").write_text("history")
        (first / ".codex/auth.json").write_text("secret")
        self.assertTrue(harvest("codex", self.session, first))
        second = self.root / "home2"
        self.assertTrue(seed("codex", self.session, second, self.root / "run2"))
        self.assertEqual((second / ".codex/sessions/2026/09/24/rollout-x.jsonl").read_text(), "history")
        self.assertFalse((second / ".codex/auth.json").exists(), "credentials are never saved")

    def test_claude_history_is_rekeyed_to_the_new_working_directory(self):
        first = self.root / "home1"
        (first / ".claude/projects" / project_key(self.root / "run1")).mkdir(parents=True)
        (first / ".claude/projects" / project_key(self.root / "run1") / "abc.jsonl").write_text("history")
        self.assertTrue(harvest("claude_code", self.session, first))
        second = self.root / "home2"
        self.assertTrue(seed("claude_code", self.session, second, self.root / "run2"))
        self.assertEqual((second / ".claude/projects" / project_key(self.root / "run2") / "abc.jsonl").read_text(), "history")

    def test_nothing_saved_means_nothing_restored(self):
        self.assertFalse(seed("codex", self.session, self.root / "h", self.root / "r"))
        self.assertFalse(harvest("codex", self.session, self.root / "empty"))

    def test_links_are_not_followed(self):
        home = self.root / "home"
        (home / ".codex/sessions").mkdir(parents=True)
        outside = self.root / "outside.txt"
        outside.write_text("private")
        (home / ".codex/sessions/link").symlink_to(outside)
        harvest("codex", self.session, home)
        self.assertFalse((self.session.state_dir / "history/link").exists())

    def test_session_use_round_trips(self):
        self.assertEqual(SessionUse.from_dict(self.session.as_dict()), self.session)


if __name__ == "__main__":
    unittest.main()
