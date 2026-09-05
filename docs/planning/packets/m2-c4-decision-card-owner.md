# M2 Wave C — Decision Card, Owner-Decision Variant — Candidate 01

**Slice ID:** `MB-SLICE-M2-C4-DECISION-CARD-OWNER-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `431a1fd` (`origin/master`)

## Scope, deliberately minimal

Wave C4 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the decision
card's **owner-decision variant** — read-only rendering plus its
option list, rendered but inert (no command wiring; that is Wave D,
items D2/D3). No ruling variant (that is C3, already merged), no
Decision Fidelity record (C5), no crash card (C6), no wiring into
`PacketThread`, `DesktopShell`, or `App.tsx`. `OwnerDecisionCard` is a
new, standalone component, exactly like C3's `DecisionCard`.

**Unlike C3, this slice reuses C1's real `A.2` scenario directly, and
that is deliberate.** C1's frozen `PACKET_A2_ENTRIES` fixture
(`apps/atlas/src/thread/fixtures.ts`) ends with a real, already-merged
entry (`k: "co"`, `14:56`, `escalate: true`): *"I can rule on scope,
corrections and dispatch — I cannot widen a frozen contract, so this
one goes to the owner. Terra holds its worktree meanwhile."* Per the M2
roadmap's own "Architecture ruling on the one real gap" section: *"an
entry that has no automated route and is durably waiting on a human
renders the 'owner decision' variant."* That is exactly this entry —
the real M1/M2 case this variant exists for. So, unlike C3 (which had
to invent a separate, real routing-table example because `A.2`'s
blocker is NOT a ruling case), C4 renders the SAME `A.2` scenario C1
already established, viewed from the owner's side.

**This slice's fixture (`apps/atlas/src/decision/ownerFixtures.ts`) is
a deliberately independent, hand-maintained object — not an import
from `../thread/fixtures`.** Importing `PACKET_A2_ENTRIES` would create
a real, new coupling between `decision/` and `thread/`, two component
families this program has kept standalone until their own explicit
wiring slice (`PacketThread`/`DesktopShell` via C1B; `DecisionCard` and
`OwnerDecisionCard` have no such slice yet). Keeping them independent
here is consistent with that pattern; the tradeoff, disclosed here and
in the fixture's own doc comment, is that if C1's fixture text ever
changes, this object must be updated by hand to stay consistent — the
same category of disclosed, hand-maintained coupling as C3's
`_REVIEW_ROUTES` citation.

**The reference file's fictional "Architect agent" persona is removed
from the copy, exactly as C3 already established — but here, because
the underlying scenario is real, most of the reference file's own copy
needs no change at all.** `Atlas Explorations.dc.html`'s owner-variant
`blk` object (verbatim):

```js
{ border: '#F1DEBE', bg: '#FEF9F0', ink: '#8A5A08', dotBg: '#E0A32E', dotRing: 'rgba(224,163,46,.24)',
  chip: '#FDF1DC', chipOn: '#E0A32E', chipOnInk: '#3D2C06',
  badge: 'your decision', age: 'waiting 41m', target: 'you',
  why: 'the Architect agent stopped: this changes a contract you froze',
  lede: 'The Architect agent will not rule on a contract the owner froze, so it escalated instead of guessing. Terra is holding its worktree until you answer.',
  foot: 'One of the few that needs a human — the Architect agent rules on the rest.',
  actLabel: 'Let the Architect rule', onAct: () => this.setState({ mine: false }) }
