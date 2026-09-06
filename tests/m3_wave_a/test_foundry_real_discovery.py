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
already-existing (unmodified) inventory/escalation engine. 20 of 29
leaves are Foundry's own real declared facts, cited inline to exact
AGENTS.md/package.json/tracker content; the other 9 (Murphy QA policy,
notification policy, deployment/rollback policy, environment/secret
reference names, owner-acceptance policy, integration commands, the
exceptions register) are explicit Architect decisions applying
Maestro's own already-Owner-approved standing policy (M0-D03/D04/D10)
to Foundry — not fabricated Foundry-specific facts, and each one cited
inline to its own source decision.
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
        # Architect decision (2026-09-06), not Foundry's own declaration —
        # Foundry's docs describe independent review + merge but state no
        # named owner-acceptance policy. Maestro's own already-Owner-approved
        # policy (M0-D10 proving-sequence step 5) applies directly: "Apply
        # the existing packet, review, escalation, and owner-acceptance rules
        # without automatic merge."
        "owner_acceptance_policy": (
            "Owner acceptance required before merge; no automatic merge "
            "(M0-D10 proving-sequence step 5)."
        ),
        # Architect decision, not Foundry's own declaration — M3's own
        # roadmap scope never deploys anything (stops at
        # AwaitingOwner/MergeReady); Foundry's own deployment process, if
        # any, is simply untouched and out of scope at this milestone.
        "deployment_rollback_policy": (
            "Not applicable for M3 — Maestro deploys nothing at this "
            "milestone; Foundry's own deployment process (if any) is "
            "unaffected and out of Maestro's M3 scope."
        ),
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
        # Architect decision, not a distinct Foundry declaration — Foundry
        # names no separate "integration" gate; the honest, real answer is
        # that its full declared check suite (identical to D1's own
        # mechanical-grading gates) is the only real gate that exists.
        "integration_commands": [
            "npm run check", "npm run build", "npm run test:foundation", "npm run test:browser",
        ],
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
        # Architect decision, not Foundry's own declaration — Murphy is a
        # Maestro-side concept (master plan §8); its own standing policy is
        # manual/Owner-approved with no Azure access implied by M3, applied
        # directly to Foundry: it is not deployed or QA'd via Murphy here.
        "qa_murphy_policy": (
            "Not applicable for M3 — Murphy remains manual/Owner-approved "
            "(master plan §8); Foundry is not deployed to Azure or QA'd via "
            "Murphy at this milestone."
        ),
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
        # Architect decision, not Foundry's own declaration — M3 deploys
        # nothing (see delivery.deployment_rollback_policy above), so no
        # named external environment reference is required at this
        # milestone; a real, empty confirmation, not an unresolved gap.
        "environment_reference_names": [],
        # Architect decision, not a Foundry declaration — the one real
        # secret this milestone actually needs is the GitHub App key
        # already stored via maestro.secrets this session (W0.2), under
        # exactly this reference name.
        "secret_reference_names": ["GITHUB_APP_PRIVATE_KEY"],
        # Architect decision, not Foundry's own declaration — Foundry states
        # no additional/stricter notification requirement; Maestro's own
        # already-Owner-approved M0-D04 policy applies directly.
        "notification_policy": "Per M0-D04 (notifications and escalation); no Foundry-specific addition.",
    },
    "exceptions": {
        # Architect decision, not Foundry's own declaration — no exceptions
        # were found or declared anywhere in the real content read; the
        # schema's own "none" disposition (requiring an empty items array)
        # is the honest, correct default, not an unresolved gap.
        "disposition": "none",
        "items": [],
    },
}


class FoundryRealDiscoveryTests(unittest.TestCase):
    def test_real_foundry_snapshot_is_now_fully_reviewable(self):
        # The 9 leaves Foundry's own docs left undeclared are now filled by
        # explicit, cited Architect decisions applying Maestro's own
        # already-Owner-approved standing policy (M0-D03/D04/D10) — not
        # fabricated Foundry-specific facts. See FOUNDRY_SNAPSHOT's own
        # inline comments for each decision's citation.
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        self.assertTrue(result["inventory"]["reviewable"])
        self.assertIsNone(result["escalation_reason"])
        self.assertIsNotNone(result["proposed_binding"])

    def test_every_leaf_is_confirmed_not_missing_or_conflicting(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        summary = result["inventory"]["summary"]
        self.assertEqual(summary["conflicting"], 0)
        self.assertEqual(summary["missing"], 0)
        self.assertEqual(summary["confirmed"], 29)  # every schema leaf

    def test_confirmed_identity_matches_the_real_fetched_repository_metadata(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        identity = result["inventory"]["areas"]["identity"]
        self.assertEqual(identity["repository_identifier"]["value"], "jmiedreich-ux/Foundry")
        self.assertEqual(identity["default_branch"]["value"], "main")

    def test_proposed_binding_carries_the_architect_decided_no_automatic_merge_policy(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        self.assertIn(
            "no automatic merge",
            result["proposed_binding"]["delivery"]["owner_acceptance_policy"],
        )

    def test_proposed_binding_carries_the_real_secret_reference_name(self):
        result = evaluate_snapshot(FOUNDRY_SNAPSHOT)
        self.assertEqual(
            result["proposed_binding"]["operations"]["secret_reference_names"],
            ["GITHUB_APP_PRIVATE_KEY"],
        )


if __name__ == "__main__":
    unittest.main()
