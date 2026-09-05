# M2 Wave C — Packet Thread, Static Fixtures — Candidate 01

**Slice ID:** `MB-SLICE-M2-C1-PACKET-THREAD-01`
**Status:** `Frozen — Pending Implementation`. Full Decision Fidelity review exhaustively verified every fixture value byte-accurate against the reference file and found exactly 1 blocking finding (a test-count/total mismatch between the code and the contract's own proof sections) plus 1 non-blocking wording fix; one targeted planning correction resolved both and was approved by targeted verification. No further planning correction is available for this slice.
**Base:** `6fc20da` (`origin/master`)

## Scope, deliberately minimal

Wave C1 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the packet
thread view, rendering rows, avatars, and the grouping rule against real
fixture message data — **no decision card, no plan checklist, no
fidelity record, no crash card, no composer**. Those are separate, later
slices (C3 decision card, C4 fidelity record, C5 crash card; the plan
checklist and cadence indicator are new, not-yet-named roadmap items this
contract adds explicitly below, since the real fixture data this slice
must use contains both and the roadmap never separately named them).

**This slice does not wire `PacketThread` into `DesktopShell` or
`App.tsx`.** `PacketThread` is a standalone component, exactly like B4's
`MobileShell` — reachable only by direct import, not by clicking
anything in the currently-shipped app. Wiring it in requires adding
packet-list nav rows to `DesktopShell`'s nav (a real, separate change to
a frozen B3 file) and deciding how the shell's content pane switches
between its four existing static views and a selected packet's thread —
a real integration decision this slice has no mandate to make alongside
everything else it already does. B3's own contract already anticipated
this exact split: *"C1 adds the packet-list rows into the same nav
between History and the divider"* — that wiring is this program's next
slice after this one, not part of it.