```

`badge` ("your decision"), `age` ("waiting 41m"), and `target` ("you")
reference no fictional persona and are transcribed verbatim, unchanged.
Only `why` and `lede` name "the Architect agent" and are adapted —
replaced with "the Coordinator," the real M1/M2 actor that actually
performs this escalation, per `PACKET_A2_ENTRIES`'s own real final
entry quoted above (which is literally the Coordinator speaking, not an
Architect agent). `foot` and `actLabel` are not rendered at all — see
below.

**This slice reuses the exact same headline question as C3's packet,
and that is not a coincidence — it is the reference file's own
literal.** The headline text (`Should a theme-free output get a
sentinel version, or does the frozen contract change?`) sits outside
the `blk.*` template holes in the markup (hardcoded, shared by both
variants, since the mockup's own simulation shows one scenario from two
different `mine` states). It names no persona and is transcribed
verbatim here, unmodified.

**No footer, no footer button — a real, disclosed exclusion, not a
visual simplification.** The reference file's `foot`/`actLabel`
("Let the Architect rule") let the owner hand this decision back to
the simulated Architect agent. M2 has no such agent to hand it to, and
no Wave-D command exists yet for anything this card could do. Rendering
a footer button that performs no real action, or one whose only honest
label references a capability that doesn't exist, would repeat the
exact failure the roadmap's architecture ruling exists to prevent. This
slice therefore ends the card's anatomy after the option list — no
footer bar.

**The option list is rendered, but with only 2 of the reference file's
3 options — the third is excluded, disclosed, not silently dropped.**
Reference file's full `BLOCK_OPTIONS` (verbatim):

```js
const BLOCK_OPTIONS = [
  { key: 'sentinel', title: 'Allow a sentinel version', cost: 'resumes now', body: 'Terra writes theme-less:1 for theme-free outputs. The A.1 contract stays frozen and no correction is spent.' },
  { key: 'amend', title: 'Amend the A.1 contract', cost: '~25 min · 1 correction', body: 'A.1 reopens for one correction so an empty theme version becomes legal. A.2 pauses and keeps its worktree.' },
  { key: 'defer', title: 'Send back to the Architect agent', cost: 'unknown · Terra idle', body: 'The Architect agent rules on the contract question and records a fidelity check. Terra stays stopped with its locks held.' },
];
```

`sentinel` and `amend` are real, substantive choices facing the owner
in this scenario, name no fictional persona, and are transcribed
verbatim. `defer` ("Send back to the Architect agent") depends entirely
on the M4 Architect agent — in real M2, there is nothing to defer to,
so offering this option would render a capability that does not exist.
It is excluded, not adapted, because there is no honest real-M2
rewording of "send it to an agent that doesn't exist yet." This is
recorded in "Explicit exclusions" below, not silently dropped.

**"Options rendered but inert," per the roadmap's own item 15 wording,
is implemented as real `<button>` elements with no `onClick` handler at
all — genuinely inert, not visually disabled.** The reference file's
own markup uses `cursor: mine ? 'pointer' : 'default'` (`pointer` in
this variant, since `mine === true`), because its simulation lets the
owner actually click these rows. This slice deliberately keeps `cursor:
default` instead — a real, disclosed deviation from the reference
file's exact styling, because there is no real click behavior yet
(Wave D adds it); a pointer cursor over a control that does nothing
would misrepresent the control as functional, the same failure this
slice otherwise avoids.

Source quote (README, Decision card anatomy and owner-variant
paragraph, verbatim):

> - *Owner decision* (rare): border `#F1DEBE`, bg `#FEF9F0`, ink
>   `#8A5A08`, dot `#E0A32E` with `0 0 0 3px rgba(224,163,46,.24)`,
>   badge `your decision`, age `waiting 41m`, final chain chip `you` on
>   `#E0A32E`/`#3D2C06`, reason "the Architect agent stopped: this
>   changes a contract you froze". Option rows are live buttons.
>   Footer: "One of the few that needs a human…" plus **Let the
>   Architect rule**.
>
> The three options are always: **Allow a sentinel version** (`resumes
> now`), **Amend the A.1 contract** (`~25 min · 1 correction`), **Send
> back to the Architect agent** (`unknown · Terra idle`).

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from — the shared eyebrow /
headline / lede / chain-chip row plus the option-list markup, eliding
the footer bar this slice does not render):

