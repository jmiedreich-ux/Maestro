"""M3 A1 — real (non-fixture) discovery, run for real against Foundry.

The snapshot below is a real, cited interpretation of Foundry's actual
repository content, fetched live this session (2026-09-06) via
maestro.github_client against jmiedreich-ux/Foundry at `main`:
- Repo metadata: full_name="jmiedreich-ux/Foundry", default_branch="main".
- AGENTS.md: fetched in full (9593 real characters); every string below
  quotes or closely paraphrases that real content, cited inline.
- package.json scripts (fetched in full): check/dev/build/test:foundation/
  test:browser, exactly as already recorded in
  docs/registrations/foundry-read-only-discovery.md.
- tracker/assignments.json and PROJECT_STATUS.md (fetched in full):
  confirm CG-M4-18 is now merged (PR #56), "Resume at CG-M4-19 only" —
  proving the cached discovery doc genuinely was stale, as that doc's
  own text already warned it would be.

This is deliberately NOT a generic "any project" parser — see
real_discovery.py's own module docstring. It is this session's one real,
by-hand interpretation of one real project's real docs, run through the
already-existing (unmodified) inventory/escalation engine. Several
leaves are honestly left absent because Foundry's own docs genuinely do
not declare them (Murphy QA policy, notification policy, deployment/
rollback policy, environment/secret reference names, an exceptions
register) — real open questions for A2, not fabricated values.
"""

from __future__ import annotations

import unittest

from maestro.real_discovery import evaluate_snapshot

