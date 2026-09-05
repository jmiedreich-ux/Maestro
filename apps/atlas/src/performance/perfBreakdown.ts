/**
 * Transcribed from `Atlas Explorations.dc.html`'s real `SPLIT` object
 * (the reference file's own `SPLIT_COLORS` array is real B2 tokens —
 * see `PerfBreakdownCard.tsx`'s own disclosure) — pure reporting
 * content, with one real
 * adaptation disclosed here and in the packet: the reference file's
 * own `cost.role` array includes a fourth entry, `['Architect agent',
 * 0, 'pending']` — the fictional M4-only persona that must never be
 * rendered as existing in M2 (see this program's own Wave C
 * precedent). Unlike `cost.role`, the reference file's `tokens.role`
 * and `time.role` arrays already use only real M1 actors for their own
 * fourth entry (`Local Qwen`, then `Coordinator`) — no fictional
 * persona there. This slice makes `cost.role` match that same real,
 * already-established pattern: `Local Qwen` (0%, `'local compute'` —
 * the exact real cost-kind text `PERF_RECORDS`'s own `p5` already uses
 * for the same real actor's cost) replaces `Architect agent`, and the
 * `cost` basis's own real `caveat` sentence is rewritten to state both
 * real reasons for a 0% role (Coordinator's actions are not worker
 * attempts; Local Qwen's cost is local compute, never billed hosted
 * dollars) rather than the reference's own sentence, which named the
 * fictional persona directly ("Coordinator and Architect actions ran
 * inside worker attempts already counted...").
 */
export type SplitBasisKey = "cost" | "tokens" | "time";

export interface SplitPart {
  label: string;
  pct: number;
  abs: string;
}

export interface SplitBasisData {
  note: string;
  role: SplitPart[];
  work: SplitPart[];
  caveat: string;
}

export const SPLIT: Record<SplitBasisKey, SplitBasisData> = {
  cost: {
    note: "billed and estimated hosted cost · $2.79",
    role: [
      { label: "Implementor", pct: 81, abs: "$2.27" },
      { label: "Reviewer", pct: 19, abs: "$0.52" },
      { label: "Coordinator", pct: 0, abs: "not billed" },
      { label: "Local Qwen", pct: 0, abs: "local compute" },
    ],
    work: [
      { label: "Coding", pct: 67, abs: "$1.86" },
      { label: "Reading & planning", pct: 15, abs: "$0.41" },
      { label: "Review", pct: 19, abs: "$0.52" },
      { label: "Preflight & records", pct: 0, abs: "not billed" },
    ],
    caveat:
      "Coordinator actions are not worker attempts, so they carry no separate billed amount; Local Qwen's cost is local compute, never billed hosted dollars. $0.52 of this total is an estimate, not a billed figure.",
  },
  tokens: {
    note: "total attempt tokens · 218,500",
    role: [
      { label: "Implementor", pct: 81, abs: "177,600" },
      { label: "Reviewer", pct: 14, abs: "31,200" },
      { label: "Local Qwen", pct: 5, abs: "9,700 est." },
      { label: "Coordinator", pct: 0, abs: "unavailable" },
    ],
    work: [
      { label: "Coding", pct: 51, abs: "112,300" },
      { label: "Reading & planning", pct: 21, abs: "46,900" },
      { label: "Review", pct: 14, abs: "31,200" },
      { label: "Preflight & checks", pct: 13, abs: "28,100" },
    ],
    caveat:
      "Hosted and local tokens are shown in one bar for shape only — they are different units of work and are never summed into an allowance figure.",
  },
  time: {
    note: "wall time across attempts · 52m 36s",
    role: [
      { label: "Implementor", pct: 78, abs: "41m 04s" },
      { label: "Reviewer", pct: 13, abs: "6m 40s" },
      { label: "Local Qwen", pct: 9, abs: "4m 52s" },
      { label: "Coordinator", pct: 0, abs: "under 1m" },
    ],
    work: [
      { label: "Coding", pct: 73, abs: "38m 11s" },
      { label: "Reading & planning", pct: 4, abs: "2m 04s" },
      { label: "Review", pct: 13, abs: "6m 40s" },
      { label: "Local checks", pct: 10, abs: "5m 41s" },
    ],
    caveat:
      "This is attempt time, not elapsed milestone time. The 41 minutes A.2 spent blocked waiting on a ruling is not attributed to any role.",
  },
};

export const SPLIT_BASES: { key: SplitBasisKey; label: string }[] = [
  { key: "cost", label: "Cost" },
  { key: "tokens", label: "Tokens" },
  { key: "time", label: "Time" },
];
