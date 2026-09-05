/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real `PERF`
 * array — pure reporting content, no persona, no fictional agent.
 * This slice renders only the collapsed row (action/packet/who/model/
 * tokens/cost/elapsed/outcome) for all 5 real records; the expandable
 * detail groups and the click-to-expand behavior are a separate,
 * later slice (a future `E2B`-style candidate), matching this
 * program's own established header/strip split pattern (E1/E1B).
 */
export type PerfCostKind = "billed" | "est" | "none";
export type PerfOutcome = "passed" | "complete" | "blocked" | "approved";

export interface PerfRecord {
  id: string;
  action: string;
  packet: string;
  who: string;
  model: string;
  tokens: string;
  cost: string;
  costKind: PerfCostKind;
  elapsed: string;
  outcome: PerfOutcome;
}

export const PERF_RECORDS: PerfRecord[] = [
  {
    id: "p1",
    action: "Dispatch preflight",
    packet: "A.2",
    who: "Terra",
    model: "claude-opus-4 · hosted · ctx 200k",
    tokens: "18,400 in",
    cost: "not billed",
    costKind: "none",
    elapsed: "0.9s",
    outcome: "passed",
  },
  {
    id: "p2",
    action: "Plan and read the A.1 contract",
    packet: "A.2",
    who: "Terra",
    model: "claude-opus-4 · hosted",
    tokens: "46,900 total",
    cost: "$0.41 billed",
    costKind: "billed",
    elapsed: "2m 04s",
    outcome: "complete",
  },
  {
    id: "p3",
    action: "Implement RuntimePackageBuilder",
    packet: "A.2",
    who: "Terra",
    model: "claude-opus-4 · hosted",
    tokens: "112,300 total",
    cost: "$1.86 billed",
    costKind: "billed",
    elapsed: "38m 11s",
    outcome: "blocked",
  },
  {
    id: "p4",
    action: "Review of the A.1 correction",
    packet: "A.1",
    who: "Claude Opus",
    model: "claude-opus-4 · hosted",
    tokens: "31,200 total",
    cost: "$0.52 estimated",
    costKind: "est",
    elapsed: "6m 40s",
    outcome: "approved",
  },
  {
    id: "p5",
    action: "Source-home check",
    packet: "A.0",
    who: "local Qwen",
    model: "qwen2.5-coder-32b · local · Q4_K_M",
    tokens: "9,700 est.",
    cost: "local compute",
    costKind: "none",
    elapsed: "4m 52s",
    outcome: "passed",
  },
];
