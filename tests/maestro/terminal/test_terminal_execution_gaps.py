"""The Execution view shows support, determinations, milestone gaps, the architect's recommendation and the typed disposition choices."""
from __future__ import annotations

import unittest

from maestro.terminal.execution import render


def view(**over):
    base = {"state": "running", "waiting": "w", "manager": {"tool": "codex", "model": "m", "route_id": "r", "passes": 1, "planning": False}, "source_commit": "a" * 40,
            "product_master": {"branch": "main", "start_commit": "b" * 40}, "packets": [], "measurements": {"active_agent_seconds": 0, "tokens": "not reported"}}
    base.update(over)
    return base


class RenderTests(unittest.TestCase):
    def test_support_recommendation_and_the_owner_choices_are_shown_in_plain_words(self) -> None:
        text = render(view(
            support=[{"support_id": "support-1", "packet_key": "p1", "state": "limit_paused", "disposition": "create_role", "role_path": "a/.maestro/role-x.md", "note": None, "reason": "no role",
                      "reviews": {"completed": 2, "limit": 2}, "review_results": [{"round": 1, "outcome": "REQUEST_CHANGES", "blocking": 1}, {"round": 2, "outcome": "REQUEST_CHANGES", "blocking": 1}],
                      "routes": {"architect": {"tool": "claude_code", "model": "x"}, "reviewer": {"tool": "codex", "model": "y"}, "switches": []}}],
            determinations=[{"determination_id": "det-q1", "state": "decided", "subject": "architectural question on p1", "note": None, "result": {"determination": "within_confirmed_design", "interpretation": "use the confirmed contract", "rationale": "r"}}],
            gaps=[{"gap_id": "gap-finding-1", "finding_id": "finding-1", "milestone": "m1", "state": "active", "note": None, "finding": {"subject": "Refunds missing"}, "determination": "in_scope_supplement",
                   "supplements": [{"supplement_id": "supplement-1", "version": 1, "state": "active", "packets": ["fix-refunds"], "commit": "c" * 40}]}],
            owner_decisions=[{"target": "execution_support_fidelity_review", "packet_key": "p1", "recommendation": "grant_one", "rationale": "one fix left"},
                             {"target": "execution_work_disposition", "packet_key": "p2", "recommendation": "finish_safe_work", "rationale": "scope change", "choices": ["continue_unaffected", "finish_safe_work"]}],
            disposition={"choice": "continue_unaffected", "recommended": "finish_safe_work", "affected": ["p2"]}), full=True)
        for expected in ("support support-1 [limit_paused] for p1", "create role: a/.maestro/role-x.md", "fidelity review 2 of 2", "the architect recommends grant_one",
                         "determination det-q1 [decided]", "within confirmed design: use the confirmed contract", "milestone gap gap-finding-1 [active]", "supplement supplement-1 v1 [active] fix-refunds",
                         "Choose: continue unaffected, finish safe work", "Work disposition: continue unaffected (architect recommended finish safe work)"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
