/**
 * Transcribed from `Atlas Explorations.dc.html`'s real `AGENTS` array
 * and `agStats` — pure reporting content, with two disclosed
 * corrections. First: the reference file's own `cost.role`-style
 * fourth entry here is `{ av: 'AR', name: 'Architect agent', role:
 * 'Approver', ... }` — the fictional M4-only persona that must never
 * render as existing in M2 (this program's own Wave C/E3 precedent).
 * Its real state (`state: 'ruling'`, `packet: 'A.2'`, `urgent: true`)
 * describes the exact same real M1/M2 escalation this program's own
 * `apps/atlas/src/decision/ownerFixtures.ts` `OWNER_DECISION_EXAMPLE`
 * already establishes — the Coordinator, not a fictional Architect,
 * is the real actor who rules on it ("The Coordinator will not rule on
 * a contract the owner froze, so it escalated instead of guessing").
 * This slice substitutes `Coordinator` (role `Coordinator`, matching
 * `apps/atlas/src/performance/perfBreakdown.ts`'s own real `Coordinator`
 * role bucket) and rewrites `line`/`due` to reuse that same
 * already-established real headline ("a theme-free output... a
 * sentinel version... the frozen contract") and `FIDELITY_RECORD_EXAMPLE`'s
 * own real "Decision Fidelity check" terminology, rather than the
 * reference file's own invented "sentinel question"/generic "fidelity
 * check" phrasing.
 *
 * Second, unrelated correction: the reference file's real breadcrumb
 * eyebrow for this one screen is literally `vennuesign` — every other
 * real M2 desktop screen (`Performance`, `History`, the packet-detail
 * view) uses `m1-a` for this exact same milestone. `vennuesign` does
 * not appear anywhere else in this reference file or this codebase; it
 * is an evident copy-paste artifact from an unrelated project
 * template, not real M2 content. This slice uses `m1-a`, matching
 * every other real screen's own established, consistent breadcrumb.
 */
export type AgentStyleKey = "run" | "wait" | "rev" | "rule";

export interface AgentEntry {
  av: string;
  name: string;
  role: string;
  packet: string;
  state: string;
  styleKey: AgentStyleKey;
  line: string;
  pct: string;
  progress: string;
  due: string;
  urgent: boolean;
  locks: string;
  ref: string;
}

export const AGENTS: AgentEntry[] = [
  {
    av: "TE",
    name: "Terra",
    role: "Implementor",
    packet: "A.2",
    state: "running",
    styleKey: "run",
    line: "Building RuntimePackageBuilder. Step 3 of 5, inside the response boundary.",
    pct: "58%",
    progress: "step 3 of 5",
    due: "report by 15:13",
    urgent: false,
    locks: "holds runtime/package.ts · runtime/package.test.ts",
    ref: "A.2",
  },
  {
    av: "SO",
    name: "Sol",
    role: "Implementor",
    packet: "A.3",
    state: "waiting on locks",
    styleKey: "wait",
    line: "Dispatched but idle — A.3 writes the overlay files A.2 still holds.",
    pct: "0%",
    progress: "not started",
    due: "blocked 24m",
    urgent: false,
    locks: "waiting on runtime/package.ts",
    ref: "A.3",
  },
  {
    av: "CL",
    name: "Claude Opus",
    role: "Reviewer",
    packet: "A.1",
    state: "reviewing",
    styleKey: "rev",
    line: "Second pass on the correction range. Same reviewer of record as the first pass.",
    pct: "80%",
    progress: "1 finding open",
    due: "no boundary",
    urgent: false,
    locks: "read-only · no locks held",
    ref: "A.1",
  },
  {
    av: "CO",
    name: "Coordinator",
    role: "Coordinator",
    packet: "A.2",
    state: "ruling",
    styleKey: "rule",
    line: "Weighing whether a theme-free output gets a sentinel version, or the frozen A.1 contract changes. Will record a Decision Fidelity check.",
    pct: "35%",
    progress: "ruling 6m",
    due: "Terra holding its worktree meanwhile",
    urgent: true,
    locks: "no locks · records only",
    ref: "A.2",
  },
];

export interface AgentStat {
  label: string;
  value: string;
  color: "accent" | "warningText" | "accentHover" | "ink";
}

export const AGENTS_STATS: AgentStat[] = [
  { label: "Working", value: "1 of 4", color: "accent" },
  { label: "Idle on locks", value: "1", color: "warningText" },
  { label: "Awaiting a ruling", value: "1", color: "accentHover" },
  { label: "Packets in flight", value: "3", color: "ink" },
];
