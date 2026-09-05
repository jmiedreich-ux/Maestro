/**
 * Real M1 automated-routing evidence, not invented product content.
 * The route cited below is one real, already-reviewed entry from
 * `services/maestro/maestro/operational_state.py`'s `_REVIEW_ROUTES`
 * dict — the M2 Atlas roadmap's "Architecture ruling on the one real
 * gap" is why: the ruling variant renders real recorded routing
 * outcomes, never a simulated "Architect agent" persona. `packetId`,
 * `attemptId`, and `recordedAt` below are illustrative example values
 * (the same convention this program's own A2–A5 backend packets use
 * for example snapshot rows) — not a transcription of any mockup
 * scenario, and not a real recorded event. Keep `route` in sync with
 * `_REVIEW_ROUTES` by hand if that dict ever changes; there is no
 * automated cross-check between this TypeScript fixture and the
 * Python source it cites.
 */
export interface RulingRouteEvidence {
  fromState: string;
  reviewKind: string;
  verdict: string;
  toState: string;
}

export interface RulingExample {
  packetId: string;
  attemptId: string;
  recordedAt: string;
  route: RulingRouteEvidence;
}

/**
 * `_REVIEW_ROUTES[("AwaitingReview", "IndependentImplementation", "Approve")]
 * == "MergeReady"` (`operational_state.py`, line 74 — corrected,
 * blocking finding from Decision Fidelity review: the dict's first two
 * entries occupy lines 72-73, making this cited third entry line 74,
 * not line 73 as an earlier draft said) — an approved
 * independent-implementation review always advances a packet to
 * `MergeReady`, deterministically, with no human step.
 */
export const RULING_EXAMPLE: RulingExample = {
  packetId: "A.4",
  attemptId: "A.4-01",
  recordedAt: "14:31",
  route: {
    fromState: "AwaitingReview",
    reviewKind: "IndependentImplementation",
    verdict: "Approve",
    toState: "MergeReady",
  },
};
