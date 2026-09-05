/**
 * Real content, not a simulated "Architect agent" ruling. The
 * reference file's own domain model describes a "Decision Fidelity
 * check" as "a record attached to a ruling, listing claims verified
 * against named evidence, each matches/drifts/n/a, plus an overall
 * verdict and a binding scope note" (README, "Domain model" section) —
 * that is structurally the exact same concept as THIS project's own,
 * real Decision Fidelity review process (the one used to review every
 * M2 packet this session, including C3 and C4). So this record cites a
 * real, already-closed review from this project's own history — C3's
 * (`MB-SLICE-M2-C3-DECISION-CARD-RULING-01`, PR #92) — rather than
 * inventing a fictional Architect-agent ruling on a fictional
 * contract question. `id` is a real, traceable identifier following
 * this project's own slice-naming convention, not the reference
 * file's arbitrary "DF-2" (reusing that literal id would misleadingly
 * imply continuity with the mockup's own, different, fictional
 * narrative).
 */
export interface FidelityRow {
  claim: string;
  evidence: string;
  verdict: "matches" | "drifts" | "n/a";
}

export interface FidelityRecordExample {
  id: string;
  subject: string;
  against: string;
  rows: FidelityRow[];
  verdict: string;
  note: string;
}

export const FIDELITY_RECORD_EXAMPLE: FidelityRecordExample = {
  id: "DF-M2-C3",
  subject: "M2-C3 decision-card packet: real-routing-table citation",
  against: "PR #92 Decision Fidelity review · commit e8a87ca",
  rows: [
    {
      claim: "Cites a real, existing _REVIEW_ROUTES entry as ruling evidence",
      evidence: "operational_state.py:74 · verified by grep",
      verdict: "matches",
    },
    {
      claim: "Renders the roadmap's required \"link to the rule that fired\"",
      evidence: "exact rule citation in the why span · corrected 2026-09-05",
      verdict: "matches",
    },
    {
      claim: "No fictional \"Architect agent\" persona anywhere in rendered copy",
      evidence: "badge/copy audit, DecisionCard.tsx",
      verdict: "matches",
    },
    {
      claim: "Reuses C1's frozen A.2 fixture thread",
      evidence: "deliberately not reused — see the C3 packet's own Scope section",
      verdict: "n/a",
    },
  ],
  verdict: "Faithful",
  note: "MB-SLICE-M2-C3-DECISION-CARD-RULING-01 closed clean after one targeted correction (PR #92). Binding on any later slice that reuses this routing-table-citation pattern — the cited rule must stay traceable to real operational_state.py source, not restated from memory.",
};
