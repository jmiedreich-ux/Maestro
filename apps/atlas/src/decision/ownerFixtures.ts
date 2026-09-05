/**
 * This is deliberately the SAME real scenario as C1's frozen
 * `apps/atlas/src/thread/fixtures.ts`'s `PACKET_A2_ENTRIES` — its final
 * entry (`k: "co"`, `14:56`, `escalate: true`) reads: "I can rule on
 * scope, corrections and dispatch — I cannot widen a frozen contract,
 * so this one goes to the owner. Terra holds its worktree meanwhile."
 * That is a real, already-established M1/M2 "no automated route, needs
 * a human" case — exactly what the owner-decision variant renders. This
 * fixture is a deliberately independent, hand-maintained object (not an
 * import from `../thread/fixtures`) so `decision/` stays standalone
 * from `thread/` until a real wiring slice joins them, matching this
 * program's own established pattern (`PacketThread` and `DecisionCard`
 * are each standalone until their own wiring slice). If C1's fixture
 * text ever changes, this object must be updated by hand to match —
 * the same kind of disclosed, hand-maintained coupling as C3's
 * `_REVIEW_ROUTES` citation.
 */
export interface OwnerOption {
  title: string;
  cost: string;
  body: string;
}

export interface OwnerDecisionExample {
  packetId: string;
  age: string;
  headline: string;
  lede: string;
  why: string;
  options: OwnerOption[];
}

/**
 * `headline`, `age` ("waiting 41m"), and both `options` are transcribed
 * verbatim from `Atlas Explorations.dc.html` — none is invented. `lede`
 * and `why` are adapted from the reference file's own `mine === true`
 * branch, replacing its fictional "the Architect agent" with "the
 * Coordinator" — the real M1/M2 actor that actually performs this
 * escalation, per `PACKET_A2_ENTRIES`'s own real final entry quoted
 * above. The reference file's third option ("Send back to the Architect
 * agent") is deliberately excluded: it depends on the M4 Architect
 * agent, which does not exist in M2, and there is nothing real to defer
 * to — see this slice's packet contract, Scope section.
 */
export const OWNER_DECISION_EXAMPLE: OwnerDecisionExample = {
  packetId: "A.2",
  age: "waiting 41m",
  headline: "Should a theme-free output get a sentinel version, or does the frozen contract change?",
  lede: "The Coordinator will not rule on a contract the owner froze, so it escalated instead of guessing. Terra is holding its worktree until you answer.",
  why: "the Coordinator stopped: this changes a contract you froze",
  options: [
    {
      title: "Allow a sentinel version",
      cost: "resumes now",
      body: "Terra writes theme-less:1 for theme-free outputs. The A.1 contract stays frozen and no correction is spent.",
    },
    {
      title: "Amend the A.1 contract",
      cost: "~25 min · 1 correction",
      body: "A.1 reopens for one correction so an empty theme version becomes legal. A.2 pauses and keeps its worktree.",
    },
  ],
};