```html
<div style="display:grid;grid-template-columns:36px minmax(0,1fr);gap:14px;padding:4px 34px 8px;animation:rise .22s ease-out">
  <span></span>
  <div style="min-width:0;max-width:60ch;border:1px solid {{ blk.border }};border-radius:14px;background:{{ blk.bg }};overflow:hidden">
    <div style="padding:15px 17px 13px">
      <div style="display:flex;align-items:center;gap:9px;font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:{{ blk.ink }}"><span style="width:7px;height:7px;border-radius:50%;background:{{ blk.dotBg }};box-shadow:0 0 0 3px {{ blk.dotRing }}"></span>{{ blk.badge }}<span style="margin-left:auto;letter-spacing:.06em;color:#A1927B">{{ blk.age }}</span></div>
      <div style="margin-top:9px;font-family:'Bricolage Grotesque',sans-serif;font-size:17.5px;font-weight:600;letter-spacing:-.015em;line-height:1.3;text-wrap:pretty">Should a theme-free output get a sentinel version, or does the frozen contract change?</div>
      <div style="margin-top:6px;font-size:13.5px;line-height:1.55;color:#6C6376;text-wrap:pretty">{{ blk.lede }}</div>
      <div style="display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-top:11px;font:500 11.5px 'IBM Plex Mono',monospace;color:{{ blk.ink }}"><span style="padding:3px 7px;border-radius:6px;background:{{ blk.chip }}">Terra</span><span style="color:#C4AE86">→</span><span style="padding:3px 7px;border-radius:6px;background:{{ blk.chip }}">Coordinator</span><span style="color:#C4AE86">→</span><span style="padding:3px 7px;border-radius:6px;background:{{ blk.chipOn }};color:{{ blk.chipOnInk }}">{{ blk.target }}</span><span style="font-family:'Public Sans',sans-serif;font-weight:400;font-size:12.5px;color:#8E8299">{{ blk.why }}</span></div>
    </div>
    <div style="display:flex;flex-direction:column;gap:1px;padding:0 9px 9px">
      <sc-for list="{{ blockerOptions }}" as="o" hint-placeholder-count="3">
      <button onClick="{{ o.onPick }}" style="display:block;width:100%;padding:11px 12px;border:1px solid {{ o.border }};border-radius:10px;background:#fff;text-align:left;cursor:{{ o.cursor }}" style-hover="border-color:#E0C79A;background:#FFFDF8">
        <div style="display:flex;align-items:baseline;gap:10px"><b style="font-size:14.5px;color:#221C29">{{ o.title }}</b><span style="margin-left:auto;flex:none;font:500 11px 'IBM Plex Mono',monospace;color:{{ o.costColor }}">{{ o.cost }}</span></div>
        <div style="margin-top:3px;font-size:13px;line-height:1.5;color:#6C6376;text-wrap:pretty">{{ o.body }}</div>
      </button>
      </sc-for>
    </div>
    <!-- footer bar: not rendered by this slice, see above -->
  </div>
</div>
```

For `mine === true` (this variant), `o.border` is always `'transparent'`
(no favoured option — the reference file's "Architect favours" styling
only applies to the ruling variant) and `o.costColor` is always `blk.ink`
(`#8A5A08`).

