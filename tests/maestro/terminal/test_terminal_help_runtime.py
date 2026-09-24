from __future__ import annotations

import unittest

from maestro.terminal.main import HELP_TOPICS, help_text
from maestro.terminal.rendering import _fit, _runtime_lines
from maestro.terminal.questions import QuestionInteraction
from maestro.terminal.workspace import AttentionItem


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
        )
        line = " ".join(line)
        self.assertIn("waiting unknown", line)
        self.assertIn("context unknown", line)
        self.assertIn("estimated, stale", line)


if __name__ == "__main__":
    unittest.main()


class QuestionDisplayTests(unittest.TestCase):
    def test_status_line_after_a_question_is_wrapped_not_cut(self) -> None:
        text = "Question: Which?\nNot sent — " + "long explanation " * 8 + "twice."
        lines = _fit([text], 60)
        self.assertTrue(all(len(line) <= 60 for line in lines))
        self.assertIn("twice.", " ".join(lines))

    def test_closed_question_offers_replacement_without_moving_text(self) -> None:
        class State:
            input = None
            attention = (
                AttentionItem("c1", "question", "q-new", "p", "a", "Pick again", "proc"),
                AttentionItem("c2", "question", "q-old", "p", "a", "Pick", "proc"),
                AttentionItem("c3", "question", "q-other", "p", "b", "Other", "proc"),
            )

        class Context:
            state = State()

        message = QuestionInteraction()._closed_message(
            Context(), {"project_id": "p", "activity_id": "a", "question_id": "q-old"}
        )
        self.assertIn("your text was not applied", message)
        self.assertIn("Pick again (q-new)", message)
        self.assertNotIn("q-other", message)