**Fixture data is transcribed verbatim from the reference file's real
`ENTRIES['A.2']` array — nothing is invented.** Per this program's
standing rule (the design handoff's own build instructions: *"Ask
[the Owner] before inventing any data, endpoint, or copy that isn't in
the README"*), and per the README's Fidelity rule (the reference file
wins over the README's own prose on any disagreement), this slice uses
`Atlas Explorations.dc.html`'s actual `ENTRIES` constant — the same
object the live reference app renders — as its one and only fixture
source, not a paraphrase or an invented example thread. `A.2` (not
`A.1`) is used because it is the reference app's own default selection
(`state.sel = 'A.2'`).

**Several exact values in the reference file differ from the README's
own prose paraphrase of this screen — resolved per the Fidelity rule,
each one checked directly, not assumed:**

| Value | README prose says | Reference file (`Atlas Explorations.dc.html`) actually says | Used here |
|---|---|---|---|
| Name weight | 600 | `font-weight:700` | **700** |
| Name font size | (unstated) | `font-size:15px` | **15px** |
| Role font size | 12.5px | `font-size:13px` | **13px** |
| Body font size | 13.5–14.5px | `font-size:15px` | **15px** |
| Body line-height | 1.55 | `line-height:1.6` | **1.6** |
| Body max-width | 60ch | `max-width:62ch` | **62ch** |
| Coordinator avatar bg | (README's separate "Avatar palettes" list says `#F2EEF8`, which is this codebase's existing `colors.neutralChip` token) | `AV.co = ['#EFEBF2', '#4A4155', 'CO']` | **`#EFEBF2`** (disclosed literal — `colors.neutralChip` is the wrong value for this specific use, confirmed by direct comparison, not reused here) |

Every other avatar color (Implementor, Reviewer, Owner, Architect agent)
matches an existing B2 token exactly (checked below); only the
Coordinator background is a real, confirmed discrepancy.

Source quote (`Atlas Explorations.dc.html`, the thread row template and
the `ENTRIES`/`AV`/`AV_NAME`/`ROLE_OF` data, elided to the parts this
slice implements):

```js
const AV = { ar: ['#E7E1FB','#3F1FC0','AR'], ow: ['#8C6BFF','#FFFFFF','OW'],
  co: ['#EFEBF2','#4A4155','CO'], wk: ['#EBE4FF','#4A28CC','TE'],
  rv: ['#FBEDE7','#A9522B','CL'], ok: ['#E4F6EE','#1F6B4E','CO'],
  by: ['#FEF3E2','#8A5A08','15'] };
const AV_NAME = { You:'OW', 'Architect agent':'AR', Sol:'SO', Terra:'TE',
  'Claude Opus':'CL', Coordinator:'CO', Boundary:'15' };
const ROLE_OF = { co:'', wk:'Implementor', rv:'Reviewer', ok:'', by:'',
  ow:'Owner', ar:'Architect · agent' };

const ENTRIES = {
  'A.2': [
    { k:'co', who:'Coordinator', text:'Terra, base is 9d3e1a2. You can write one Runtime file and one Runtime test. One correction allowed, and you have 60 minutes before I expect a response.', time:'13:49' },
    { k:'wk', who:'Terra', text:'Base verified, worktree clean. 200k of context available, no pressure.', time:'13:51', plan:{ name:"Terra's task list", summary:'2 complete · 1 active · 2 open', steps:[
      ['Read the frozen-presentation contract from A.1','done'],
      ['Derive the per-output Runtime shape without importing UI','done'],
      ['Implement RuntimePackageBuilder and its fixture','now'],
      ['Focused tests against local fixture data','open'],
      ['Hand off for validate-only integration','open'] ] } },
    { k:'co', who:'Coordinator', text:'Status check, once: plan, current step, blocker, and an ETA or unknown.', time:'14:19' },
    { k:'wk', who:'Terra', text:'Step 3 of 5, building the Runtime Package. Writing RuntimePackageBuilder now. No blocker. ETA unknown.', time:'14:30', cadence:true },
    { k:'wk', who:'Terra', text:'Blocked. Outputs with no theme still need a theme version, and the A.1 contract rejects an empty one. I read the contract twice and tried a derived hash — both violate the frozen-presentation rule, so this is not mine to decide.', time:'14:52' },
    { k:'co', who:'Coordinator', text:'Terra raised this to me first. I can rule on scope, corrections and dispatch — I cannot widen a frozen contract, so this one goes to the owner. Terra holds its worktree meanwhile.', time:'14:56', escalate:true },
  ],
};
```

```js
// grouping (renderVals): raw.map((e,i) => {
//   const prev = raw[i-1];
//   const grouped = prev && prev.who === e.who && !prev.plan && !prev.cadence && !prev.fid && !e.fid;
//   ...
```

```html
<!-- thread row -->
<div style="display:grid;grid-template-columns:36px minmax(0,1fr);gap:14px;padding:{{ e.pad }} 34px">
  <span style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;
    border-radius:10px;background:{{ e.avBg }};color:{{ e.avColor }};
    font:600 11.5px 'IBM Plex Mono',monospace">{{ e.av }}</span>
  <div style="min-width:0">
    <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:2px">
      <span style="font-weight:700;font-size:15px">{{ e.who }}</span>
      <span style="font-size:13px;color:#8E8299">{{ e.role }}</span>
      <time style="color:#A79BB4;font:500 12px 'IBM Plex Mono',monospace">{{ e.time }}</time>
    </div>
    <p style="margin:0;font-size:15px;line-height:1.6;max-width:62ch;text-wrap:pretty;
      color:{{ e.textColor }}">{{ e.text }}</p>
  </div>
</div>
```

`pad` (row vertical padding) is `'2px'` when grouped (avatar omitted),
`'16px'` otherwise — the exact values `renderVals` computes.
`e.textColor` is `#221C29` (`colors.ink`) for every role except `by`,
which uses `#6C6376` (`colors.inkSecondary`) — this fixture's own two
roles (`co`, `wk`) both use the default.

**Explicitly not built by this slice** (present as inert, typed fixture
fields, carried over verbatim from the reference data, rendered by
nothing yet):

- `plan` (the task-list checklist card on Terra's second message) — its
  own future slice.
- `cadence` (the small progress indicator on Terra's status-check
  reply) — its own future slice.
- `escalate` (the reference file style change on Coordinator's final
  message, marking it as an escalation) — its own future slice.
- `closure` (used only by `A.1`'s data, not `A.2`'s — not exercised by
  this slice's chosen fixture at all).
- The `fid` (fidelity record) field the grouping rule's `!prev.fid &&
  !e.fid` clause references — this field does not exist on any `A.2`
  entry and is not yet part of this codebase's `ThreadEntry` type (C4
  adds it, and extends the grouping function's condition to check it
  then; this slice's grouping function correctly omits a check for a
  field that cannot exist yet).
- The composer, the header summary row, the eyebrow/title line above
  the thread — all separate, later work.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C1-PACKET-THREAD-01` |
| `phase` | `PendingImplementation` |
| `current_actor` | `none` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:6fc20da","git:full-planning-review-head:8d7c32f1f32ffdcd298c39b0892b1b984340283a","review:decision-fidelity:request-changes:1-blocking-finding","git:corrected-planning-head:9df116338611460496b74c2e1202b848aee8b4bc","review:targeted-decision-fidelity-verification:approve"]` |

## Exact file contents

`apps/atlas/src/thread/fixtures.ts` (new — the fixture data and its
types; no rendering logic):

```ts
export type EntryRoleKey = "co" | "wk" | "rv" | "ok" | "by" | "ow" | "ar";

export interface ThreadPlanStep {
  text: string;
  status: "done" | "now" | "open";
}

export interface ThreadPlan {
  name: string;
  summary: string;
  steps: ThreadPlanStep[];
}

export interface ThreadEntry {
  k: EntryRoleKey;
  who: string;
  text: string;
  time: string;
  // Present in the real reference data; not yet rendered by any slice.
  plan?: ThreadPlan;
  cadence?: boolean;
  escalate?: boolean;
  closure?: string;
}

/**
 * Transcribed verbatim from Atlas Explorations.dc.html's real
 * `ENTRIES['A.2']` array — the reference app's own default-selected
 * packet's thread. Do not edit a value here without re-checking that
 * file; this is fixture content, not this program's own prose.
 */
export const PACKET_A2_ENTRIES: ThreadEntry[] = [
  {
    k: "co",
    who: "Coordinator",
    text: "Terra, base is 9d3e1a2. You can write one Runtime file and one Runtime test. One correction allowed, and you have 60 minutes before I expect a response.",
    time: "13:49",
  },
  {
    k: "wk",
    who: "Terra",
    text: "Base verified, worktree clean. 200k of context available, no pressure.",
    time: "13:51",
    plan: {
      name: "Terra's task list",
      summary: "2 complete · 1 active · 2 open",
      steps: [
        { text: "Read the frozen-presentation contract from A.1", status: "done" },
        { text: "Derive the per-output Runtime shape without importing UI", status: "done" },
        { text: "Implement RuntimePackageBuilder and its fixture", status: "now" },
        { text: "Focused tests against local fixture data", status: "open" },
        { text: "Hand off for validate-only integration", status: "open" },
      ],
    },
  },
  {
    k: "co",
    who: "Coordinator",
    text: "Status check, once: plan, current step, blocker, and an ETA or unknown.",
    time: "14:19",
  },
  {
    k: "wk",
    who: "Terra",
    text: "Step 3 of 5, building the Runtime Package. Writing RuntimePackageBuilder now. No blocker. ETA unknown.",
    time: "14:30",
    cadence: true,
  },
  {
    k: "wk",
    who: "Terra",
    text: "Blocked. Outputs with no theme still need a theme version, and the A.1 contract rejects an empty one. I read the contract twice and tried a derived hash — both violate the frozen-presentation rule, so this is not mine to decide.",
    time: "14:52",
  },
  {
    k: "co",
    who: "Coordinator",
    text: "Terra raised this to me first. I can rule on scope, corrections and dispatch — I cannot widen a frozen contract, so this one goes to the owner. Terra holds its worktree meanwhile.",
    time: "14:56",
    escalate: true,
  },
];

/** `AV_NAME` from the reference file — explicit initials by real name. */
export const INITIALS_BY_NAME: Record<string, string> = {
  You: "OW",
  "Architect agent": "AR",
  Sol: "SO",
  Terra: "TE",
  "Claude Opus": "CL",
  Coordinator: "CO",
  Boundary: "15",
};

/** `ROLE_OF` from the reference file — the role label shown next to the name. */
export const ROLE_LABEL: Record<EntryRoleKey, string> = {
  co: "",
  wk: "Implementor",
  rv: "Reviewer",
  ok: "",
  by: "",
  ow: "Owner",
  ar: "Architect · agent",
};
```

Source quote (README, "Avatar palettes" list — for direct comparison
against `AVATAR_PALETTE` below; used for every role except `co`, per the
discrepancy table above):

> Avatar palettes (bg, ink, initials): Coordinator `#F2EEF8`/`#4A4155`;
> Implementor `#EBE4FF`/`#4A28CC`; Reviewer `#FBEDE7`/`#A9522B`; Owner
> `#8C6BFF`/`#FFFFFF` (`OW`); Architect agent `#E7E1FB`/`#3F1FC0` (`AR`).

`apps/atlas/src/thread/PacketThread.module.css` (new — CSS Module,
`var(--atlas-*)` only, following the exact B3/B4 pattern):

```css
.thread {
  display: flex;
  flex-direction: column;
}

.row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 14px;
  padding: 0 34px;
}

.avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font: 600 11.5px var(--atlas-font-mono);
}

.body {
  min-width: 0;
}

.nameRow {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 2px;
}

.name {
  font-weight: 700;
  font-size: 15px;
  color: var(--atlas-ink);
}

.role {
  font-size: 13px;
  color: var(--atlas-ink-muted);
}

.time {
  color: var(--atlas-ink-faint);
  font: 500 12px var(--atlas-font-mono);
}

.text {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  max-width: 62ch;
  text-wrap: pretty;
}
```

`apps/atlas/src/thread/PacketThread.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import {
  INITIALS_BY_NAME,
  PACKET_A2_ENTRIES,
  ROLE_LABEL,
  type EntryRoleKey,
  type ThreadEntry,
} from "./fixtures";
import styles from "./PacketThread.module.css";

const SHELL_VARS = {
  "--atlas-ink": colors.ink,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-ink-faint": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * `AV` from the reference file. Two values have no equivalent B2 token
 * and stay disclosed literals, each checked directly against
 * `Atlas Explorations.dc.html`'s real `AV` constant, not invented:
 * `co`'s background (`#EFEBF2` — a real, checked mismatch against this
 * codebase's existing `colors.neutralChip`, see the discrepancy table
 * above) and `by`'s background (`#FEF3E2` — never rendered by this
 * slice's chosen `A.2` fixture, which uses only the `co`/`wk` roles,
 * but included here for a complete, correct palette matching the
 * README's own "Avatar palettes" enumeration). Every other value below
 * is a direct property of the real `colors` token.
 */
const AVATAR_PALETTE: Record<EntryRoleKey, { bg: string; ink: string }> = {
  co: { bg: "#EFEBF2", ink: "#4A4155" },
  wk: { bg: colors.accentWash[0], ink: colors.accentHover },
  rv: { bg: colors.reviewWash, ink: colors.reviewText },
  ok: { bg: colors.successWash, ink: colors.successText },
  by: { bg: "#FEF3E2", ink: colors.warningText },
  ow: { bg: colors.accentLight, ink: colors.surface },
  ar: { bg: colors.accentWash[1], ink: colors.accentDeepest },
};

const FALLBACK_INITIALS: Record<EntryRoleKey, string> = {
  co: "CO",
  wk: "TE",
  rv: "CL",
  ok: "CO",
  by: "15",
  ow: "OW",
  ar: "AR",
};

/**
 * The exact grouping rule from `Atlas Explorations.dc.html`'s
 * `renderVals`, minus the `fid` check (that field doesn't exist on
 * `ThreadEntry` yet — C4 adds it, and extends this function's
 * condition then, matching the reference file's own full rule).
 */
export function computeShowAvatar(entries: ThreadEntry[], index: number): boolean {
  const entry = entries[index];
  const prev = entries[index - 1];
  const grouped = !!prev && prev.who === entry.who && !prev.plan && !prev.cadence;
  return !grouped;
}

function textColorFor(entry: ThreadEntry): string {
  return entry.k === "by" ? colors.inkSecondary : colors.ink;
}

export function PacketThread() {
  return (
    <div className={styles.thread} style={SHELL_VARS}>
      {PACKET_A2_ENTRIES.map((entry, index) => {
        const showAvatar = computeShowAvatar(PACKET_A2_ENTRIES, index);
        const palette = AVATAR_PALETTE[entry.k];
        const initials = INITIALS_BY_NAME[entry.who] ?? FALLBACK_INITIALS[entry.k];
        return (
          <div
            key={`${entry.who}-${entry.time}`}
            className={styles.row}
            style={{ paddingTop: showAvatar ? 16 : 2, paddingBottom: showAvatar ? 16 : 2 }}
          >
            {showAvatar ? (
              <span
                className={styles.avatar}
                style={{ background: palette.bg, color: palette.ink }}
                aria-hidden="true"
              >
                {initials}
              </span>
            ) : (
              <span aria-hidden="true" />
            )}
            <div className={styles.body}>
              {showAvatar ? (
                <div className={styles.nameRow}>
                  <span className={styles.name}>{entry.who}</span>
                  <span className={styles.role}>{ROLE_LABEL[entry.k]}</span>
                  <time className={styles.time}>{entry.time}</time>
                </div>
              ) : null}
              <p className={styles.text} style={{ color: textColorFor(entry) }}>
                {entry.text}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default PacketThread;
```

`apps/atlas/src/thread/PacketThread.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { computeShowAvatar, PacketThread } from "./PacketThread";
import { PACKET_A2_ENTRIES, type ThreadEntry } from "./fixtures";

afterEach(cleanup);

describe("PacketThread", () => {
  it("renders all six real fixture messages, in order, with their exact body text", () => {
    render(<PacketThread />);
    const bodies = screen.getAllByText(/./, { selector: "p" }).map((p) => p.textContent);
    expect(bodies).toEqual(PACKET_A2_ENTRIES.map((e) => e.text));
  });

  it("shows the avatar and name row on every entry in this fixture (no consecutive same-author pair without an intervening plan/cadence entry)", () => {
    render(<PacketThread />);
    // Every one of the 6 fixture entries in A.2 is either a different
    // author than the previous one, or immediately follows a
    // plan/cadence-bearing entry from the same author — so all 6 show
    // their own avatar and name row. This is a real, checked property
    // of the actual fixture data, not an assumption.
    expect(screen.getAllByText("Coordinator")).toHaveLength(3);
    expect(screen.getAllByText("Terra")).toHaveLength(3);
  });

  it("shows the correct role label next to each name (Coordinator: none, Terra: Implementor)", () => {
    render(<PacketThread />);
    expect(screen.getAllByText("Implementor")).toHaveLength(3);
  });

  it("renders the Coordinator avatar with the reference file's real background, not the neutralChip token's value", () => {
    // colors.neutralChip is "#F2EEF8" — a real, different token this
    // avatar must NOT use. jsdom reports computed inline styles as
    // rgb(...); #F2EEF8 = rgb(242,238,248), #EFEBF2 (the correct,
    // reference-file value) = rgb(239,235,242) — both spelled out
    // explicitly so this assertion actually distinguishes them, rather
    // than comparing an rgb() string to a hex string that could never
    // match either way.
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<PacketThread />);
    const avatars = Array.from(container.querySelectorAll('[aria-hidden="true"]')).filter(
      (el) => el.textContent === "CO",
    );
    expect(avatars.length).toBeGreaterThan(0);
    for (const avatar of avatars) {
      expect((avatar as HTMLElement).style.background).toBe("rgb(239, 235, 242)");
      expect((avatar as HTMLElement).style.background).not.toBe("rgb(242, 238, 248)");
    }
  });

  it("computeShowAvatar: a real consecutive same-author pair with no intervening card groups (avatar omitted)", () => {
    // Synthetic data, for algorithm verification only — not product
    // fixture content. Two plain messages from the same author with
    // nothing between them.
    const synthetic: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00" },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(synthetic, 0)).toBe(true);
    expect(computeShowAvatar(synthetic, 1)).toBe(false);
  });

  it("computeShowAvatar: never groups across a plan- or cadence-bearing entry, even with the same author", () => {
    const syntheticPlan: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00", plan: { name: "x", summary: "y", steps: [] } },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(syntheticPlan, 1)).toBe(true);

    const syntheticCadence: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00", cadence: true },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(syntheticCadence, 1)).toBe(true);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PacketThread />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `App.tsx`, `DesktopShell.tsx`, or any
   other existing component — standalone, exactly like B4's
   `MobileShell`.
2. Every fixture message's `who`/`text`/`time`/`plan`/`cadence`/
   `escalate` value is transcribed verbatim from
   `Atlas Explorations.dc.html`'s real `ENTRIES['A.2']` — none invented.
   Every color value is either a real B2 token or a disclosed literal
   checked directly against the same reference file (the discrepancy
   table above), never assumed from the README's separate prose
   paraphrase of this screen.
3. No file under `apps/atlas/src/tokens/` or `apps/atlas/src/shell/` is
   modified.
4. The grouping function (`computeShowAvatar`) omits the reference
   file's `fid` check because no such field exists on `ThreadEntry` yet
   — this is a deliberate, disclosed simplification tied to a named
   future slice (C4), not a silent behavior gap.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/thread/fixtures.ts` (new)
- `apps/atlas/src/thread/PacketThread.module.css` (new)
- `apps/atlas/src/thread/PacketThread.tsx` (new)
- `apps/atlas/src/thread/PacketThread.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, everything under
`apps/atlas/src/shell/`, and everything under `apps/atlas/src/tokens/`
are untouched.

The 7 named tests (**corrected — blocking finding from Decision
Fidelity review: the test file's code block actually contains 7 `it(...)`
cases, not 6, and the resulting total is 24, not 23** — the file content
itself was always correct; only this section's and M0-D12 element 5's
own counts were wrong), run from `apps/atlas/`: `npm run typecheck`,
`npm run lint`, and `npm test` must all exit `0`, covering the new test
file above plus every existing `apps/atlas` test continuing to pass
unmodified — 24 total after this slice (17 existing + 7 new). `npm run
build` must still succeed; `PacketThread` is not expected to appear in
the `dist/` bundle, matching B2's and B4's own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `PacketThread` renders the real `A.2` fixture
   thread's six messages, in order, with byte-accurate body text, the
   correct avatar/name/role/time for each, and the reference file's
   exact grouping behavior (including the "never group across a
   card-bearing entry" rule), using only real token values or explicitly
   disclosed, reference-file-checked literals.
2. **Operating and threat model:** a trusted local dev box; no user
   interaction yet (this view has none — no composer, no clickable
   element).
3. **Explicit exclusions:** the plan checklist, cadence indicator,
   escalate styling, fidelity record, decision card, crash card,
   composer, header summary — all separate, later slices; any wiring
   into `DesktopShell`/`App.tsx`; any data beyond the one chosen fixture
   packet (`A.2`).
4. **Assurance level:** practical component-rendering correctness with
   byte-exact fixture-data transcription, proportionate to a read-only
   view with no data dependency and no consumer yet — identical
   assurance posture to B2/B4, with the added rigor this slice's own
   fixture-transcription responsibility requires.
5. **Acceptance proof:** the 7 named tests, the existing 17 `apps/atlas`
   tests continuing to pass (24 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color either a real token property or a
   literal checked directly against the reference file.
7. **Proportionality ceiling:** one view component, one fixtures module,
   one CSS Module, one pure grouping function; no plan/cadence/fidelity/
   decision/crash rendering; no wiring; no second fixture packet.
8. **Stop and escalation rule:** wiring `PacketThread` into
   `DesktopShell`'s nav and content pane is a new, separately reviewed
   slice — not something this one decides implicitly by choosing not to
   wire it in. Extending `ThreadEntry`/`computeShowAvatar` for `fid` is
   C4's job, not this slice's. A discovered proof/contract defect
   against a frozen slice terminally returns that slice. One planning
   correction and one implementation correction are the maximum
   available.