**Color discrepancy table — every owner-variant value checked against
this codebase's real B2 tokens; a much cleaner token match than C3's
ruling palette, only 3 real gaps:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| `border` `#F1DEBE` | `colors.warningBorder` | exact |
| `bg` `#FEF9F0` | `colors.warningWash` | exact |
| `ink` `#8A5A08` | `colors.warningText` | exact |
| `dotBg` `#E0A32E` | `colors.warning` | exact |
| `dotRing` `rgba(224,163,46,.24)` | (no token; derived from `colors.warning`'s RGB) | disclosed literal |
| `chip` `#FDF1DC` | `colors.warningChip` | exact |
| `chipOn` `#E0A32E` | `colors.warning` | exact |
| `chipOnInk` `#3D2C06` | none in `colors.ts` | disclosed literal |
| lede text `#6C6376` | `colors.inkSecondary` | exact |
| `why` text `#8E8299` | `colors.inkMuted` | exact |
| age text `#A1927B` (shared, already disclosed by C3) | none in `colors.ts` | disclosed literal |
| chain-arrow `#C4AE86` (shared, already disclosed by C3) | none in `colors.ts` | disclosed literal |
| option title `#221C29` | `colors.ink` | exact |
| option body `#6C6376` | `colors.inkSecondary` | exact |
| option background `#fff` | `colors.surface` | exact |
| hover border `#E0C79A` | `colors.focusHoverBorderAmber` | exact |
| hover background `#FFFDF8` | none in `colors.ts` (nearest, `colors.focusHoverCard` `#FCFBFD`, is a different, real value — not reused) | disclosed literal |

Five real, checked gaps (`dotRing`, `chipOnInk`, age text, arrow, hover
background) — the same disclosure convention as every prior slice: a
real gap is a checked, disclosed literal inline in the component, never
silently substituted with a near-but-wrong token, and never added to
`colors.ts` itself.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C4-DECISION-CARD-OWNER-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:431a1fd2f846f1e28f6bda398411c8a9696f3a5e"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`. The first real run found one
genuine defect — `OwnerDecisionCard`'s destructuring assignment
included an unused `packetId` field, a real `tsc` error
(`TS6133: 'packetId' is declared but its value is never read`) — fixed
by removing it from the destructure (the fixture's `packetId` field
itself is kept, as real metadata for a future wiring slice; only the
component doesn't need it yet). After that fix: 43/43 tests passed (35
existing + 8 new), typecheck and lint clean, production build
succeeded. This is disclosed here so the Decision Fidelity reviewer
knows the code block below is the corrected, passing version.

`apps/atlas/src/decision/ownerFixtures.ts` (new — the evidence data and
its types; no rendering logic):

```ts
/**
 * This is deliberately the SAME real scenario as C1's frozen
 * `apps/atlas/src/thread/fixtures.ts`'s `PACKET_A2_ENTRIES` — its final
 * entry (`k: "co"`, `14:56`, `escalate: true`) reads: "I can rule on
 * scope, corrections and dispatch — I cannot widen a frozen contract,
 * so this one goes to the owner. Terra holds its worktree meanwhile."
 * That is a real, already-established M1/M2 "no automated route, needs
 * a human" case — exactly what the owner-decision variant renders. This
 * fixture is a deliberately independent, hand-maintained object (not an
 * import from `../thread/fixtures`) so `decision/` stays standalone
 * from `thread/` until a real wiring slice joins them, matching this
 * program's own established pattern (`PacketThread` and `DecisionCard`
 * are each standalone until their own wiring slice). If C1's fixture
 * text ever changes, this object must be updated by hand to match —
 * the same kind of disclosed, hand-maintained coupling as C3's
 * `_REVIEW_ROUTES` citation.
 */
export interface OwnerOption {
  title: string;
  cost: string;
  body: string;
}

export interface OwnerDecisionExample {
  packetId: string;
  age: string;
  headline: string;
  lede: string;
  why: string;
  options: OwnerOption[];
}

/**
 * `headline`, `age` ("waiting 41m"), and both `options` are transcribed
 * verbatim from `Atlas Explorations.dc.html` — none is invented. `lede`
 * and `why` are adapted from the reference file's own `mine === true`
 * branch, replacing its fictional "the Architect agent" with "the
 * Coordinator" — the real M1/M2 actor that actually performs this
 * escalation, per `PACKET_A2_ENTRIES`'s own real final entry quoted
 * above. The reference file's third option ("Send back to the Architect
 * agent") is deliberately excluded: it depends on the M4 Architect
 * agent, which does not exist in M2, and there is nothing real to defer
 * to — see this slice's packet contract, Scope section.
 */
export const OWNER_DECISION_EXAMPLE: OwnerDecisionExample = {
  packetId: "A.2",
  age: "waiting 41m",
  headline: "Should a theme-free output get a sentinel version, or does the frozen contract change?",
  lede: "The Coordinator will not widen a contract you froze, so it escalated instead of guessing. Terra is holding its worktree until you answer.",
  why: "the Coordinator escalated: this changes a contract you froze",
  options: [
    {
      title: "Allow a sentinel version",
      cost: "resumes now",
      body: "Terra writes theme-less:1 for theme-free outputs. The A.1 contract stays frozen and no correction is spent.",
    },
    {
      title: "Amend the A.1 contract",
      cost: "~25 min · 1 correction",
      body: "A.1 reopens for one correction so an empty theme version becomes legal. A.2 pauses and keeps its worktree.",
    },
  ],
};
```

`apps/atlas/src/decision/OwnerDecisionCard.module.css` (new — CSS
Module, `var(--atlas-*)` only, following the exact C1/C3/B3/B4
pattern):

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
  border: 1px solid var(--atlas-owner-border);
  border-radius: 14px;
  background: var(--atlas-owner-bg);
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
  color: var(--atlas-owner-ink);
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--atlas-owner-dot);
  box-shadow: 0 0 0 3px var(--atlas-owner-dot-ring);
}

