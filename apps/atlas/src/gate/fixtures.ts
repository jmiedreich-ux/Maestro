/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `GATE_CRITERIA` array, the entry-criteria header's real
 * `metLabel`/`metColor`, and the card's own trailing footer note —
 * pure reporting content, no persona, no fictional agent. This slice
 * renders only the entry-criteria card (header, all 5 criteria rows,
 * and the card's own footer note); the gate's separate header block
 * (title, state line, Open-gate button, approver note, releases list)
 * is a separate, later slice (a future `E7B`-style candidate) — its
 * lede and approver note both reference the reference file's
 * fictional "Architect agent" and need the same real-mechanism
 * adaptation treatment Wave C used (C3/C4), which this slice's own
 * real, persona-free content does not need.
 */
export type GateCriterionMet = "yes" | "part" | "no";

export interface GateCriterion {
  title: string;
  detail: string;
  evidence: string;
  met: GateCriterionMet;
}

export const GATE_CRITERIA: GateCriterion[] = [
  {
    title: "A.0 through A.7 accepted",
    detail: "Every M1-A packet closed by the Coordinator with locks released.",
    evidence: "2 of 8 accepted",
    met: "no",
  },
  {
    title: "Frozen-presentation contract holds",
    detail: "No packet re-derived or widened the A.1 identity contract.",
    evidence: "A.1 · 9d3e1a2",
    met: "yes",
  },
  {
    title: "Every owner decision carries a fidelity check",
    detail: "Rulings that changed behaviour are recorded and binding on later packets.",
    evidence: "DF-2 pending",
    met: "part",
  },
  {
    title: "Fixture journey proven end to end",
    detail: "A.6 demonstrates the complete journey and its exclusions.",
    evidence: "A.6 not dispatched",
    met: "no",
  },
  {
    title: "No correction budget overdrawn",
    detail: "One correction per packet, same reviewer of record.",
    evidence: "1 spent · none over",
    met: "yes",
  },
];

/** Real, verbatim — matches GATE_CRITERIA's own real counts (2 yes, 1 part, 2 no). */
export const GATE_MET_LABEL = "2 met · 1 partial · 2 open";

/** Real, verbatim — the card's own trailing footer row. */
export const GATE_FOOTER_NOTE =
  "Criteria were fixed when M1-A opened. Changing one is an owner decision and reopens the milestone plan.";
