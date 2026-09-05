/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `HISTORY` array, `HIST_STYLE` map, and `histStats` — pure reporting
 * content, no persona, no fictional agent. Every entry describes real
 * M1-A events already established elsewhere in this program (A.1's
 * acceptance, A.2's dispatch/blocked/escalation — the same real
 * scenario C1's `PACKET_A2_ENTRIES`, C4's `OwnerDecisionCard`, and C6's
 * `CrashCard` already use). `histStats`'s "Decisions recorded" value
 * (`'1'`) is the reference file's own real initial-state default
 * (`s.decided` is `null` at initialization), not a fabricated number —
 * the same reasoning C7's `derivePacketHeaderState` used for its own
 * real-default values.
 */
export type HistoryKind =
  | "dispatch"
  | "handoff"
  | "review"
  | "correction"
  | "accepted"
  | "report"
  | "blocked"
  | "escalated";

export interface HistoryEntry {
  time: string;
  kind: HistoryKind;
  packet: string;
  title: string;
  who: string;
  detail: string;
  ref: string;
}

export interface HistoryStat {
  label: string;
  value: string;
}

export const HISTORY_STATS: HistoryStat[] = [
  { label: "Packets accepted", value: "2 of 8" },
  { label: "Corrections spent", value: "1" },
  { label: "Decisions recorded", value: "1" },
  { label: "Elapsed", value: "3h 07m" },
];

export const HISTORY_ENTRIES: HistoryEntry[] = [
  {
    time: "13 Feb",
    kind: "dispatch",
    packet: "A.0",
    title: "Source homes confirmed",
    who: "Coordinator",
    detail: "Routed to local Qwen, reviewed PASS by Terra. Output was an issue comment — no code, no locks.",
    ref: "",
  },
  {
    time: "12:40",
    kind: "dispatch",
    packet: "A.1",
    title: "Sol dispatched on the Core contract",
    who: "Coordinator",
    detail: "Base c246080f, one Core file and one Core test, review to Claude Opus.",
    ref: "",
  },
  {
    time: "13:14",
    kind: "handoff",
    packet: "A.1",
    title: "Branch m1-a-1 handed off",
    who: "Sol",
    detail: "Two files changed, build passes, focused tests 4 of 4.",
    ref: "",
  },
  {
    time: "13:28",
    kind: "review",
    packet: "A.1",
    title: "Changes requested",
    who: "Claude Opus",
    detail: "An empty theme version was still accepted by the identity contract. One finding, one file.",
    ref: "",
  },
  {
    time: "13:30",
    kind: "correction",
    packet: "A.1",
    title: "The packet’s one correction spent",
    who: "Coordinator",
    detail: "Fix limited to the named finding, same reviewer. No budget left on A.1.",
    ref: "",
  },
  {
    time: "13:48",
    kind: "accepted",
    packet: "A.1",
    title: "A.1 accepted, contract frozen at 9d3e1a2",
    who: "Coordinator",
    detail: "Locks released and A.2 became dispatchable.",
    ref: "A.1",
  },
  {
    time: "13:49",
    kind: "dispatch",
    packet: "A.2",
    title: "Terra dispatched on the Runtime Package",
    who: "Coordinator",
    detail: "Base 9d3e1a2, one Runtime file and one Runtime test, 60-minute response boundary.",
    ref: "",
  },
  {
    time: "14:30",
    kind: "report",
    packet: "A.2",
    title: "Status check answered",
    who: "Terra",
    detail: "Step 3 of 5, no blocker, ETA unknown. Inside the boundary.",
    ref: "",
  },
  {
    time: "14:52",
    kind: "blocked",
    packet: "A.2",
    title: "Terra stopped rather than guess",
    who: "Terra",
    detail: "Theme-free outputs still need a theme version, and the frozen contract rejects an empty one.",
    ref: "",
  },
  {
    time: "14:56",
    kind: "escalated",
    packet: "A.2",
    title: "Coordinator passed it up",
    who: "Coordinator",
    detail: "Scope and corrections are the Coordinator’s to rule on; a frozen contract is not.",
    ref: "A.2",
  },
];

/** Real, verbatim — the timeline's own trailing placeholder note. */
export const HISTORY_EMPTY_NOTE = "A.3 through A.7 have not been dispatched — nothing to record yet.";
