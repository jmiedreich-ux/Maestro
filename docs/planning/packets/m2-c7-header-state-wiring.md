# M2 Wave C — Header Summary / Boundary-Timestamps Single-State-Source Wiring — Candidate 01

**Slice ID:** `MB-SLICE-M2-C7-HEADER-STATE-WIRING-01`
**Status:** `Corrected — Pending Targeted Decision Fidelity Verification`.
Full Decision Fidelity review found every architectural and data claim
correct and returned `REQUEST_CHANGES_MINOR`: one quoted markup block
labeled "verbatim" had silently dropped a real `sc-if` conditional
around the summary row, with no disclosure (unlike the neighboring
button/session-label elision, which was already disclosed correctly).
One targeted planning correction restored the conditional and added
the missing disclosure. No further planning correction is available
for this slice.
**Base:** `a0e6e05` (`origin/master`)

## Scope, deliberately minimal

Wave C7 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md) — the last
item in Wave C. Per the roadmap's own item 18: *"Header summary /
boundary timestamps single-state-source wiring. Enforces the README's
rule: header summary, hero card, boundary timestamps, and 'what
happens next' all derive from one state value — done once, reused
everywhere it recurs (C, F)."* This slice builds that one, reusable
derivation function plus its first real consumer — the packet-thread
header (eyebrow, title, state line, and the `Last report`/`Blocker`/
`Next permitted action` summary row). It does not build the hero card
or the "what happens next" panel (both Wave F, mobile-tab work), and
does not wire the new header into `PacketThread`, `DesktopShell`, or
`App.tsx` — standalone, exactly like every C-wave component before it.

**The rule this slice enforces, verbatim (README, "Interactions &
behavior" section):**

> Picking an option appends resolution messages to the thread and
> updates the header summary, session label, hero card, boundary
> timestamps, and "what happens next" together — they must all read
> from one state value, not be set independently.

This is an architecture rule, not a visual spec: multiple surfaces
must derive from **one** computed state object, never be independently
hand-set. This slice's real contribution is that one function —
`derivePacketHeaderState` — not a new visual card. The hero card and
"what happens next" panel are separate, later Wave F components that
should call this same function (extended, when a real second scenario
exists) rather than re-deriving their own copy of this logic.

**`eyebrow` and `title` are real, transcribed values, minus one
segment checked and found not to be real for this repository.**
Reference file's real packet-header markup (`Atlas Explorations.dc.html`,
elided only where explicitly marked below — corrected: an earlier
draft of this quote dropped the summary row's own `sc-if` conditional
silently, with no disclosure; this version keeps it, matching the
disclosed treatment already given to the button/session-label elision):

```html
<div style="flex:none;padding:16px 34px 0;background:#fff;border-bottom:1px solid #EEEAF2">
  <div style="display:flex;align-items:center;gap:9px;font:500 11px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:#A79BB4"><span>m1-a</span><span style="width:3px;height:3px;border-radius:50%;background:#CFC6D6"></span><span>issue #970</span><span style="width:3px;height:3px;border-radius:50%;background:#CFC6D6"></span><span>{{ cur.id }}</span></div>
  <div style="display:flex;align-items:flex-start;gap:20px;margin-top:7px">
    <div style="min-width:0;flex:1">
      <h1 style="margin:0;font-family:'Bricolage Grotesque',sans-serif;font-size:25px;font-weight:600;letter-spacing:-.025em;line-height:1.15;text-wrap:pretty">{{ cur.title }}</h1>
      <div style="display:flex;align-items:center;gap:8px;margin-top:7px;font-size:13.5px;font-weight:600;color:{{ cur.stateColor }}"><span style="{{ cur.stateDot }}"></span>{{ cur.stateLine }}</div>
    </div>
    <!-- Stop/Start-work button and session label: real, but interactive-command-dependent (Wave D), not built by this slice -->
  </div>
  <sc-if value="{{ cur.isCurrent }}" hint-placeholder-val="{{ true }}">
  <div style="display:flex;flex-wrap:wrap;margin:16px -34px 0;padding:11px 34px;border-top:1px solid #F3F0F6;background:#FCFBFD;gap:0 30px">
    <div style="display:flex;align-items:baseline;gap:8px;font-size:13.5px"><span style="color:#8E8299">Last report</span><b style="font-family:'IBM Plex Mono',monospace">{{ meta.report }}</b></div>
    <div style="display:flex;align-items:baseline;gap:8px;font-size:13.5px"><span style="color:#8E8299">Blocker</span><b style="color:{{ meta.blockerColor }};font-weight:{{ meta.blockerWeight }}">{{ meta.blocker }}</b></div>
    <div style="display:flex;align-items:baseline;gap:8px;font-size:13.5px"><span style="color:#8E8299">{{ meta.nextLabel }}</span><b style="font-family:'IBM Plex Mono',monospace;color:{{ meta.nextColor }}">{{ meta.next }}</b></div>
  </div>
  </sc-if>
</div>
```

