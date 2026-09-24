from __future__ import annotations

import unittest

from maestro.terminal.main import HELP_TOPICS, help_text
from maestro.terminal.rendering import _runtime_lines


class HelpAndRuntimeTests(unittest.TestCase):
    def test_help_lists_only_implemented_commands_with_syntax(self) -> None:
        overview = help_text("")
        for name in ("projects", "attention", "findings", "retry", "exit", "help"):
            self.assertIn(f"/{name}", overview)
        for missing in ("/register", "/architecture", "/execution"):
            self.assertNotIn(missing, overview)
        self.assertIn("Context:", help_text("findings"))
        self.assertIn("No command named /nope", help_text("nope"))
        self.assertEqual(set(HELP_TOPICS), {"help", "projects", "attention", "findings", "retry", "exit"})

    def test_runtime_readings_show_unknown_and_stale_plainly(self) -> None:
        self.assertEqual([], _runtime_lines({}))
        self.assertEqual(
            ["Runtime: no measurements recorded"],
            _runtime_lines({"runtime": {"runs": [], "sessions": [], "assignment_totals": []}}),
        )
        line = _runtime_lines(
            {
                "runtime": {
                    "runs": [
                        {
                            "run_id": "r1",
                            "active_seconds": 12,
                            "input_tokens": 100,
                            "context_used": None,
                            "quality": "estimated",
                            "stale": True,
                        }
                    ]
                }
            }
        )[0]
        self.assertIn("waiting unknown", line)
        self.assertIn("context unknown", line)
        self.assertIn("estimated, stale", line)


if __name__ == "__main__":
    unittest.main()