.age {
  margin-left: auto;
  letter-spacing: 0.06em;
  color: var(--atlas-owner-age);
}

.headline {
  margin-top: 9px;
  font-family: var(--atlas-font-display);
  font-size: 17.5px;
  font-weight: 600;
  letter-spacing: -0.015em;
  line-height: 1.3;
  text-wrap: pretty;
  color: var(--atlas-owner-headline);
}

.lede {
  margin: 6px 0 0;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-owner-lede);
  text-wrap: pretty;
}

.chainRow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin-top: 11px;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-owner-ink);
}

.chip {
  padding: 3px 7px;
  border-radius: 6px;
  background: var(--atlas-owner-chip);
}

.chipOn {
  padding: 3px 7px;
  border-radius: 6px;
  background: var(--atlas-owner-chip-on);
  color: var(--atlas-owner-chip-on-ink);
}

.arrow {
  color: var(--atlas-owner-arrow);
}

.why {
  font-family: var(--atlas-font-body);
  font-weight: 400;
  font-size: 12.5px;
  color: var(--atlas-owner-why);
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
  background: var(--atlas-owner-surface);
  text-align: left;
  cursor: default;
  font: inherit;
}

.option:hover {
  border-color: var(--atlas-owner-hover-border);
  background: var(--atlas-owner-hover-bg);
}

.optionRow {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.optionTitle {
  font-size: 14.5px;
  color: var(--atlas-owner-headline);
}

.optionCost {
  margin-left: auto;
  flex: none;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-owner-ink);
}

.optionBody {
  margin-top: 3px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--atlas-owner-lede);
  text-wrap: pretty;
}
```

`apps/atlas/src/decision/OwnerDecisionCard.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { OWNER_DECISION_EXAMPLE } from "./ownerFixtures";
import styles from "./OwnerDecisionCard.module.css";

/**
 * Owner-decision-variant colors from `Atlas Explorations.dc.html`'s
 * `blk` object (`mine === true` branch) plus the two markup-hardcoded
 * values shared with the ruling variant (`age`, `arrow` — already
 * disclosed by C3's `DecisionCard.tsx`). Every semantic color here
 * (`border`, `bg`, `ink`, `dotBg`, `chip`, `chipOn`) is a real B2
 * `colors.warning*` token — a cleaner token match than C3's ruling
 * palette. Two values have no equivalent token and stay disclosed
 * literals, checked directly against the reference file: `dotRing`
 * (derived from `colors.warning`'s RGB) and `chipOnInk` (`#3D2C06`, the
 * "you" chip's dark-brown text — no B2 token matches it). The hover
 * background (`#FFFDF8`) also has no exact token match and stays a
 * disclosed literal; the hover border reuses the real
 * `colors.focusHoverBorderAmber` token.
 */
