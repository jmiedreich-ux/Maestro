# M2 Wave C — Crash Card Rendering — Candidate 01

**Slice ID:** `MB-SLICE-M2-C6-CRASH-CARD-01`
**Status:** `Corrected — Pending Targeted Decision Fidelity Verification`.
Full Decision Fidelity review found 1 blocking finding (the headline
and lede silently adapted two of the same class of unverifiable/
contradicted claims the packet already disclosed correcting elsewhere,
without being numbered as corrections themselves); one targeted
planning correction resolved it — Corrections 1 and 2 added, the
remaining three renumbered, disclosure wording tightened throughout.
No further planning correction is available for this slice.
**Base:** `0945d3c` (`origin/master`)

## Scope, deliberately minimal

Wave C6 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the crash
card's read-only visual anatomy — eyebrow (dot + badge + age),
headline, lede, a 2×2 fact grid, a 3-item option list (rendered but
genuinely inert — no command wiring; that is Wave D, item D6/D7), and
a footer note. No wiring into `PacketThread`, `DesktopShell`, or
`App.tsx`. `CrashCard` is a new, standalone component, exactly like
C3's `DecisionCard`, C4's `OwnerDecisionCard`, and C5's
`FidelityRecord`.

**This slice reuses C1's real `A.2` scenario, and that is not this
program's own choice — it is the reference file's own scoping.** The
reference file's `crashed` system-state toggle is conditioned on
`sys === 'crashed' && cur.id === 'A.2'` (verbatim from the source,
quoted below): the mockup's crash simulation only ever applies to the
`A.2` packet. So, like C4, this slice renders the same real packet
C1's frozen fixture already established, not a new invented scenario.

**No fictional "Architect agent" persona appears anywhere in the
reference file's crash-card markup or data — the cleanest of any
C-wave card so far.** Every name, role, and mechanic referenced
(`Terra`, `Sol`, `Coordinator`, worktree, correction budget, base
commit) is real M1/M2 vocabulary already established by C1's fixture.
No persona-swap is needed here, unlike C3/C4.

**This slice's real content work is different in kind: verifying the
reference file's own factual claims against the real backend state
machine, not swapping a persona.** Checking the reference file's crash
copy against `services/maestro/maestro/operational_state.py`'s real
`finish_attempt_execution` method found repeated instances of the same
two failure patterns: a claim about the physical worktree that nothing
in the real code tracks either way (**unverifiable**), and a claim that
locks/context are held or preserved after a failure, which the real
mechanism's `outcome_mapping` directly contradicts (**contradicted**) —
plus one further claim (an automatic retry) with no corresponding code
path at all. Per this program's standing rule (never invent or carry
forward an unverified factual claim once a real source is available to
check it against), all five instances below are corrected, disclosed
explicitly — not silently carried over from the mockup and not
silently dropped.

`finish_attempt_execution`'s real outcome mapping
(`operational_state.py`, verbatim, lines 1403–1409):

```python
outcome_mapping = {
    "Succeeded": ("AwaitingIntegration", "Released", "Released"),
    "Failed": ("NeedsReplan", "Released", "Released"),
    "Cancelled": ("Cancelled", "Cancelled", "Released"),
    "TimedOut": ("NeedsReplan", "Expired", "Expired"),
    "Stale": ("NeedsReplan", "Released", "Released"),
}
```

A `Failed` execution outcome — the real mechanism closest to "Terra
died mid-step" — always routes the packet to `NeedsReplan` and always
**releases** the attempt's lease. There is no real outcome that leaves
a lease held after failure, and (checked directly against
`_PACKET_ELIGIBILITY_TRANSITIONS` and `record_and_close_needs_replan`,
the only real function that transitions a `NeedsReplan` packet) the
only implemented next step for a `NeedsReplan` packet today is
cancellation — real recovery (resume/re-dispatch) is not yet built,
which is exactly why the roadmap's own D6/D7 items exist as future
work, not something this slice can wire to already-real commands.

