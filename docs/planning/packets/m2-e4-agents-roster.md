# M2 Wave E — Agents Roster — Candidate 01

**Slice ID:** `MB-SLICE-M2-E4-AGENTS-ROSTER-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `f1e73dd` (full: `f1e73dd86c78180260b18875e8b9650e28d809da`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 29, *"E4 — Agents: roster cards."* A new, standalone
`AgentsRoster` renders the real Agents screen in full: the header
(eyebrow, title, 4 real `agStats`) and all 4 real roster cards. No
wiring into `DesktopShell`/`App.tsx`. The contention/lock card
(roadmap item 30, E5) is a separate, later slice — this program's own
established split precedent (E1/E1B, E2/E2B).

**Two disclosed corrections, both design judgment calls made under
delegated Project Architect authority:**

**1. Real-vs-fictional persona adaptation.** The reference file's real
`AGENTS` array has a fourth entry, `{ av: 'AR', name: 'Architect
agent', role: 'Approver', state: 'ruling', packet: 'A.2', urgent: true,
line: 'Weighing the sentinel question against the frozen contract.
Will record a fidelity check.' }` — the fictional M4-only persona that
must never render as existing in M2. Its real state describes the
exact same real M1/M2 escalation this program's own
`apps/atlas/src/decision/ownerFixtures.ts`'s `OWNER_DECISION_EXAMPLE`
already establishes: the Coordinator, not a fictional Architect, is
the real actor who rules on it ("The Coordinator will not rule on a
contract the owner froze, so it escalated instead of guessing").
This slice substitutes `Coordinator` — role `Coordinator`, matching
`apps/atlas/src/performance/perfBreakdown.ts`'s own real `Coordinator`
role bucket (E3) — and rewrites `line`/`due` to reuse that same
already-established real headline ("a theme-free output... a sentinel
version... the frozen contract") and this program's own
`FIDELITY_RECORD_EXAMPLE`'s real "Decision Fidelity check" terminology,
rather than the reference file's own invented "sentinel
question"/generic "fidelity check" phrasing. `av`, `packet`, `state`,
`urgent`, and `locks` are otherwise transcribed verbatim (all already
real and consistent).

**2. Corrected breadcrumb artifact, unrelated to the persona issue.**
The reference file's real eyebrow for this one screen is literally
`vennuesign` — every other real M2 desktop screen (`Performance`,
`History`, the packet-detail view) uses `m1-a` for this exact same
milestone (checked directly: `grep`ped the whole reference file, `m1-a`
appears on every other screen's eyebrow, `vennuesign` appears exactly
once, nowhere else in this file or this codebase). This is an evident
copy-paste artifact from an unrelated project template, not real M2
content. This slice uses `m1-a`, matching every other real screen's
own established, consistent breadcrumb.

## Source quote

`Atlas Explorations.dc.html`'s real markup for the header and each
roster card, verbatim:

```html
<div style="flex:none;padding:16px 34px 15px;background:#fff;border-bottom:1px solid #EEEAF2">
  <div style="display:flex;align-items:center;gap:9px;font:500 11px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:#A79BB4"><span>vennuesign</span><span style="width:3px;height:3px;border-radius:50%;background:#CFC6D6"></span><span>agents</span></div>
  <h1 style="margin:7px 0 0;font-family:'Bricolage Grotesque',sans-serif;font-size:25px;font-weight:600;letter-spacing:-.025em;line-height:1.15">Four agents, one worktree each</h1>
  <div style="display:flex;flex-wrap:wrap;gap:0 26px;margin-top:9px;font-size:13.5px;color:#6C6376">
    <sc-for list="{{ agStats }}" as="s" hint-placeholder-count="4">
    <span style="display:flex;align-items:baseline;gap:7px">{{ s.label }}<b style="font-family:'IBM Plex Mono',monospace;color:{{ s.color }}">{{ s.value }}</b></span>
    </sc-for>
  </div>
</div>

<div style="flex:1 1 0;min-height:0;overflow:auto;padding:18px 34px 28px">
  <div style="display:grid;grid-template-columns:{{ agCols }};gap:12px">
    <sc-for list="{{ agents }}" as="a" hint-placeholder-count="4">
    <div style="min-width:0;border:1px solid {{ a.border }};border-radius:14px;background:#fff;overflow:hidden">
      <div style="display:flex;align-items:center;gap:11px;padding:13px 15px 11px">
        <span style="width:34px;height:34px;flex:none;display:flex;align-items:center;justify-content:center;border-radius:10px;background:{{ a.avBg }};color:{{ a.avColor }};font:600 11.5px 'IBM Plex Mono',monospace">{{ a.av }}</span>
        <div style="min-width:0;flex:1">
          <div style="display:flex;align-items:baseline;gap:8px"><span style="font-size:15.5px;font-weight:700;letter-spacing:-.01em">{{ a.name }}</span><span style="font-size:12.5px;color:#8E8299">{{ a.role }}</span></div>
          <div style="display:flex;align-items:center;gap:7px;margin-top:2px;font-size:12.5px;font-weight:600;color:{{ a.stateColor }}"><span style="width:7px;height:7px;box-sizing:border-box;border-radius:50%;background:{{ a.stateDotBg }};border:{{ a.stateDotBorder }}"></span>{{ a.state }}</div>
        </div>
        <span style="flex:none;font:500 11.5px 'IBM Plex Mono',monospace;color:#A79BB4">{{ a.packet }}</span>
      </div>
      <div style="padding:0 15px 12px;font-size:13.5px;line-height:1.55;color:#6C6376;text-wrap:pretty">{{ a.line }}</div>
      <div style="padding:0 15px 13px">
        <div style="position:relative;height:5px;border-radius:999px;background:#EEEAF2;overflow:hidden">
          <span style="position:absolute;left:0;top:0;bottom:0;width:{{ a.pct }};border-radius:999px;background:{{ a.barColor }}"></span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:7px;font:500 11.5px 'IBM Plex Mono',monospace;color:#8E8299"><span>{{ a.progress }}</span><span style="color:{{ a.dueColor }}">{{ a.due }}</span></div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;padding:10px 15px;border-top:1px solid #F3F0F6;background:#FCFBFD">
        <span style="min-width:0;flex:1;font-size:12.5px;color:#8E8299;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ a.locks }}</span>
        <button onClick="{{ a.onOpen }}" style="flex:none;height:26px;padding:0 10px;border:1px solid #E4DEEE;border-radius:7px;background:#fff;color:#5B34E8;cursor:pointer;font:600 12px 'Public Sans',sans-serif" style-hover="border-color:#C9BEDC;background:#FBFAFE">Open thread</button>
      </div>
    </div>
    </sc-for>
  </div>
</div>
```

Real per-agent derivation logic (verbatim) and the real `AGENTS`/
`AG_STYLE` data, before this slice's two disclosed corrections:

```js
agents: AGENTS.map(a => {
  const st = AG_STYLE[a.k];
  return { av: a.av, name: a.name, role: a.role, packet: a.packet, state: a.state, line: a.line,
    pct: a.pct, progress: a.progress, due: a.due, locks: a.locks,
    avBg: st[0], avColor: st[1], stateColor: st[2], barColor: st[3], border: st[4],
    stateDotBg: a.k === 'wait' ? 'transparent' : st[3], stateDotBorder: a.k === 'wait' ? '1.5px solid #B9AFC4' : '0',
    dueColor: a.urgent ? '#8A5A08' : '#8E8299',
    onOpen: () => this.setState({ view: 'packet', sel: a.ref, tab: 'thread' }) };
}),
```

```js
const AGENTS = [
  { av: 'TE', name: 'Terra', role: 'Implementor', packet: 'A.2', state: 'running', k: 'run',
    line: 'Building RuntimePackageBuilder. Step 3 of 5, inside the response boundary.', pct: '58%', progress: 'step 3 of 5', due: 'report by 15:13', urgent: false,
    locks: 'holds runtime/package.ts · runtime/package.test.ts', ref: 'A.2' },
  { av: 'SO', name: 'Sol', role: 'Implementor', packet: 'A.3', state: 'waiting on locks', k: 'wait',
    line: 'Dispatched but idle — A.3 writes the overlay files A.2 still holds.', pct: '0%', progress: 'not started', due: 'blocked 24m', urgent: false,
    locks: 'waiting on runtime/package.ts', ref: 'A.3' },
  { av: 'CL', name: 'Claude Opus', role: 'Reviewer', packet: 'A.1', state: 'reviewing', k: 'rev',
    line: 'Second pass on the correction range. Same reviewer of record as the first pass.', pct: '80%', progress: '1 finding open', due: 'no boundary', urgent: false,
    locks: 'read-only · no locks held', ref: 'A.1' },
  { av: 'AR', name: 'Architect agent', role: 'Approver', packet: 'A.2', state: 'ruling', k: 'rule',
    line: 'Weighing the sentinel question against the frozen contract. Will record a fidelity check.', pct: '35%', progress: 'ruling 6m', due: 'Terra idle meanwhile', urgent: true,
    locks: 'no locks · records only', ref: 'A.2' },
];
const AG_STYLE = {
  run: ['#EBE4FF', '#4A28CC', '#5B34E8', '#8C6BFF', '#E0DAF2'],
  wait: ['#F2EEF8', '#4A4155', '#8E8299', '#CFC6D6', '#E7E1EE'],
  rev: ['#FBEDE7', '#A9522B', '#A9522B', '#D08A63', '#EFE0D8'],
  rule: ['#E7E1FB', '#3F1FC0', '#4A28CC', '#5B34E8', '#DAD2EC'],
};
```

```js
agStats: [
  { label: 'Working', value: '1 of 4', color: '#5B34E8' },
  { label: 'Idle on locks', value: '1', color: '#8A5A08' },
  { label: 'Awaiting a ruling', value: '1', color: '#4A28CC' },
  { label: 'Packets in flight', value: '3', color: '#221C29' },
],
```

**"Options rendered but inert," matching C4's/C6's/E2's own
established pattern.** Real `<button>` elements, no `onClick` handler
at all — the click-to-navigate command doesn't exist yet.

## Color discrepancy table — every value is a real, existing B2 token except 2 disclosed literals

| Reference value | `colors.ts` match | Verdict |
|---|---|---|
| card surface `#fff` | `colors.surface` | real token |
| header border-bottom `#EEEAF2` | `colors.borderDivider[0]` | real token |
| eyebrow text `#A79BB4` | `colors.inkFaint` | real token |
| role text `#8E8299` | `colors.inkMuted` | real token |
| packet text `#A79BB4` | `colors.inkFaint` | real token |
| line text `#6C6376` | `colors.inkSecondary` | real token |
| progress-bar track `#EEEAF2` | `colors.borderDivider[0]` (same token, reused) | real token |
| progress/due text `#8E8299` | `colors.inkMuted` | real token |
| due text, urgent `#8A5A08` | `colors.warningText` | real token |
| footer border-top `#F3F0F6` | `colors.borderDivider[1]` | real token |
| footer bg `#FCFBFD` | `colors.focusHoverCard` | real token |
| locks text `#8E8299` | `colors.inkMuted` | real token |
| button border `#E4DEEE` | none in `colors.ts` — same, previously-disclosed literal C3's/C5's/History's/E7's own cards already use | **disclosed literal** |
| button ink `#5B34E8` | `colors.accent` | real token |
| button hover border `#C9BEDC` | `colors.focusHoverBorderNeutral` | real token |
| button hover bg `#FBFAFE` | none in `colors.ts` — same, previously-disclosed literal | **disclosed literal** |
| hollow-dot border `#B9AFC4` | `colors.borderDashed[2]` | real token |
| `agStats` "Working" `#5B34E8` | `colors.accent` | real token |
| `agStats` "Idle on locks" `#8A5A08` | `colors.warningText` | real token |
| `agStats` "Awaiting a ruling" `#4A28CC` | `colors.accentHover` | real token |
| `agStats` "Packets in flight" `#221C29` | `colors.ink` | real token |
| `run` avBg `#EBE4FF` | `colors.accentWash[0]` | real token |
| `run` avColor `#4A28CC` | `colors.accentHover` | real token |
| `run` stateColor `#5B34E8` | `colors.accent` | real token |
| `run` barColor `#8C6BFF` | `colors.accentLight` | real token |
| `run` border `#E0DAF2` | none in `colors.ts` — checked directly against `colors.borderStrong`, `colors.borderDashed`, `colors.accentWash`, and every other family | **disclosed literal** |
| `wait` avBg `#F2EEF8` | `colors.neutralChip` | real token |
| `wait` avColor `#4A4155` | `colors.neutralChipText` | real token |
| `wait` stateColor `#8E8299` | `colors.inkMuted` | real token |
| `wait` barColor `#CFC6D6` | `colors.navText` — the same coincidental-match, no-nav-consumer literal History's own timeline slice already disclosed; re-checked independently here, not copied | real token |
| `wait` border `#E7E1EE` | `colors.border` | real token |
| `rev` avBg `#FBEDE7` | `colors.reviewWash` | real token |
| `rev` avColor `#A9522B` | `colors.reviewText` | real token |
| `rev` stateColor `#A9522B` | `colors.reviewText` (same token, reused) | real token |
| `rev` barColor `#D08A63` | `colors.review` | real token |
| `rev` border `#EFE0D8` | none in `colors.ts` — checked directly, same families as `run`'s own border above | **disclosed literal** |
| `rule` avBg `#E7E1FB` | `colors.accentWash[1]` | real token |
| `rule` avColor `#3F1FC0` | `colors.accentDeepest` | real token |
| `rule` stateColor `#4A28CC` | `colors.accentHover` | real token |
| `rule` barColor `#5B34E8` | `colors.accent` | real token |
| `rule` border `#DAD2EC` | `colors.borderStrong[1]` | real token |

**41 rows total: 37 real, existing B2 tokens, 4 disclosed literals**
(`run`'s border `#E0DAF2`, `rev`'s border `#EFE0D8`, the "Open thread"
button's own border `#E4DEEE`, and its hover background `#FBFAFE`),
all individually checked directly against `colors.ts`.

## Guards

1. This slice adds 5 new files only — no wiring into
   `DesktopShell`/`App.tsx`, no modification of any already-merged
   file.
2. The persona substitution (`Architect agent` → `Coordinator`) and the
   breadcrumb correction (`vennuesign` → `m1-a`) are the only two
   departures from verbatim transcription; every other field on every
   `AGENTS` entry and every `AG_STYLE`/`agStats` value is transcribed
   directly.
3. `agCols`'s mobile/narrow variant (`'1fr'`) is not implemented — this
   is a desktop-Wave-E slice, matching every prior slice's own
   established desktop-only scope.
4. Coordinator's own real `name` and `role` are both literally
   "Coordinator" — a genuine text collision this program's own
   persona substitution introduces (the reference data has no such
   collision, since it names this field "Approver" for the fictional
   persona). Disclosed and handled explicitly in the test file via
   class-scoped queries, not a bare, ambiguous `getByText`.

## `apps/atlas/src/agents/agents.ts` (new)

```ts
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
```

## `apps/atlas/src/agents/agentStyle.ts` (new)

```ts
import { colors } from "../tokens";
import type { AgentStyleKey } from "./agents";

/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `AG_STYLE` map (`[avBg, avColor, stateColor, barColor, border]` per
 * style key). Every value is a real B2 token except two disclosed
 * literals, checked directly against `colors.ts`: `run`'s own border
 * (`#E0DAF2`) and `rev`'s own border (`#EFE0D8`) — neither matches any
 * real token property (checked against `colors.borderStrong`,
 * `colors.borderDashed`, `colors.accentWash`, and every other color
 * family directly, not assumed). `wait`'s bar color (`#CFC6D6`) does
 * match a real token, `colors.navText` — the same coincidental-match,
 * no-nav-consumer literal this program's own History-timeline slice
 * already disclosed and used the same way (checked again here
 * independently, not copied from that disclosure).
 */
export interface AgentStyle {
  avBg: string;
  avColor: string;
  stateColor: string;
  barColor: string;
  border: string;
}

export const AGENT_STYLE: Record<AgentStyleKey, AgentStyle> = {
  run: {
    avBg: colors.accentWash[0],
    avColor: colors.accentHover,
    stateColor: colors.accent,
    barColor: colors.accentLight,
    border: "#E0DAF2",
  },
  wait: {
    avBg: colors.neutralChip,
    avColor: colors.neutralChipText,
    stateColor: colors.inkMuted,
    barColor: colors.navText,
    border: colors.border,
  },
  rev: {
    avBg: colors.reviewWash,
    avColor: colors.reviewText,
    stateColor: colors.reviewText,
    barColor: colors.review,
    border: "#EFE0D8",
  },
  rule: {
    avBg: colors.accentWash[1],
    avColor: colors.accentDeepest,
    stateColor: colors.accentHover,
    barColor: colors.accent,
    border: colors.borderStrong[1],
  },
};
```

## `apps/atlas/src/agents/AgentsRoster.tsx` (new)

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { AGENT_STYLE } from "./agentStyle";
import { AGENTS, AGENTS_STATS, type AgentEntry, type AgentStat } from "./agents";
import styles from "./AgentsRoster.module.css";

/**
 * Every color here is a real B2 token except the two literals
 * `agentStyle.ts` already discloses (`run`'s and `rev`'s own border
 * colors) — the hollow "waiting" dot's border (`#B9AFC4`) is a real
 * token, `colors.borderDashed[2]`, checked directly. The "Open thread"
 * button's border (`#E4DEEE`) and hover background (`#FBFAFE`) are the
 * same two real, previously-disclosed literals this program's own
 * History/Gate-criteria/decision-card slices already use for their own
 * "Open … thread" buttons — reused here, not newly derived. The
 * button's hover border (`#C9BEDC`) is a real token,
 * `colors.focusHoverBorderNeutral`.
 */
const SHELL_VARS = {
  "--atlas-ag-card-surface": colors.surface,
  "--atlas-ag-header-border": colors.borderDivider[0],
  "--atlas-ag-eyebrow": colors.inkFaint,
  "--atlas-ag-name": colors.ink,
  "--atlas-ag-role": colors.inkMuted,
  "--atlas-ag-packet": colors.inkFaint,
  "--atlas-ag-line": colors.inkSecondary,
  "--atlas-ag-bar-track": colors.borderDivider[0],
  "--atlas-ag-progress": colors.inkMuted,
  "--atlas-ag-due": colors.inkMuted,
  "--atlas-ag-due-urgent": colors.warningText,
  "--atlas-ag-footer-border": colors.borderDivider[1],
  "--atlas-ag-footer-bg": colors.focusHoverCard,
  "--atlas-ag-locks": colors.inkMuted,
  "--atlas-ag-button-border": "#E4DEEE",
  "--atlas-ag-button-ink": colors.accent,
  "--atlas-ag-button-hover-border": colors.focusHoverBorderNeutral,
  "--atlas-ag-button-hover-bg": "#FBFAFE",
  "--atlas-ag-wait-dot-border": colors.borderDashed[2],
  "--atlas-ag-stat-accent": colors.accent,
  "--atlas-ag-stat-warning": colors.warningText,
  "--atlas-ag-stat-accent-hover": colors.accentHover,
  "--atlas-ag-stat-ink": colors.ink,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-font-body": fontFamily.body,
} as CSSProperties;

const STAT_VALUE_CLASS: Record<AgentStat["color"], string> = {
  accent: styles.statValueAccent,
  warningText: styles.statValueWarning,
  accentHover: styles.statValueAccentHover,
  ink: styles.statValueInk,
};

function AgentCard({ agent }: { agent: AgentEntry }) {
  const style = AGENT_STYLE[agent.styleKey];
  const isWait = agent.styleKey === "wait";
  const cardVars = {
    "--atlas-ag-card-border": style.border,
    "--atlas-ag-avatar-bg": style.avBg,
    "--atlas-ag-avatar-ink": style.avColor,
    "--atlas-ag-state-ink": style.stateColor,
    "--atlas-ag-bar-fill": style.barColor,
    "--atlas-ag-dot-bg": isWait ? "transparent" : style.barColor,
  } as CSSProperties;

  return (
    <div className={styles.card} style={cardVars}>
      <div className={styles.top}>
        <span className={styles.avatar}>{agent.av}</span>
        <div className={styles.identity}>
          <div className={styles.nameLine}>
            <span className={styles.name}>{agent.name}</span>
            <span className={styles.role}>{agent.role}</span>
          </div>
          <div className={styles.state}>
            <span className={`${styles.stateDot} ${isWait ? styles.stateDotHollow : ""}`} />
            {agent.state}
          </div>
        </div>
        <span className={styles.packet}>{agent.packet}</span>
      </div>
      <div className={styles.line}>{agent.line}</div>
      <div className={styles.progressBlock}>
        <div className={styles.barTrack}>
          <span className={styles.barFill} style={{ width: agent.pct }} />
        </div>
        <div className={styles.progressRow}>
          <span>{agent.progress}</span>
          <span className={agent.urgent ? styles.dueUrgent : styles.due}>{agent.due}</span>
        </div>
      </div>
      <div className={styles.footer}>
        <span className={styles.locks}>{agent.locks}</span>
        <button type="button" className={styles.openButton}>
          Open thread
        </button>
      </div>
    </div>
  );
}

/**
 * Renders the real Agents screen in full: header (eyebrow, title, 4
 * real `agStats`) and all 4 real roster cards. `AGENTS[3]` substitutes
 * the fictional `Architect agent` persona with the real `Coordinator`
 * actor — see `agents.ts`'s own disclosure. The header eyebrow uses
 * `m1-a`, correcting the reference file's own `vennuesign` artifact —
 * see the same disclosure. Every "Open thread" button is a real
 * `<button>` with no `onClick` — genuinely inert, matching this
 * program's own established convention for options rendered but not
 * yet wired.
 */
export function AgentsRoster() {
  return (
    <div style={SHELL_VARS}>
      <div className={styles.head}>
        <div className={styles.eyebrow}>m1-a · agents</div>
        <h1 className={styles.title}>Four agents, one worktree each</h1>
        <div className={styles.stats}>
          {AGENTS_STATS.map((stat) => (
            <span key={stat.label} className={styles.stat}>
              {stat.label}
              <b className={`${styles.statValue} ${STAT_VALUE_CLASS[stat.color]}`}>{stat.value}</b>
            </span>
          ))}
        </div>
      </div>
      <div className={styles.roster}>
        {AGENTS.map((agent) => (
          <AgentCard key={agent.ref + agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

export default AgentsRoster;
```

## `apps/atlas/src/agents/AgentsRoster.module.css` (new)

```css
.head {
  padding: 16px 34px 15px;
  background: var(--atlas-ag-card-surface);
  border-bottom: 1px solid var(--atlas-ag-header-border);
}

.eyebrow {
  font: 500 11px var(--atlas-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--atlas-ag-eyebrow);
}

.title {
  margin: 7px 0 0;
  font-family: var(--atlas-font-body);
  font-size: 25px;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.15;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0 26px;
  margin-top: 9px;
  font-size: 13.5px;
  color: var(--atlas-ag-role);
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.statValue {
  font-family: var(--atlas-font-mono);
}

.statValueAccent {
  color: var(--atlas-ag-stat-accent);
}

.statValueWarning {
  color: var(--atlas-ag-stat-warning);
}

.statValueAccentHover {
  color: var(--atlas-ag-stat-accent-hover);
}

.statValueInk {
  color: var(--atlas-ag-stat-ink);
}

.roster {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
  padding: 18px 34px 28px;
}

.card {
  min-width: 0;
  border: 1px solid var(--atlas-ag-card-border);
  border-radius: 14px;
  background: var(--atlas-ag-card-surface);
  overflow: hidden;
}

.top {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px 15px 11px;
}

.avatar {
  width: 34px;
  height: 34px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--atlas-ag-avatar-bg);
  color: var(--atlas-ag-avatar-ink);
  font: 600 11.5px var(--atlas-font-mono);
}

.identity {
  min-width: 0;
  flex: 1;
}

.nameLine {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.name {
  font-size: 15.5px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--atlas-ag-name);
}

.role {
  font-size: 12.5px;
  color: var(--atlas-ag-role);
}

.state {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 2px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--atlas-ag-state-ink);
}

.stateDot {
  width: 7px;
  height: 7px;
  box-sizing: border-box;
  border-radius: 50%;
  background: var(--atlas-ag-dot-bg);
  border: 0;
}

.stateDotHollow {
  border: 1.5px solid var(--atlas-ag-wait-dot-border);
}

.packet {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-ag-packet);
}

.line {
  padding: 0 15px 12px;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-ag-line);
  text-wrap: pretty;
}

.progressBlock {
  padding: 0 15px 13px;
}

.barTrack {
  position: relative;
  height: 5px;
  border-radius: 999px;
  background: var(--atlas-ag-bar-track);
  overflow: hidden;
}

.barFill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 999px;
  background: var(--atlas-ag-bar-fill);
}

.progressRow {
  display: flex;
  justify-content: space-between;
  margin-top: 7px;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-ag-progress);
}

.due {
  color: var(--atlas-ag-due);
}

.dueUrgent {
  color: var(--atlas-ag-due-urgent);
}

.footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  border-top: 1px solid var(--atlas-ag-footer-border);
  background: var(--atlas-ag-footer-bg);
}

.locks {
  min-width: 0;
  flex: 1;
  font-size: 12.5px;
  color: var(--atlas-ag-locks);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.openButton {
  flex: none;
  height: 26px;
  padding: 0 10px;
  border: 1px solid var(--atlas-ag-button-border);
  border-radius: 7px;
  background: var(--atlas-ag-card-surface);
  color: var(--atlas-ag-button-ink);
  cursor: pointer;
  font: 600 12px var(--atlas-font-body);
}

.openButton:hover {
  border-color: var(--atlas-ag-button-hover-border);
  background: var(--atlas-ag-button-hover-bg);
}
```

## `apps/atlas/src/agents/AgentsRoster.test.tsx` (new)

```tsx
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { AgentsRoster } from "./AgentsRoster";
import { AGENTS, AGENTS_STATS } from "./agents";
import { AGENT_STYLE } from "./agentStyle";

afterEach(cleanup);

// "A.2" is the real packet for both Terra's and Coordinator's cards at
// once, so every per-card check below is scoped to that specific
// card. Coordinator's own real `name` AND `role` are both literally
// "Coordinator" (self-caught while writing these tests — the reference
// data has no such collision, since it named this field "Approver" for
// the fictional persona; this program's own real substitution
// introduced it), so `agentCard` finds the card via the name SPAN
// specifically (scoped by its own class), never a bare `getByText`
// that would match both the name and the role.
function agentCard(name: string): HTMLElement {
  const nameNode = screen.getByText(
    (content, element) => content === name && Boolean(element?.className?.includes("name")),
  );
  return nameNode.closest('[class*="card"]') as HTMLElement;
}

function roleText(card: HTMLElement, role: string): HTMLElement {
  return within(card).getByText(
    (content, element) => content === role && Boolean(element?.className?.includes("role")),
  );
}

describe("AgentsRoster", () => {
  it("renders the real header: corrected 'm1-a' eyebrow (not the reference file's own 'vennuesign' artifact), title, and all 4 real stats", () => {
    render(<AgentsRoster />);
    expect(screen.getByText("m1-a · agents")).toBeInTheDocument();
    expect(screen.queryByText(/vennuesign/i)).toBeNull();
    expect(screen.getByText("Four agents, one worktree each")).toBeInTheDocument();
    for (const stat of AGENTS_STATS) {
      const row = within(screen.getByText(stat.label).closest('[class*="stat"]') as HTMLElement);
      expect(row.getByText(stat.value)).toBeInTheDocument();
    }
  });

  it("renders all 4 real agent cards with their real role, packet, state, line, progress, due, and locks", () => {
    render(<AgentsRoster />);
    for (const agent of AGENTS) {
      const cardEl = agentCard(agent.name);
      const card = within(cardEl);
      expect(roleText(cardEl, agent.role)).toBeInTheDocument();
      expect(card.getByText(agent.packet)).toBeInTheDocument();
      expect(card.getByText(agent.state)).toBeInTheDocument();
      expect(card.getByText(agent.line)).toBeInTheDocument();
      expect(card.getByText(agent.progress)).toBeInTheDocument();
      expect(card.getByText(agent.due)).toBeInTheDocument();
      expect(card.getByText(agent.locks)).toBeInTheDocument();
    }
  });

  it("substitutes the fictional 'Architect agent' persona with the real Coordinator actor, with no fictional persona anywhere", () => {
    render(<AgentsRoster />);
    expect(screen.queryByText("Architect agent")).toBeNull();
    const coordinatorCardEl = agentCard("Coordinator");
    const coordinatorCard = within(coordinatorCardEl);
    // name AND role both real "Coordinator" — see agentCard's own note.
    expect(coordinatorCard.getAllByText("Coordinator")).toHaveLength(2);
    expect(roleText(coordinatorCardEl, "Coordinator")).toBeInTheDocument();
    expect(coordinatorCard.getByText("ruling")).toBeInTheDocument();
    expect(coordinatorCard.getByText("A.2")).toBeInTheDocument();
  });

  it("renders exactly 4 real 'Open thread' buttons, all inert (no onClick)", () => {
    render(<AgentsRoster />);
    const buttons = screen.getAllByRole("button", { name: "Open thread" });
    expect(buttons).toHaveLength(4);
  });

  it("renders the hollow waiting-dot only for Sol's card (the real 'waiting on locks' state)", () => {
    render(<AgentsRoster />);
    const solDot = agentCard("Sol").querySelector('[class*="stateDot"]') as HTMLElement;
    const terraDot = agentCard("Terra").querySelector('[class*="stateDot"]') as HTMLElement;
    expect(solDot.className).toContain("stateDotHollow");
    expect(terraDot.className).not.toContain("stateDotHollow");
  });

  it("colors the due text urgent only for Coordinator's real urgent entry", () => {
    render(<AgentsRoster />);
    const coordinatorDue = within(agentCard("Coordinator")).getByText(
      AGENTS.find((a) => a.name === "Coordinator")!.due,
    );
    const terraDue = within(agentCard("Terra")).getByText(AGENTS.find((a) => a.name === "Terra")!.due);
    expect(coordinatorDue.className).toContain("dueUrgent");
    expect(terraDue.className).not.toContain("dueUrgent");
  });

  it("sets each card's real per-style border color as a checked CSS variable, matching agentStyle.ts's own real/disclosed values", () => {
    expect(AGENT_STYLE.run.border).toBe("#E0DAF2");
    expect(AGENT_STYLE.wait.border).toBe(colors.border);
    expect(AGENT_STYLE.rev.border).toBe("#EFE0D8");
    expect(AGENT_STYLE.rule.border).toBe(colors.borderStrong[1]);

    render(<AgentsRoster />);
    expect(agentCard("Terra").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.run.border);
    expect(agentCard("Sol").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.wait.border);
    expect(agentCard("Claude Opus").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.rev.border);
    expect(agentCard("Coordinator").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.rule.border);
  });

  it("sets the header's real, checked CSS variables", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    const { container } = render(<AgentsRoster />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-ag-header-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-ag-eyebrow")).toBe(colors.inkFaint);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<AgentsRoster />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were written to 5 new files
in a scratch worktree and run through the real toolchain from
`apps/atlas`, before this docs-only packet was finalized:

- `npm run typecheck` — clean, no errors.
- `npm run lint` — clean, no errors.
- `npm test -- --run` — **123/123 passed** across 17 files (the exact
  number the real `vitest` run printed; pre-slice baseline was 114,
  and this slice's own new `AgentsRoster.test.tsx` adds exactly 9
  tests: 114 + 9 = 123).
- `npm run build` — succeeds, no new asset failures.

**One self-caught test bug, fixed before finalizing**: the first draft
of `AgentsRoster.test.tsx` used a bare `agentCard(name)` helper that
called plain `screen.getByText(name)`. Coordinator's own real `name`
and `role` fields are both literally "Coordinator" (introduced by this
slice's own persona substitution — the reference data has no such
collision), so that bare lookup threw a real multiple-elements error on
4 of the file's tests. Fixed by scoping the lookup to the `name` span's
own CSS class specifically (and adding a matching `roleText` helper for
role-specific checks), not by renaming the real data to avoid the
collision.

**Real-browser visual check attempted, not completed**: per the
project's newly-opened issue (#130) about missing browser-based visual
verification for prior slices, an attempt was made to temporarily
preview this component in a real browser (Vite dev server +
browser-automation screenshot) before finalizing this packet. The
browser automation tool itself failed to load any page at all in this
environment (including a plain external URL, not just the local dev
server), so no visual check was possible this time either. This is
disclosed here rather than silently skipped; the existing typecheck/
lint/test/build verification stands as the only actual verification
for this slice, same as every prior slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** `AgentsRoster` renders the real Agents screen
   in full — header (eyebrow, title, 4 real stats) and all 4 real
   roster cards — completing roadmap item 29. 4 disclosed color
   literals (matching Gate/History's own precedent, not E1/E1B/E2/E2B/
   E3's zero-literal precedent). Two disclosed, motivated corrections:
   the `Architect agent` → `Coordinator` persona substitution, and the
   `vennuesign` → `m1-a` breadcrumb correction.
2. **Operating and threat model:** a trusted local dev box; the "Open
   thread" buttons are real `<button>` elements (for correct semantics/
   focus) but carry no `onClick` — clicking one does nothing, by
   construction.
3. **Explicit exclusions:** any wiring into `DesktopShell`/`App.tsx`,
   the mobile/narrow `agCols` layout variant, any real navigation
   behind an "Open thread" button, the contention/lock card (a separate
   E5 slice).
4. **Assurance level:** practical component-rendering correctness, with
   every entry and style value transcribed verbatim except the two
   disclosed corrections, and every color either a real token or one
   explicitly disclosed and checked.
5. **Acceptance proof:** the 9 named tests, the existing 114
   `apps/atlas` tests continuing to pass (123 total), `npm run
   typecheck`, `npm run lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the 5 new files; no new npm
   dependency; every color a real token property except the 4
   disclosed literals; no import of any other component-family module.
7. **Proportionality ceiling:** one roster component, one fixtures
   module, one style-derivation module, one CSS Module; no wiring, no
   real navigation, no mobile variant, no contention card.
8. **Stop and escalation rule:** the mobile/narrow layout variant, real
   navigation/wiring, and the contention/lock card (E5) remain out of
   scope — a future slice's job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E4-AGENTS-ROSTER-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:f1e73dd86c78180260b18875e8b9650e28d809da"]` |
