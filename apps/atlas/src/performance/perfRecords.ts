/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real `PERF`
 * array, now including the per-record `note` and the three real
 * detail `groups` (`context`/`tokens`/`cost & time`) this program's own
 * E2 packet deferred — pure reporting content, no persona, no
 * fictional agent. Every `PerfDetailRow`'s `kind` ('' | 'est' | 'ok' |
 * 'warn' | 'na') is transcribed directly from the reference file's own
 * per-row third tuple element, not inferred from the label text.
 */
export type PerfCostKind = "billed" | "est" | "none";
export type PerfOutcome = "passed" | "complete" | "blocked" | "approved";
export type PerfDetailKind = "" | "est" | "ok" | "warn" | "na";

export interface PerfDetailRow {
  label: string;
  value: string;
  kind: PerfDetailKind;
}

export interface PerfDetailGroup {
  name: string;
  rows: PerfDetailRow[];
}

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
  note: string;
  groups: PerfDetailGroup[];
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
    note: "Counted with the model tokenizer before launch. Future tool and file growth was carried as a bounded range, not a false exact number.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Configured limit", value: "200,000", kind: "" },
          { label: "Known input tokens", value: "18,400 exact", kind: "" },
          { label: "Projected growth", value: "12k–31k est.", kind: "est" },
          { label: "Output reserve", value: "16,000", kind: "" },
          { label: "Packet minimum", value: "90,000 · satisfied", kind: "ok" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "18,400 reported", kind: "" },
          { label: "Cached input", value: "unavailable", kind: "na" },
          { label: "Output", value: "0", kind: "" },
          { label: "Reasoning", value: "unavailable", kind: "na" },
          { label: "Total", value: "18,400", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "not_billed", kind: "na" },
          { label: "Elapsed", value: "0.9s", kind: "" },
          { label: "Allowance link", value: "weekly window · fresh", kind: "" },
          { label: "Measurement", value: "tokenizer, exact", kind: "ok" },
        ],
      },
    ],
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
    note: "Runtime-reported counters, so no estimate was substituted. Cached input reduced billed input on the second contract read.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Context used", value: "46,900 of 200,000", kind: "" },
          { label: "Pressure threshold", value: "150,000", kind: "" },
          { label: "Headroom", value: "76% free", kind: "ok" },
          { label: "Checkpoint fired", value: "no", kind: "" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "38,100 reported", kind: "" },
          { label: "Cached input", value: "11,700 reported", kind: "ok" },
          { label: "Output", value: "8,800 reported", kind: "" },
          { label: "Reasoning", value: "3,200 reported", kind: "" },
          { label: "Total", value: "46,900", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "$0.41 billed", kind: "ok" },
          { label: "Elapsed", value: "2m 04s", kind: "" },
          { label: "Attributed to", value: "controlled usage", kind: "" },
          { label: "Measurement", value: "runtime-reported", kind: "ok" },
        ],
      },
    ],
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
    note: "Attempt ended at a safe boundary when Terra hit the contract question. Nothing was discarded and no correction was spent.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Context used", value: "112,300 of 200,000", kind: "" },
          { label: "Pressure threshold", value: "150,000", kind: "" },
          { label: "Headroom", value: "44% free", kind: "" },
          { label: "Checkpoint fired", value: "no", kind: "" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "81,400 reported", kind: "" },
          { label: "Cached input", value: "29,600 reported", kind: "" },
          { label: "Output", value: "30,900 reported", kind: "" },
          { label: "Reasoning", value: "14,100 reported", kind: "" },
          { label: "Total", value: "112,300", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "$1.86 billed", kind: "ok" },
          { label: "Elapsed", value: "38m 11s", kind: "" },
          { label: "Ended by", value: "blocker at boundary", kind: "warn" },
          { label: "Corrections spent", value: "0 of 1", kind: "" },
        ],
      },
    ],
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
    note: "The runtime did not return a billed amount for this attempt, so cost is labelled an estimate with its confidence — it is not presented as billed.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Context used", value: "31,200 of 200,000", kind: "" },
          { label: "Review round", value: "2 of 2", kind: "" },
          { label: "Reviewer of record", value: "unchanged", kind: "ok" },
          { label: "Scope", value: "correction range only", kind: "" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "26,800 reported", kind: "" },
          { label: "Cached input", value: "unavailable", kind: "na" },
          { label: "Output", value: "4,400 reported", kind: "" },
          { label: "Reasoning", value: "unavailable", kind: "na" },
          { label: "Total", value: "31,200", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "$0.52 estimated", kind: "est" },
          { label: "Confidence", value: "medium", kind: "est" },
          { label: "Elapsed", value: "6m 40s", kind: "" },
          { label: "Measurement", value: "price-table estimate", kind: "est" },
        ],
      },
    ],
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
    note: "Local execution is not called zero-cost. It is reported as capacity and wall time, separately from the hosted weekly allowance.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Configured limit", value: "32,768", kind: "" },
          { label: "Quantization", value: "Q4_K_M", kind: "" },
          { label: "Context used", value: "9,700 estimated", kind: "est" },
          { label: "Packet minimum", value: "8,000 · satisfied", kind: "ok" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "7,900 estimated", kind: "est" },
          { label: "Cached input", value: "unavailable", kind: "na" },
          { label: "Output", value: "1,800 estimated", kind: "est" },
          { label: "Reasoning", value: "unavailable", kind: "na" },
          { label: "Throughput", value: "31 tok/s", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "local compute", kind: "na" },
          { label: "Elapsed", value: "4m 52s", kind: "" },
          { label: "Host capacity", value: "GPU 78% · 22m held", kind: "" },
          { label: "Allowance impact", value: "none — kept separate", kind: "ok" },
        ],
      },
    ],
  },
];