const SHELL_VARS = {
  "--atlas-owner-border": colors.warningBorder,
  "--atlas-owner-bg": colors.warningWash,
  "--atlas-owner-ink": colors.warningText,
  "--atlas-owner-dot": colors.warning,
  "--atlas-owner-dot-ring": "rgba(224,163,46,.24)",
  "--atlas-owner-chip": colors.warningChip,
  "--atlas-owner-chip-on": colors.warning,
  "--atlas-owner-chip-on-ink": "#3D2C06",
  "--atlas-owner-age": "#A1927B",
  "--atlas-owner-arrow": "#C4AE86",
  "--atlas-owner-lede": colors.inkSecondary,
  "--atlas-owner-why": colors.inkMuted,
  "--atlas-owner-headline": colors.ink,
  "--atlas-owner-surface": colors.surface,
  "--atlas-owner-hover-border": colors.focusHoverBorderAmber,
  "--atlas-owner-hover-bg": "#FFFDF8",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function OwnerDecisionCard() {
  const { age, headline, lede, why, options } = OWNER_DECISION_EXAMPLE;
  return (
    <div className={styles.row} style={SHELL_VARS}>
      <span aria-hidden="true" />
      <div className={styles.card}>
        <div className={styles.head}>
          <div className={styles.eyebrow}>
            <span className={styles.dot} aria-hidden="true" />
            your decision
            <span className={styles.age}>{age}</span>
          </div>
          <div className={styles.headline}>{headline}</div>
          <p className={styles.lede}>{lede}</p>
          <div className={styles.chainRow}>
            <span className={styles.chip}>Terra</span>
            <span className={styles.arrow} aria-hidden="true">
              →
            </span>
            <span className={styles.chip}>Coordinator</span>
            <span className={styles.arrow} aria-hidden="true">
              →
            </span>
            <span className={styles.chipOn}>you</span>
            <span className={styles.why}>{why}</span>
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
      </div>
    </div>
  );
}

export default OwnerDecisionCard;
```

`apps/atlas/src/decision/OwnerDecisionCard.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { OwnerDecisionCard } from "./OwnerDecisionCard";
import { OWNER_DECISION_EXAMPLE } from "./ownerFixtures";

afterEach(cleanup);

describe("OwnerDecisionCard", () => {
  it("renders the real chain-chip actors (Terra, Coordinator, you), never the reference file's fictional Architect agent target", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText("Terra")).toBeInTheDocument();
    expect(screen.getByText("Coordinator")).toBeInTheDocument();
    expect(screen.getByText("you")).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent/)).toBeNull();
  });

  it("labels the eyebrow badge and age with the real, transcribed reference values", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText("your decision")).toBeInTheDocument();
    expect(screen.getByText(OWNER_DECISION_EXAMPLE.age)).toBeInTheDocument();
  });

  it("renders the verbatim headline question", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText(OWNER_DECISION_EXAMPLE.headline)).toBeInTheDocument();
  });

  it("attributes the escalation to the Coordinator, never to a fictional Architect agent persona", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText(OWNER_DECISION_EXAMPLE.why)).toBeInTheDocument();
    expect(screen.queryByText(/[Aa]rchitect agent/)).toBeNull();
  });

  it("renders exactly the 2 real options this slice keeps, and never the excluded third 'defer to the Architect agent' option", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getAllByRole("button")).toHaveLength(2);
    for (const option of OWNER_DECISION_EXAMPLE.options) {
      expect(screen.getByText(option.title)).toBeInTheDocument();
      expect(screen.getByText(option.cost)).toBeInTheDocument();
      expect(screen.getByText(option.body)).toBeInTheDocument();
    }
    expect(screen.queryByText(/Send back to the Architect agent/)).toBeNull();
  });

  it("renders no footer or footer action button — that anatomy is Wave D's, not this slice's", () => {
    render(<OwnerDecisionCard />);
    expect(screen.queryByText(/Let the Architect rule/)).toBeNull();
    expect(screen.queryByText(/One of the few that needs a human/)).toBeNull();
  });

  it("sets the card border and background CSS variables to the real colors.warning* tokens", () => {
    expect(colors.warningBorder).toBe("#F1DEBE");
    expect(colors.warningWash).toBe("#FEF9F0");
    const { container } = render(<OwnerDecisionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-owner-border")).toBe(colors.warningBorder);
    expect(root.style.getPropertyValue("--atlas-owner-bg")).toBe(colors.warningWash);
    expect(root.style.getPropertyValue("--atlas-owner-dot")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-owner-chip-on")).toBe(colors.warning);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<OwnerDecisionCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `PacketThread`, `DesktopShell`, or
   `App.tsx` — standalone, exactly like C3's `DecisionCard`.
2. This slice does not import from `apps/atlas/src/thread/fixtures.ts`
   or any other C1/C1B file — `ownerFixtures.ts` is an independent,
   hand-maintained object that deliberately mirrors the same real `A.2`
   scenario (see Scope).
3. Every color value is either a real B2 token or a disclosed literal
   checked directly against `Atlas Explorations.dc.html` (the
   discrepancy table above); none is invented or borrowed from a
   near-but-wrong existing token.
4. The option list renders exactly 2 real options, never the excluded
   third ("Send back to the Architect agent"); each option is a
   `<button>` with no `onClick` — genuinely inert, not merely styled to
   look disabled.
5. No footer, no footer button — deferred, disclosed, not silently
   dropped (see Scope).
6. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, or C3's own `apps/atlas/src/decision/
   DecisionCard.*`/`fixtures.ts` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/decision/ownerFixtures.ts` (new)
- `apps/atlas/src/decision/OwnerDecisionCard.module.css` (new)
- `apps/atlas/src/decision/OwnerDecisionCard.tsx` (new)
- `apps/atlas/src/decision/OwnerDecisionCard.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/tokens/`, and C3's own `fixtures.ts`/`DecisionCard.*`
are untouched.

The 8 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 43 total after this slice (35 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 7 thread tests, 5 mobile-shell tests, 10
desktop-shell tests — + 8 new). `npm run build` must still succeed;
`OwnerDecisionCard` is not expected to appear in the `dist/` bundle,
matching every prior standalone slice's own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `OwnerDecisionCard` renders the owner-decision
   variant's exact visual anatomy (eyebrow, headline, lede, chain-chip
   row, 2-item option list) using real B2 tokens or disclosed
   reference-file-checked literals, driven by the same real `A.2`
   escalation scenario C1 already established, with no fictional
   "Architect agent" persona, no footer, and no functioning command.
2. **Operating and threat model:** a trusted local dev box; the option
   rows are real `<button>` elements (for correct semantics/focus) but
   carry no `onClick` — clicking one does nothing, by construction.
3. **Explicit exclusions:** the ruling variant (C3, already merged),
   the third reference-file option ("Send back to the Architect
   agent" — depends on the nonexistent M4 Architect agent), the footer
   bar and its button (references the same nonexistent agent; a real
   command-driven footer is Wave D's, specifically D3), the Decision
   Fidelity record (C5), the crash card (C6), any wiring into
   `PacketThread`/`DesktopShell`/`App.tsx`/`../thread/fixtures.ts`.
4. **Assurance level:** practical component-rendering correctness with
   accurate reuse of C1's own already-reviewed real scenario,
   proportionate to a read-only view with no data dependency and no
   consumer yet — identical assurance posture to C3, with the added
   discipline of not silently importing a frozen sibling module.
5. **Acceptance proof:** the 8 named tests, the existing 35 `apps/atlas`
   tests continuing to pass (43 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color either a real token property or a
   literal checked directly against the reference file; no import of
   `../thread/fixtures` or C3's `DecisionCard`/`fixtures` modules.
7. **Proportionality ceiling:** one view component, one fixtures
   module, one CSS Module; no third option, no footer, no wiring, no
   second scenario.
8. **Stop and escalation rule:** wiring `OwnerDecisionCard` into
   `PacketThread`/a real packet thread, or wiring its option rows to a
   real command, is new, separately reviewed work (a future wiring
   slice and Wave D's D2/D3, respectively) — not decided implicitly
   here. Rendering the Decision Fidelity record or the crash card is
   C5's/C6's job, not this slice's. A discovered proof/contract defect
   against a frozen slice terminally returns that slice. One planning
   correction and one implementation correction are the maximum
   available.