Both `sc-if value="{{ cur.isCurrent }}"` conditionals above are real —
`A.2` is always the mockup's own currently-selected/running packet
(`state.sel === 'A.2'`), so `cur.isCurrent` is always true in every
real scenario this program has established, and this slice's
standalone component renders unconditionally as if it were, with no
`isCurrent`-false state to model (there is no real fixture for a
different, non-current packet's header yet).

`PACKETS`'s real `A.2` entry (`Atlas Explorations.dc.html`, verbatim):

```js
{ id: 'A.2', short: 'Runtime Package', title: 'Add output-specific Runtime Package creation', state: 'run' },
```

`cur.id` (`A.2`) and `cur.title` (`Add output-specific Runtime Package
creation`) are both real and transcribed verbatim. The eyebrow's
middle segment, `issue #970`, is **not**: checked directly against
this actual repository (`gh issue view 970 --repo jmiedreich-ux/Maestro`
→ *"Could not resolve to an issue or pull request with the number of
970"*), no such issue exists here. It is mockup-specific flavor from
whatever project the design handoff's own demo data originated from,
not real, verifiable content for Maestro — excluded, not transcribed,
per this program's standing content discipline. The eyebrow is
therefore `m1-a · a.2` (`m1-a` — this program's own real M1 milestone
identifier, already used throughout this session — and the real
packet id), not the three-segment reference version.

**The state-driven fields (`stateLine`, `meta.*`) are only implemented
for the one real trajectory C1's frozen fixture actually contains.**
The reference file's own `blocked` condition (verbatim, checked
directly): `const blocked = cur.id === 'A.2' && s.running && !s.decided;`
— at the mockup's own real initial state (`running: true, decided:
null`, from its own `state = {...}` object), `blocked` evaluates to
`true`. This is not one of two equally-real branches to model: it is
the mockup's own actual default/initial condition for `A.2`, and it is
exactly the state C1's real, frozen `PACKET_A2_ENTRIES` already
depicts (Terra blocked at `14:52`, Coordinator escalating to the owner
at `14:56`). The **only** way to reach the "not blocked" branch in the
reference file is through simulated, interactive resolution state
(`s.decided`/`s.running`, toggled by clicking a decision-card option)
with no single real default and no backing real fixture — `report`,
`nextLabel`, and `next` each fork into multiple values depending on
*which* option was picked. Inventing a specific number for that branch
would be fabricating product content this program has no real source
for. Per this project's own real M0-D14 reporting-honesty convention
(quoted in the README's own domain model: *"reported beats estimated;
an unsupported field reads `unavailable`, never `0`"*), the
not-blocked branch of `derivePacketHeaderState` reports `"unavailable"`
for those three fields rather than a guess — disclosed explicitly, not
silently invented and not silently omitted.

**`meta.blocker` ("theme version for theme-free outputs") is a real,
verbatim reference-file value — a concise label for the same real
blocker C1's fixture describes in longer prose**, not independently
invented: C1's frozen `PACKET_A2_ENTRIES`'s blocked entry (`14:52`)
reads *"Outputs with no theme still need a theme version, and the A.1
contract rejects an empty one..."* — the same real blocker, summarized
by the reference file's own separate `meta` object into the shorter
label this slice transcribes.

**`stateLine` ("Terra is blocked and waiting on your decision") is the
real `mine === true` branch, matching C4's own established choice —
never the fictional `mine === false` "the Architect agent is ruling"
alternative.** Reference file's real ternary (verbatim): `stateLine:
cur.state === 'run' ? (blocked ? (mine ? 'Terra is blocked and waiting
on your decision' : 'Terra is blocked — the Architect agent is
ruling') : ... ) : st[0]`. Exactly like C4's `OwnerDecisionCard`, this
slice picks the real, honest branch (the owner is who this program's
real M1 escalation chain actually reaches, per C1's own fixture) and
excludes the fictional M4-Architect-agent branch entirely.

**The `Last report` value is derived from the last message authored by
an implementor role (`k === "wk"`), not simply the thread's last entry
— a real, structural distinction, checked directly against C1's
fixture.** `PACKET_A2_ENTRIES`'s actual last entry is the Coordinator's
escalation (`14:56`), but the real reference value for `meta.report`
is `14:52` — Terra's own last status report, one entry earlier. The
derivation function finds the last `wk`-role entry, not
`entries.at(-1)`, matching this real distinction exactly.

**Every `#RRGGBB` value in the discrepancy table below is either an
existing real B2 token or the exact same real literal C1B's
`DesktopShell.tsx` already established for the identical "needs
attention" signal — redeclared here (that constant is module-private
and frozen), not independently reinvented:**

| Reference value | Real B2 token / precedent | Match? |
|---|---|---|
| header surface `#fff` | `colors.surface` | exact |
| header border `#EEEAF2` | `colors.borderDivider[0]` | exact |
| eyebrow text `#A79BB4` | `colors.inkFaint` | exact |
| title text (implicit default) | `colors.ink` | exact |
| state-line / blocker / next text (blocked) `#8A5A08` | `colors.warningText` | exact |
| "need" dot bg `#E0A32E` | `colors.warning` (same value C1B's `--atlas-dot-need` already uses) | exact, precedent-matched |
| "need" dot halo `rgba(224,163,46,.26)` | (no token; same literal C1B's `--atlas-dot-need-halo` already uses) | disclosed literal, precedent-matched |
| summary-row border `#F3F0F6` | `colors.borderDivider[1]` | exact |
| summary-row bg `#FCFBFD` | `colors.pageBgDesktop` | exact |
| pair-label text `#8E8299` | `colors.inkMuted` | exact |

Zero new, unprecedented disclosed literals — the one non-token value
(the dot halo) is the exact same literal already reviewed and merged
in C1B, reused, not reinvented.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C7-HEADER-STATE-WIRING-01` |
| `phase` | `PendingTargetedDecisionFidelityVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:a0e6e05e332d9f266acdff0faa1dfb190f63d10c","git:full-planning-review-head:9f22fcaf61189b0b4223c5296ab620921a911608","review:decision-fidelity:request-changes-minor:1-non-blocking-finding"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`: 64/64 tests passed (57 existing +
7 new), typecheck and lint clean, production build succeeded — all on
the first real run, no fix needed.

**The targeted planning correction below (restoring and disclosing the
`sc-if` conditional) changed only this document's Scope-section prose,
not any shipped code** — the `headerState.ts`/`PacketHeader.tsx`/
`PacketHeader.module.css`/`PacketHeader.test.tsx` code blocks shown
below are unchanged from the version already run above. No re-run of
the toolchain was needed or performed for this correction.

`apps/atlas/src/thread/headerState.ts` (new — the single-state-source
derivation function; no rendering logic):

```ts
import type { ThreadEntry } from "./fixtures";

/**
 * The README's own single-state-source rule (verbatim): "Picking an
 * option appends resolution messages to the thread and updates the
 * header summary, session label, hero card, boundary timestamps, and
 * 'what happens next' together — they must all read from one state
 * value, not be set independently." This is that one function for the
 * packet-thread header (the hero card and mobile "what happens next"
 * panel are separate, later Wave F work that should call this same
 * function once it's extended to those surfaces, not re-derive their
 * own copy of this logic).
 *
 * `eyebrow` and `title` are `PACKETS['A.2']`'s own real `id`/`title`
 * (`Atlas Explorations.dc.html`, verbatim), minus the mockup's own
 * "issue #970" segment — checked directly against this real
 * repository (`gh issue view 970` — no such issue exists here), so it
 * is not real, verifiable content for this project and is excluded,
 * not transcribed.
 *
 * The derivation below only implements the one real trajectory
 * `PACKET_A2_ENTRIES` (C1, frozen) actually contains: escalated,
 * waiting on the owner. The reference file's own "not blocked" values
 * depend entirely on simulated, interactive UI state (a `decided`/
 * `running` toggle) with no backing real fixture — inventing plausible
 * numbers for that branch would violate this program's own
 * fixture-content discipline (never invent product content). A future
 * slice with a second real scenario should extend this function then;
 * until it exists, the non-blocked branch reports `"unavailable"`,
 * per this project's own real M0-D14 reporting-honesty convention
 * (reported beats estimated; an unsupported field reads `unavailable`,
 * never a guess).
 */
export interface PacketHeaderState {
  eyebrow: string;
  title: string;
  isBlocked: boolean;
  stateLine: string;
  lastReport: string;
  blocker: string;
  nextLabel: string;
  next: string;
}

export function derivePacketHeaderState(entries: ThreadEntry[]): PacketHeaderState {
  const escalation = entries.find((entry) => entry.escalate === true);
  const isBlocked = escalation !== undefined;
  const lastImplementorReport = [...entries].reverse().find((entry) => entry.k === "wk");
  return {
    eyebrow: "m1-a · a.2",
    title: "Add output-specific Runtime Package creation",
    isBlocked,
    stateLine: isBlocked
      ? "Terra is blocked and waiting on your decision"
      : "unavailable",
    lastReport: lastImplementorReport?.time ?? "unavailable",
    blocker: isBlocked ? "theme version for theme-free outputs" : "none",
    nextLabel: isBlocked ? "Waiting on you" : "unavailable",
    next: isBlocked ? "41m" : "unavailable",
  };
}
```

`apps/atlas/src/thread/PacketHeader.module.css` (new — CSS Module,
`var(--atlas-*)` only, following the exact C1/C3/C4/C5/C6/B3/B4
pattern):

```css
.head {
  flex: none;
  padding: 16px 34px 0;
  background: var(--atlas-header-surface);
  border-bottom: 1px solid var(--atlas-header-border);
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  font: 500 11px var(--atlas-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--atlas-header-eyebrow);
}

.title {
  margin: 7px 0 0;
  font-family: var(--atlas-font-display);
  font-size: 25px;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.15;
  text-wrap: pretty;
  color: var(--atlas-header-title);
}

.stateLine {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 7px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--atlas-header-state-color);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--atlas-header-dot);
  box-shadow: 0 0 0 3px var(--atlas-header-dot-halo);
}

.summary {
  display: flex;
  flex-wrap: wrap;
  margin: 16px -34px 0;
  padding: 11px 34px;
  border-top: 1px solid var(--atlas-header-summary-border);
  background: var(--atlas-header-summary-bg);
  gap: 0 30px;
}

.pair {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13.5px;
}

.label {
  color: var(--atlas-header-label);
}

.reportValue {
  font-family: var(--atlas-font-mono);
  color: var(--atlas-header-title);
}

.blockerValue {
  font-weight: 600;
  color: var(--atlas-header-state-color);
}

.nextValue {
  font-family: var(--atlas-font-mono);
  color: var(--atlas-header-state-color);
}
```

`apps/atlas/src/thread/PacketHeader.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { derivePacketHeaderState } from "./headerState";
import { PACKET_A2_ENTRIES } from "./fixtures";
import styles from "./PacketHeader.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real packet-header markup.
 * The "need" dot (bg + halo) reuses the exact same real values C1B's
 * `DesktopShell.tsx` already established for the identical real signal
 * (`colors.warning` + `rgba(224,163,46,.26)`) — redeclared here rather
 * than imported, since `DesktopShell.tsx`'s constant is module-private
 * and frozen; both are the same real, checked value, not two different
 * guesses.
 */
const SHELL_VARS = {
  "--atlas-header-surface": colors.surface,
  "--atlas-header-border": colors.borderDivider[0],
  "--atlas-header-eyebrow": colors.inkFaint,
  "--atlas-header-title": colors.ink,
  "--atlas-header-state-color": colors.warningText,
  "--atlas-header-dot": colors.warning,
  "--atlas-header-dot-halo": "rgba(224,163,46,.26)",
  "--atlas-header-summary-border": colors.borderDivider[1],
  "--atlas-header-summary-bg": colors.pageBgDesktop,
  "--atlas-header-label": colors.inkMuted,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * The one, single source of state this header, and any future surface
 * that needs the same summary (a hero card, a "what happens next"
 * panel), should call — see `derivePacketHeaderState`'s own doc
 * comment for why only the real, exercised (blocked) branch renders
 * grounded values today.
 */
export function PacketHeader() {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
  return (
    <div className={styles.head} style={SHELL_VARS}>
      <div className={styles.eyebrow}>{state.eyebrow}</div>
      <h1 className={styles.title}>{state.title}</h1>
      <div className={styles.stateLine}>
        <span className={styles.dot} aria-hidden="true" />
        {state.stateLine}
      </div>
      <div className={styles.summary}>
        <div className={styles.pair}>
          <span className={styles.label}>Last report</span>
          <b className={styles.reportValue}>{state.lastReport}</b>
        </div>
        <div className={styles.pair}>
          <span className={styles.label}>Blocker</span>
          <b className={styles.blockerValue}>{state.blocker}</b>
        </div>
        <div className={styles.pair}>
          <span className={styles.label}>{state.nextLabel}</span>
          <b className={styles.nextValue}>{state.next}</b>
        </div>
      </div>
    </div>
  );
}

export default PacketHeader;
```

`apps/atlas/src/thread/PacketHeader.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PacketHeader } from "./PacketHeader";
import { derivePacketHeaderState } from "./headerState";
import { PACKET_A2_ENTRIES, type ThreadEntry } from "./fixtures";

afterEach(cleanup);

describe("derivePacketHeaderState", () => {
  it("derives the real blocked/escalated state from C1's frozen A.2 entries, every field from one function", () => {
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.isBlocked).toBe(true);
    expect(state.stateLine).toBe("Terra is blocked and waiting on your decision");
    expect(state.lastReport).toBe("14:52");
    expect(state.blocker).toBe("theme version for theme-free outputs");
    expect(state.nextLabel).toBe("Waiting on you");
    expect(state.next).toBe("41m");
  });

  it("reports unavailable, not a fabricated value, for a synthetic non-escalated thread (no real fixture backs this branch yet)", () => {
    const synthetic: ThreadEntry[] = [
      { k: "co", who: "Coordinator", text: "Go.", time: "10:00" },
      { k: "wk", who: "Terra", text: "On it.", time: "10:05" },
    ];
    const state = derivePacketHeaderState(synthetic);
    expect(state.isBlocked).toBe(false);
    expect(state.stateLine).toBe("unavailable");
    expect(state.lastReport).toBe("10:05");
    expect(state.blocker).toBe("none");
    expect(state.nextLabel).toBe("unavailable");
    expect(state.next).toBe("unavailable");
  });

  it("finds the last implementor (wk) report, not simply the last entry overall", () => {
    // Real property of PACKET_A2_ENTRIES: its very last entry is the
    // Coordinator's escalation (14:56), but the last report FROM
    // Terra is the earlier blocked message (14:52) — these differ,
    // and lastReport must track the implementor, not the last entry.
    expect(PACKET_A2_ENTRIES.at(-1)?.who).toBe("Coordinator");
    expect(PACKET_A2_ENTRIES.at(-1)?.time).toBe("14:56");
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.lastReport).toBe("14:52");
  });
});

describe("PacketHeader", () => {
  it("renders the real eyebrow and title, never the mockup's own unverifiable 'issue #970' segment", () => {
    render(<PacketHeader />);
    expect(screen.getByText("m1-a · a.2")).toBeInTheDocument();
    expect(screen.getByText("Add output-specific Runtime Package creation")).toBeInTheDocument();
    expect(screen.queryByText(/issue #970/)).toBeNull();
  });

  it("renders the state line and the three summary pairs, all consistent with one derived state object", () => {
    render(<PacketHeader />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText(state.stateLine)).toBeInTheDocument();
    expect(screen.getByText("Last report")).toBeInTheDocument();
    expect(screen.getByText(state.lastReport)).toBeInTheDocument();
    expect(screen.getByText("Blocker")).toBeInTheDocument();
    expect(screen.getByText(state.blocker)).toBeInTheDocument();
    expect(screen.getByText(state.nextLabel)).toBeInTheDocument();
    expect(screen.getByText(state.next)).toBeInTheDocument();
  });

  it("sets the header surface, border, and warning-state CSS variables to the real, checked tokens", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    expect(colors.borderDivider[1]).toBe("#F3F0F6");
    expect(colors.warning).toBe("#E0A32E");
    expect(colors.warningText).toBe("#8A5A08");
    const { container } = render(<PacketHeader />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-header-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-header-summary-border")).toBe(colors.borderDivider[1]);
    expect(root.style.getPropertyValue("--atlas-header-dot")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-header-state-color")).toBe(colors.warningText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PacketHeader />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `PacketThread`, `DesktopShell`, or
   `App.tsx` — standalone, exactly like every prior C-wave component.
2. This slice reads `PACKET_A2_ENTRIES` from C1's frozen
   `apps/atlas/src/thread/fixtures.ts` (read-only import) but does not
   modify that file, `PacketThread.tsx`, `PacketThread.module.css`, or
   `PacketThread.test.tsx`.
3. `derivePacketHeaderState` is the one, single source every displayed
   header field reads from — no field is independently hand-set in the
   component.
4. The not-blocked branch reports `"unavailable"` for every field that
   has no real, non-simulated default — never a fabricated number.
5. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`, or
   any C3/C4/C5/C6 (`decision/`, `crash/`) file is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/thread/headerState.ts` (new)
- `apps/atlas/src/thread/PacketHeader.module.css` (new)
- `apps/atlas/src/thread/PacketHeader.tsx` (new)
- `apps/atlas/src/thread/PacketHeader.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, everything under
`apps/atlas/src/shell/`, `apps/atlas/src/tokens/`, every C3-C6 file,
and C1's own `fixtures.ts`/`PacketThread.*` are untouched.

The 7 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 64 total after this slice (57 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 CrashCard tests, 7 thread tests, 5 mobile-shell
tests, 10 desktop-shell tests — + 7 new). `npm run build` must still
succeed; `PacketHeader` is not expected to appear in the `dist/`
bundle, matching every prior standalone slice's own build-unaffected
proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `derivePacketHeaderState` is the one real
   function every header-summary field is computed from — eyebrow,
   title, state line, and the three summary pairs are never
   independently hand-set — and `PacketHeader` renders its output using
   real B2 tokens or a literal already reviewed and merged in C1B.
2. **Operating and threat model:** a trusted local dev box; fully
   read-only, no interactive element of any kind.
3. **Explicit exclusions:** the hero card and "what happens next" panel
   (Wave F), the Stop/Start-work button and session label (real, but
   command-dependent — Wave D), any wiring into `PacketThread`/
   `DesktopShell`/`App.tsx`, a real "not blocked" branch (no backing
   fixture exists yet — deferred to whenever a second real scenario
   does).
4. **Assurance level:** practical component-rendering correctness with
   every real value checked against either the reference file directly
   or C1's own frozen fixture, and every unexercised value honestly
   reported `"unavailable"` rather than guessed — proportionate to a
   read-only view with no data dependency and no consumer yet.
5. **Acceptance proof:** the 7 named tests, the existing 57 `apps/atlas`
   tests continuing to pass (64 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color either a real token property or
   the one literal precedent already reviewed in C1B; the only cross-
   module import is a read-only import of C1's frozen
   `PACKET_A2_ENTRIES`/`ThreadEntry`.
7. **Proportionality ceiling:** one derivation function, one header
   component, one CSS Module; no hero card, no "what happens next"
   panel, no wiring, no second scenario.
8. **Stop and escalation rule:** wiring `PacketHeader` into
   `PacketThread`/`DesktopShell`, extending `derivePacketHeaderState`
   for a hero card or "what happens next" panel, or modeling a real
   "not blocked" branch, are each new, separately reviewed work — not
   decided implicitly here. If a future backend/fixture change alters
   C1's `PACKET_A2_ENTRIES`, this slice's derived values must be
   revisited — a discovered drift here is a defect against this slice,
   not a silent acceptability. A discovered proof/contract defect
   against a frozen slice terminally returns that slice. One planning
   correction and one implementation correction are the maximum
   available.