**Corrections 1 and 2 — the headline and lede (added — blocking finding
from Decision Fidelity review: an earlier draft of this slice silently
adapted this text without numbering it as a correction, the exact
failure mode the other three corrections exist to avoid).** Reference
file's real headline and lede (verbatim, from the markup quoted in
full below): *"Terra died mid-step. Its work is still on disk."* and
*"The process exited during step 3 of 5 without a handoff. The
worktree and its locks were preserved at the last safe boundary —
nothing has been discarded and no correction was spent."* Both contain
the same class of claim already identified as a problem elsewhere in
this exact card: "still on disk" is an unverifiable physical-worktree
claim (the same reasoning Correction 3 below gives for excluding
`Worktree: preserved`), and "its locks... were preserved" is not
merely unverifiable but **directly contradicts** the real mechanism
(the same reasoning Correction 4 below gives for excluding "Locks stay
held" — a `Failed` outcome always releases the lease). Both are
corrected, not silently carried forward: the headline becomes *"Terra's
attempt failed mid-step. A.2 is routed to NeedsReplan"* and the lede
becomes *"The process exited during step 3 of 5 without a handoff. A
Failed execution outcome routes the packet to NeedsReplan and releases
its lease, per Maestro's real execution-outcome mapping"* — both
stating only what `finish_attempt_execution`'s real mapping actually
does, with no claim about the physical worktree either way.

**Correction 3 — the fact grid.** Reference file's real `crash.facts`
(verbatim):

```js
facts: [
  { k: 'Last boundary', v: '14:52' }, { k: 'Step reached', v: '3 of 5' },
  { k: 'Worktree', v: 'preserved' }, { k: 'Corrections spent', v: '0 of 1' },
],
```

`Last boundary` (`14:52`) and `Step reached` (`3 of 5`) are both real,
transcribed verbatim, and independently checkable against C1's frozen
`PACKET_A2_ENTRIES`: `14:52` is the real timestamp of Terra's own
blocked message, and `3 of 5` matches Terra's own real `plan.steps`
array exactly (step index 2, `status: "now"`, out of 5 total steps).
`Corrections spent` (`0 of 1`) is also kept verbatim — a real,
checkable value (`A.2` has not consumed its one correction per C1's
fixture). `Worktree: preserved` is **not** carried forward: nothing in
`operational_state.py` tracks or asserts anything about the physical
worktree's contents after a `Failed` outcome — only the logical lease
state (`Released`), which is a real, different, and verifiable fact.
This slice's fact grid replaces the unverifiable claim with the real
one: `Outcome: Failed`, citing `finish_attempt_execution`'s own real
mapping.

**Correction 4 — the third recovery option's body text.** Reference
file's real `crash.options[2]` (verbatim):

```js
{ title: 'Hold A.2 and inspect the worktree', cost: 'A.3 stays blocked', body: 'Nothing is dispatched. Locks stay held so you can read what Terra wrote before deciding.' },
```

"Locks stay held" is not merely unverifiable here — it directly
**contradicts** the real mechanism quoted above: a `Failed` (or
`TimedOut`/`Stale`) outcome always sets the lease to `Released` or
`Expired`, never held. This slice keeps the option's title and cost
verbatim (both real, and neither makes a factual claim about lock
state) and corrects only the contradicted clause in the body text:
*"Nothing is dispatched. A.3 stays blocked until this is resolved —
read what Terra wrote before deciding."* — preserving the option's real
intent (don't dispatch anything yet, inspect first) without asserting
something the real state machine rules out.

**Correction 5 — the footer note.** Reference file's real footer
(verbatim): *"The Coordinator retried once and the process died the
same way, so it stopped retrying and surfaced this instead."* No
automatic-retry mechanism for a `Failed` execution exists anywhere in
`operational_state.py` — checked directly, there is no code path that
re-attempts a failed execution before recording it as `Failed`. This
claim is not carried forward. This slice's footer instead states the
real, checkable situation plainly: this is `A.2`'s only recorded
attempt, and `NeedsReplan` has no real automatic-resume mechanism yet
— the three options above describe what a future Wave D command would
do, and (matching C3's/C4's own established pattern) none of them are
wired to anything real yet.

**The other two recovery options, and the corrected third option's
title/cost, are kept exactly as the reference file, with no persona
issue and no factual overclaim to correct.** All reference real
vocabulary (`Terra`, `Sol`, worktree, base commit `9d3e1a2`,
correction budget) already established by C1's fixture, and describe
plausible future Wave D behavior without asserting anything about the
*current* state machine that isn't true today.

Source quote (README, "Packet detail" section, crash-card paragraph,
verbatim):

> **Crash card** (when the agent died): border `#EFC9C4`, bg `#FEF7F6`,
> ink `#A63F36`, dot `#C4564A`, badge `agent stopped unexpectedly`.
> Headline "Terra died mid-step. Its work is still on disk." Then a
> 2-up fact grid (`Last boundary 14:52`, `Step reached 3 of 5`,
> `Worktree preserved`, `Corrections spent 0 of 1`), three recovery
> options (resume from boundary / re-dispatch to Sol / hold and
> inspect), and a footer noting the Coordinator already retried once.
> The crash card **replaces** the decision card, never stacks with it.

("The crash card replaces the decision card, never stacks with it" is
a real UI-composition rule this slice does not need to implement —
there is no shared parent component yet for the two cards to compete
inside; recorded here as a note for whichever future slice wires both
into the same thread.)

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from):

```html
<div style="display:grid;grid-template-columns:36px minmax(0,1fr);gap:14px;padding:4px 34px 8px;animation:rise .22s ease-out">
  <span></span>
  <div style="min-width:0;max-width:60ch;border:1px solid #EFC9C4;border-radius:14px;background:#FEF7F6;overflow:hidden">
    <div style="padding:15px 17px 13px">
      <div style="display:flex;align-items:center;gap:9px;font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#A63F36"><span style="width:7px;height:7px;border-radius:50%;background:#C4564A"></span>agent stopped unexpectedly<span style="margin-left:auto;letter-spacing:.06em;color:#B79C99">14:58</span></div>
      <div style="margin-top:9px;font-family:'Bricolage Grotesque',sans-serif;font-size:17.5px;font-weight:600;letter-spacing:-.015em;line-height:1.3;text-wrap:pretty">Terra died mid-step. Its work is still on disk.</div>
      <div style="margin-top:6px;font-size:13.5px;line-height:1.55;color:#6C6376;text-wrap:pretty">The process exited during step 3 of 5 without a handoff. The worktree and its locks were preserved at the last safe boundary — nothing has been discarded and no correction was spent.</div>
      <div style="display:grid;grid-template-columns:{{ crash.cols }};gap:0 22px;margin-top:13px;padding-top:12px;border-top:1px solid #F6E2DF">
        <sc-for list="{{ crash.facts }}" as="ft" hint-placeholder-count="4">
        <div style="display:flex;align-items:baseline;gap:8px;padding:3px 0;font-size:13px"><span style="color:#8E8299">{{ ft.k }}</span><b style="font-family:'IBM Plex Mono',monospace;font-weight:600">{{ ft.v }}</b></div>
        </sc-for>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:1px;padding:0 9px 9px">
      <sc-for list="{{ crash.options }}" as="o" hint-placeholder-count="3">
      <button onClick="{{ o.onPick }}" style="display:block;width:100%;padding:11px 12px;border:1px solid transparent;border-radius:10px;background:#fff;text-align:left;cursor:pointer" style-hover="border-color:#EBBDB7;background:#FFFCFB">
        <div style="display:flex;align-items:baseline;gap:10px"><b style="font-size:14.5px;color:#221C29">{{ o.title }}</b><span style="margin-left:auto;flex:none;font:500 11px 'IBM Plex Mono',monospace;color:#A63F36">{{ o.cost }}</span></div>
        <div style="margin-top:3px;font-size:13px;line-height:1.5;color:#6C6376;text-wrap:pretty">{{ o.body }}</div>
      </button>
      </sc-for>
    </div>
    <div style="padding:10px 17px;border-top:1px solid #F6E2DF;font-size:12.5px;line-height:1.5;color:#8E8299;text-wrap:pretty">The Coordinator retried once and the process died the same way, so it stopped retrying and surfaced this instead.</div>
  </div>
</div>
```

**"Options rendered but inert," matching C3's/C4's own established
implementation, not the reference file's live `cursor:pointer` /
`onClick` behavior.** Real `<button>` elements, no `onClick` handler at
all, `cursor: default` — the same real, disclosed deviation C4 already
established for the same reason: there is no real command yet (Wave
D's D6/D7), and a pointer cursor over a control that does nothing would
misrepresent it as functional.

**Color discrepancy table — every value checked against this
codebase's real B2 tokens; the cleanest token match of any C-wave card
so far, only 2 real gaps:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| border `#EFC9C4` | `colors.dangerBorder` | exact |
| bg `#FEF7F6` | `colors.dangerWash` | exact |
| ink `#A63F36` | `colors.dangerText` | exact |
| dot `#C4564A` | `colors.danger` | exact |
| age text `#B79C99` | none in `colors.ts` | disclosed literal |
| headline / fact-value / option-title text `#221C29` | `colors.ink` | exact |
| lede / option-body text `#6C6376` | `colors.inkSecondary` | exact |
| fact-grid divider / footer divider `#F6E2DF` | `colors.dangerDivider` | exact |
| fact-label text `#8E8299` | `colors.inkMuted` | exact |
| option background `#fff` | `colors.surface` | exact |
| option hover border `#EBBDB7` | `colors.focusHoverBorderRed` | exact |
| option hover background `#FFFCFB` | none in `colors.ts` | disclosed literal |
| footer text `#8E8299` | `colors.inkMuted` | exact |

2 real, checked gaps (the eyebrow age color, distinct from the
decision cards' own shared `#A1927B` age color, and the option hover
background).

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C6-CRASH-CARD-01` |
| `phase` | `PendingTargetedDecisionFidelityVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:0945d3c5798175ee89f320cd764ea2a5e2ab28d5","git:full-planning-review-head:296ed9afcd337e9740276bc7353b3fdae4a7e774","review:decision-fidelity:request-changes:1-blocking-finding"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`: 57/57 tests passed (50 existing +
7 new), typecheck and lint clean, production build succeeded — all on
the first real run, no fix needed.

**The targeted planning correction below (adding Corrections 1 and 2)
changed only this document's prose and doc comments, not the shipped
`fixtures.ts`/`CrashCard.tsx` code's runtime content** — the
`CRASH_EXAMPLE` object's `headline`/`lede` fields shown below were
already the corrected text at the time of the original real toolchain
run quoted above; the DF-review finding was that this document had not
disclosed that correction as one of the numbered ones, not that the
code was wrong. No re-run of the toolchain was needed or performed for
this correction.

`apps/atlas/src/crash/fixtures.ts` (new — the evidence data and its
types; no rendering logic):

```ts
/**
 * Same real `A.2` scenario C1/C4 already established (the reference
 * file's own `crashed` system-state toggle is scoped to
 * `cur.id === 'A.2'`) — not a new, invented scenario. Five pieces of
 * the reference file's own copy (the headline, the lede, one fact, one
 * option's body, and the footer) make a claim this program cannot
 * verify or that directly contradicts the real backend state machine,
 * and are corrected here to state only what
 * `services/maestro/maestro/operational_state.py`'s real
 * `finish_attempt_execution` outcome mapping actually does — see this
 * slice's packet contract, Scope section, for the full comparison,
 * numbered as Corrections 1 through 5.
 */
export interface CrashFact {
  k: string;
  v: string;
}

export interface CrashOption {
  title: string;
  cost: string;
  body: string;
}

export interface CrashExample {
  packetId: string;
  age: string;
  headline: string;
  lede: string;
  facts: CrashFact[];
  options: CrashOption[];
  footerNote: string;
}

export const CRASH_EXAMPLE: CrashExample = {
  packetId: "A.2",
  age: "14:58",
  headline: "Terra's attempt failed mid-step. A.2 is routed to NeedsReplan.",
  lede: "The process exited during step 3 of 5 without a handoff. A Failed execution outcome routes the packet to NeedsReplan and releases its lease, per Maestro's real execution-outcome mapping.",
  facts: [
    { k: "Last boundary", v: "14:52" },
    { k: "Step reached", v: "3 of 5" },
    { k: "Outcome", v: "Failed" },
    { k: "Corrections spent", v: "0 of 1" },
  ],
  options: [
    {
      title: "Resume Terra from the last boundary",
      cost: "no correction",
      body: "A fresh Terra process rereads the worktree and the thread, then continues at step 3. Context is rebuilt, not remembered.",
    },
    {
      title: "Re-dispatch A.2 to another implementor",
      cost: "discards ~1h of work",
      body: "Sol takes the packet from base 9d3e1a2. The existing worktree is archived, not merged.",
    },
    {
      title: "Hold A.2 and inspect the worktree",
      cost: "A.3 stays blocked",
      body: "Nothing is dispatched. A.3 stays blocked until this is resolved — read what Terra wrote before deciding.",
    },
  ],
  footerNote: "This is A.2's only recorded attempt. NeedsReplan has no automatic resume in Maestro today — the three choices above describe what a future guarded command would do; none of them dispatch anything yet.",
};
```

`apps/atlas/src/crash/CrashCard.module.css` (new — CSS Module,
`var(--atlas-*)` only, following the exact C1/C3/C4/C5/B3/B4 pattern):

```css
.row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 14px;
  padding: 4px 34px 8px;
}

.card {
  min-width: 0;
  max-width: 60ch;
  border: 1px solid var(--atlas-crash-border);
  border-radius: 14px;
  background: var(--atlas-crash-bg);
  overflow: hidden;
}

.head {
  padding: 15px 17px 13px;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-crash-ink);
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--atlas-crash-dot);
}

.age {
  margin-left: auto;
  letter-spacing: 0.06em;
  color: var(--atlas-crash-age);
}

.headline {
  margin-top: 9px;
  font-family: var(--atlas-font-display);
  font-size: 17.5px;
  font-weight: 600;
  letter-spacing: -0.015em;
  line-height: 1.3;
  text-wrap: pretty;
  color: var(--atlas-crash-headline);
}

.lede {
  margin: 6px 0 0;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-crash-lede);
  text-wrap: pretty;
}

.facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 22px;
  margin-top: 13px;
  padding-top: 12px;
  border-top: 1px solid var(--atlas-crash-divider);
}

.fact {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 3px 0;
  font-size: 13px;
}

.factLabel {
  color: var(--atlas-crash-fact-label);
}

.factValue {
  font-family: var(--atlas-font-mono);
  font-weight: 600;
  color: var(--atlas-crash-fact-value);
}

.optionList {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 0 9px 9px;
}

.option {
  display: block;
  width: 100%;
  padding: 11px 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: var(--atlas-crash-surface);
  text-align: left;
  cursor: default;
  font: inherit;
}

.option:hover {
  border-color: var(--atlas-crash-hover-border);
  background: var(--atlas-crash-hover-bg);
}

.optionRow {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.optionTitle {
  font-size: 14.5px;
  color: var(--atlas-crash-headline);
}

.optionCost {
  margin-left: auto;
  flex: none;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-crash-ink);
}

.optionBody {
  margin-top: 3px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--atlas-crash-lede);
  text-wrap: pretty;
}

.footer {
  padding: 10px 17px;
  border-top: 1px solid var(--atlas-crash-divider);
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--atlas-crash-fact-label);
  text-wrap: pretty;
}
```

`apps/atlas/src/crash/CrashCard.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { CRASH_EXAMPLE } from "./fixtures";
import styles from "./CrashCard.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real, non-templated crash
 * markup (this card has only one visual treatment, no variant object).
 * Every semantic color here is a real B2 `colors.danger*` token — the
 * cleanest token match of any C-wave card so far. Two values have no
 * equivalent token and stay disclosed literals, checked directly
 * against the reference file: the eyebrow age color (`#B79C99`,
 * distinct from the decision cards' shared `#A1927B` age color) and
 * the option hover background (`#FFFCFB`).
 */
const SHELL_VARS = {
  "--atlas-crash-border": colors.dangerBorder,
  "--atlas-crash-bg": colors.dangerWash,
  "--atlas-crash-ink": colors.dangerText,
  "--atlas-crash-dot": colors.danger,
  "--atlas-crash-age": "#B79C99",
  "--atlas-crash-headline": colors.ink,
  "--atlas-crash-lede": colors.inkSecondary,
  "--atlas-crash-divider": colors.dangerDivider,
  "--atlas-crash-fact-label": colors.inkMuted,
  "--atlas-crash-fact-value": colors.ink,
  "--atlas-crash-surface": colors.surface,
  "--atlas-crash-hover-border": colors.focusHoverBorderRed,
  "--atlas-crash-hover-bg": "#FFFCFB",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * The reference file's `crashed` state is scoped to the same real
 * `A.2` packet C1/C4 already established — not a new scenario. See
 * this slice's packet contract (Corrections 1-5) for the headline,
 * lede, one fact, one option's body, and the footer note, all adapted
 * rather than transcribed verbatim: the reference file's own "still on
 * disk", "locks... preserved", "Worktree: preserved", "Locks stay
 * held", and "Coordinator retried once" claims are either not
 * verifiable against, or directly contradict, `finish_attempt_execution`'s
 * real outcome mapping in `operational_state.py`, which always
 * releases a Failed attempt's lease.
 */
export function CrashCard() {
  const { age, headline, lede, facts, options, footerNote } = CRASH_EXAMPLE;
  return (
    <div className={styles.row} style={SHELL_VARS}>
      <span aria-hidden="true" />
      <div className={styles.card}>
        <div className={styles.head}>
          <div className={styles.eyebrow}>
            <span className={styles.dot} aria-hidden="true" />
            agent stopped unexpectedly
            <span className={styles.age}>{age}</span>
          </div>
          <div className={styles.headline}>{headline}</div>
          <p className={styles.lede}>{lede}</p>
          <div className={styles.facts}>
            {facts.map((fact) => (
              <div key={fact.k} className={styles.fact}>
                <span className={styles.factLabel}>{fact.k}</span>
                <b className={styles.factValue}>{fact.v}</b>
              </div>
            ))}
          </div>
        </div>
        <div className={styles.optionList}>
          {options.map((option) => (
            <button key={option.title} type="button" className={styles.option}>
              <div className={styles.optionRow}>
                <b className={styles.optionTitle}>{option.title}</b>
                <span className={styles.optionCost}>{option.cost}</span>
              </div>
              <div className={styles.optionBody}>{option.body}</div>
            </button>
          ))}
        </div>
        <div className={styles.footer}>{footerNote}</div>
      </div>
    </div>
  );
}

export default CrashCard;
```

`apps/atlas/src/crash/CrashCard.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { CrashCard } from "./CrashCard";
import { CRASH_EXAMPLE } from "./fixtures";

afterEach(cleanup);

describe("CrashCard", () => {
  it("renders the eyebrow badge and age, and the adapted headline naming the real Failed/NeedsReplan mechanism", () => {
    render(<CrashCard />);
    expect(screen.getByText("agent stopped unexpectedly")).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.age)).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.headline)).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.lede)).toBeInTheDocument();
    expect(screen.queryByText(/still on disk/)).toBeNull();
  });

  it("renders all 4 real facts, including the corrected 'Outcome: Failed' fact in place of the reference file's unverifiable 'worktree preserved' claim", () => {
    render(<CrashCard />);
    for (const fact of CRASH_EXAMPLE.facts) {
      expect(screen.getByText(fact.k)).toBeInTheDocument();
      expect(screen.getByText(fact.v)).toBeInTheDocument();
    }
    expect(screen.queryByText(/preserved/)).toBeNull();
  });

  it("renders exactly the 3 real options, with the third's corrected body text that no longer claims locks stay held", () => {
    render(<CrashCard />);
    expect(screen.getAllByRole("button")).toHaveLength(3);
    for (const option of CRASH_EXAMPLE.options) {
      expect(screen.getByText(option.title)).toBeInTheDocument();
      expect(screen.getByText(option.cost)).toBeInTheDocument();
      expect(screen.getByText(option.body)).toBeInTheDocument();
    }
    expect(screen.queryByText(/[Ll]ocks stay held/)).toBeNull();
  });

  it("renders the corrected footer note, not the reference file's unverifiable 'Coordinator retried once' claim", () => {
    render(<CrashCard />);
    expect(screen.getByText(CRASH_EXAMPLE.footerNote)).toBeInTheDocument();
    expect(screen.queryByText(/retried once/)).toBeNull();
  });

  it("sets the card border, background, and ink CSS variables to the real colors.danger* tokens", () => {
    expect(colors.dangerBorder).toBe("#EFC9C4");
    expect(colors.dangerWash).toBe("#FEF7F6");
    expect(colors.dangerText).toBe("#A63F36");
    expect(colors.danger).toBe("#C4564A");
    const { container } = render(<CrashCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-crash-border")).toBe(colors.dangerBorder);
    expect(root.style.getPropertyValue("--atlas-crash-bg")).toBe(colors.dangerWash);
    expect(root.style.getPropertyValue("--atlas-crash-ink")).toBe(colors.dangerText);
    expect(root.style.getPropertyValue("--atlas-crash-dot")).toBe(colors.danger);
  });

  it("renders exactly 3 real <button> elements with no onClick side effect (clicking does nothing observable)", () => {
    render(<CrashCard />);
    const buttons = screen.getAllByRole("button");
    for (const button of buttons) {
      button.click();
    }
    // Still exactly 3 buttons, same text — nothing changed state.
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<CrashCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `PacketThread`, `DesktopShell`, or
   `App.tsx` — standalone, exactly like C3's `DecisionCard`, C4's
   `OwnerDecisionCard`, and C5's `FidelityRecord`.
2. This slice does not import from `apps/atlas/src/thread/fixtures.ts`
   or any C3/C4/C5 file — `apps/atlas/src/crash/fixtures.ts` is an
   independent, hand-maintained object that deliberately mirrors the
   same real `A.2` scenario (see Scope), matching C4's own established
   non-import pattern.
3. Every color value is either a real B2 token or a disclosed literal
   checked directly against `Atlas Explorations.dc.html`; none is
   invented or borrowed from a near-but-wrong existing token.
4. Every piece of card copy (headline, lede, each fact, each option's
   body, the footer note) is either transcribed verbatim from the
   reference file or explicitly corrected (Corrections 1-5) against a
   real, cited `operational_state.py` mechanism — never silently
   carried forward unverified and never silently dropped.
5. The option list renders exactly 3 real options as inert `<button>`
   elements with no `onClick` — genuinely inert, not merely styled to
   look disabled, matching C4's established pattern.
6. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, or any C3/C4/C5 file is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/crash/fixtures.ts` (new)
- `apps/atlas/src/crash/CrashCard.module.css` (new)
- `apps/atlas/src/crash/CrashCard.tsx` (new)
- `apps/atlas/src/crash/CrashCard.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/tokens/`, and every C3/C4/C5 file are untouched.

The 7 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 57 total after this slice (50 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 thread tests, 5 mobile-shell tests, 10
desktop-shell tests — + 7 new). `npm run build` must still succeed;
`CrashCard` is not expected to appear in the `dist/` bundle, matching
every prior standalone slice's own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `CrashCard` renders the crash card's exact
   visual anatomy (eyebrow, headline, lede, fact grid, 3-option list,
   footer) using real B2 tokens or disclosed reference-file-checked
   literals, populated with C1's real `A.2` scenario, with every
   factual claim either transcribed verbatim or corrected against
   `operational_state.py`'s real `finish_attempt_execution` mechanism.
2. **Operating and threat model:** a trusted local dev box; the option
   rows are real `<button>` elements (for correct semantics/focus) but
   carry no `onClick` — clicking one does nothing, by construction.
3. **Explicit exclusions:** header/state-source wiring (C7), any wiring
   into `PacketThread`/`DesktopShell`/`App.tsx`/`../thread/fixtures.ts`,
   any real command behind an option (Wave D, items D6/D7), the
   "crash card replaces the decision card, never stacks" composition
   rule (no shared parent yet for the two cards to compete inside).
4. **Assurance level:** practical component-rendering correctness with
   every factual claim checked against either C1's own frozen fixture
   or `operational_state.py`'s real, already-reviewed mechanism —
   proportionate to a read-only view with no data dependency and no
   consumer yet, with the added discipline of correcting (not just
   disclosing) two real, checked inaccuracies in the reference file's
   own copy.
5. **Acceptance proof:** the 7 named tests, the existing 50 `apps/atlas`
   tests continuing to pass (57 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color either a real token property or a
   literal checked directly against the reference file; no import of
   any C1/C3/C4/C5 module.
7. **Proportionality ceiling:** one view component, one fixtures
   module, one CSS Module; no wiring, no second scenario, no real
   command behind any option.
8. **Stop and escalation rule:** wiring `CrashCard` into a real packet
   thread, or wiring its options to real Wave D commands, is new,
   separately reviewed work — not decided implicitly here. If
   `finish_attempt_execution`'s real outcome mapping ever changes (e.g.
   a future slice adds a real resume-without-replan path), this
   slice's corrected facts and option body must be revisited — a
   discovered drift here is a defect against this slice, not a silent
   acceptability. A discovered proof/contract defect against a frozen
   slice terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