FOUNDRY_SNAPSHOT = {
    "identity": {
        "project_name": "Foundry",
        "repository_identifier": "jmiedreich-ux/Foundry",
        "default_branch": "main",
        # Maestro's own adapter/process identifiers, not project-specific.
        "adapter_version": "maestro-github-adapter-v1",
        "process_version": "maestro-m3-a1-process-v1",
    },
    "authority": {
        # AGENTS.md: "Design authority is approved and recorded in
        # docs/features/<feature>/ before implementation"; the one real
        # feature directory confirmed live via the GitHub API this
        # session is docs/features/control-gallery.
        "architecture_paths": ["docs/features/control-gallery"],
        "plan_paths": ["docs/features/control-gallery", "ROADMAP.md"],
        # AGENTS.md "Authority and startup", item 2, verbatim path.
        "handoff_path": "ai/handoffs/current.md",
        # AGENTS.md "Authority and startup", item 1, verbatim path.
        "rules_sop_path": "AGENTS.md",
        # AGENTS.md "Features and milestones", quoted near-verbatim.
        "task_issue_conventions": (
            "A packet's assignment belongs on its own checklist line, in the "
            "milestone's linked GitHub issue: `- [ ] task text — role-or-name`, "
            "optionally leading with a stable id before a middle dot "
            "(`- [ ] CG-M1-01 · task text — role`)."
        ),
    },
    "delivery": {
        # AGENTS.md "Features and milestones", quoted verbatim.
        "branch_pr_merge_policy": (
            "One milestone at a time: claim it, create one branch and PR, "
            "verify locally, obtain independent review, merge, then "
            "synchronize records."
        ),
        # delivery.owner_acceptance_policy and delivery.deployment_rollback_policy
        # are deliberately absent: AGENTS.md describes independent review and
        # merge, and PROJECT_STATUS.md shows real owner-pause behavior
        # ("Paused by owner after CG-M4-18"), but neither document states a
        # named owner-acceptance or deployment/rollback POLICY as such.
    },
    "verification": {
        # package.json "build" script, fetched live this session.
        "build_commands": ["npm run build"],
        # package.json "test:foundation" script (vitest), fetched live.
        "test_commands": ["npm run test:foundation"],
        # package.json "test:browser" script (playwright) is Foundry's
        # real UI/browser QA gate, distinct from its unit test command.
        "ui_qa_commands": ["npm run test:browser"],
        # AGENTS.md "How every task is performed", quoted verbatim.
        "evidence_rules": (
            "Evidence is a rerunnable command plus its result. Never call "
            "unexecuted work verified."
        ),
        # AGENTS.md "Definition of done", quoted near-verbatim.
        "untested_handling": (
            "Explicitly mark non-applicable items `N/A (reason)` and "
            "unexecuted items `UNTESTED`."
        ),
        # verification.integration_commands is deliberately absent: the only
        # other declared script, "check" (`node --check apps/lab/src/main.js`),
        # is a syntax check, not a distinct integration gate.
    },
    "roles": {
        # tracker/assignments.json, fetched live: real distinct owner
        # classes observed across real completed packets.
        "specialist_overlays": ["Codex coordinator", "Local Qwen implementation agent"],
        # AGENTS.md "Verification, review, and handoff", quoted verbatim.
        "reviewer_route": "Every change receives independent review by someone other than its author.",
        # AGENTS.md "Local-agent quality protocol", "Remote-agent delivery
        # parity", paraphrased: both a local worker and a delegated
        # remote/cloud worker are real, eligible executor classes.
        "local_cloud_eligibility": (
            "Local Qwen and a delegated remote/cloud implementation agent are "
            "both eligible, under the same delivery-parity requirements "
            "(AGENTS.md 'Remote-agent delivery parity')."
        ),
        # roles.qa_murphy_policy is deliberately absent: Murphy is a
        # Maestro-side concept; Foundry's own docs, correctly, never
        # mention it.
    },
    "operations": {
        # AGENTS.md "Shared-file and agent safety", quoted/paraphrased:
        # "No two workers modify the same file concurrently... The
        # coordinator owns contracts, package configuration, shared
        # fixtures, workflows, tracker, status, and handoff."
        "resource_locks": [
            "package.json", "workspace configuration", "shared fixtures",
            "workflows", "tracker", "PROJECT_STATUS.md", "ai/handoffs/current.md",
        ],
        # operations.environment_reference_names, operations.secret_reference_names,
        # and operations.notification_policy are deliberately absent: Foundry's
        # docs declare a rule against committing secrets (AGENTS.md
        # "Documentation and controlled records") but name no specific
        # environment/secret reference identifiers, and state no
        # notification policy at all — both real Maestro-side operational
        # concepts this project has not (yet) declared.
    },
    # exceptions.disposition/items are deliberately absent: Foundry's docs
    # declare no Maestro-shaped exceptions register.
}


class FoundryRealDiscoveryTests(unittest.TestCase):
    def test_real_foundry_snapshot_is_not_yet_reviewable(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        self.assertFalse(result["inventory"]["reviewable"])
        self.assertIsNone(result["proposed_binding"])

    def test_escalation_reason_names_exactly_the_real_missing_leaves(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        missing_paths = {
            path.strip() for path in result["escalation_reason"].split(",")
        }
        self.assertEqual(
            missing_paths,
            {
                "delivery.owner_acceptance_policy",
                "delivery.deployment_rollback_policy",
                "verification.integration_commands",
                "roles.qa_murphy_policy",
                "operations.environment_reference_names",
                "operations.secret_reference_names",
                "operations.notification_policy",
                "exceptions.disposition",
                "exceptions.items",
            },
        )

    def test_every_leaf_not_missing_is_confirmed_not_conflicting(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        summary = result["inventory"]["summary"]
        self.assertEqual(summary["conflicting"], 0)
        self.assertEqual(summary["missing"], 9)
        self.assertEqual(summary["confirmed"], 20)  # 29 total leaves - 9 missing

    def test_confirmed_identity_matches_the_real_fetched_repository_metadata(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        identity = result["inventory"]["areas"]["identity"]
        self.assertEqual(identity["repository_identifier"]["value"], "jmiedreich-ux/Foundry")
        self.assertEqual(identity["default_branch"]["value"], "main")


if __name__ == "__main__":
    unittest.main()
