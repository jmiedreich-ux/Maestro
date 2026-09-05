# M2 Wave C — Decision Card, Ruling Variant — Candidate 01

**Slice ID:** `MB-SLICE-M2-C3-DECISION-CARD-RULING-01`
**Status:** `Corrected — Pending Targeted Decision Fidelity Verification`.
Full Decision Fidelity review found 2 blocking findings (a wrong
`operational_state.py` line-number citation, and an undisclosed gap
against the roadmap's own "link to the rule that fired" requirement);
one targeted planning correction resolved both, re-verified against the
real toolchain. No further planning correction is available for this
slice.
**Base:** `b84f32f` (`origin/master`)

## Scope, deliberately minimal

Wave C3 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the decision
card's **ruling variant only** — read-only rendering of an entry
resolved by Maestro's existing automated review routing. No owner
variant (C4), no fidelity record (C5), no crash card (C6), no wiring
into `PacketThread`, `DesktopShell`, or `App.tsx`. `DecisionCard` is a
standalone component, exactly like C1's `PacketThread` before C1B wired
it in.

**This slice cannot reuse `A.2`'s fixture thread from C1, and that is a
deliberate, checked decision, not an oversight.** `PACKET_A2_ENTRIES`'s
own final entry (`k: "co"`, `14:56`, `escalate: true`) reads: *"I can
rule on scope, corrections and dispatch — I cannot widen a frozen
contract, so this one goes to the owner."* That is, by its own text, an
entry with **no automated route** — the real M0-D01/roadmap ruling's
*owner decision* case (C4), not the *ruling* case this slice renders.
Rendering a ruling-variant card against `A.2`'s blocker would directly
contradict C1's own frozen fixture narrative. So this slice introduces
its own, separate, real evidence example instead of stretching `A.2`'s
to fit.

**The reference file's decision-card scenario is not reused either,
and the roadmap's own architecture ruling is why.** `Atlas
Explorations.dc.html`'s decision card renders a simulated "Architect
agent" persona — badge `architect agent ruling`, chain chips `Terra →
Coordinator → Architect agent`, footer button `Decide this myself`.
Per the M2 roadmap's own "Architecture ruling on the one real gap"
section (already committed to `docs/planning/m2-atlas-roadmap.md`,
lines 10–18, before this slice): *"M2 does not wait for M4 [...] an
entry resolved by Maestro's existing automated routing renders the
'ruling' variant, labeled by the actual mechanism (e.g. 'resolved by
routing policy'), with a link to the rule that fired."* This slice is
the first one that ruling actually governs. It reuses the reference
file's **exact visual anatomy** (card structure, colors, type,
spacing — every value cited below, checked directly against the file)
but replaces every piece of copy that names a fictional persona with
copy naming the real mechanism.

**"A link to the rule that fired" (corrected — blocking finding from
Decision Fidelity review: an earlier draft of this slice omitted this
requirement entirely, with no disclosed exclusion for it, which is
inconsistent with this program's own standing practice of disclosing
every real gap rather than silently dropping a requirement its own
cited authority states).** This slice renders that link as a literal,
exact textual citation of the fired rule — `rule:
_REVIEW_ROUTES["AwaitingReview","IndependentImplementation","Approve"]
→ "MergeReady"` in the trailing `why` text — not as a clickable
hyperlink. A real navigable link needs a real destination (a rule
detail view or source-jump target), and no such destination exists
anywhere in M2 yet — inventing one here would repeat the exact
"rendering a capability that does not exist" failure this slice
otherwise avoids. The citation is precise enough to trace, by hand, to
the exact fired dict entry in `operational_state.py`, which is the
substantive intent behind "link to the rule that fired." Building an
actual clickable link to a real rule-inspection surface is out of
scope for this slice (see Explicit exclusions, M0-D12 §3).

**The rendered evidence is a real M1 routing-table entry, not invented
product content.** `services/maestro/maestro/operational_state.py`'s
`_REVIEW_ROUTES` dict (already-reviewed M1 code, lines 71–75) contains:

```python
_REVIEW_ROUTES = {
    ("AwaitingIntegration", "Integration", "ValidateOnly"): "AwaitingReview",
    ("AwaitingIntegration", "Integration", "NeedsReplan"): "NeedsReplan",
    ("AwaitingReview", "IndependentImplementation", "Approve"): "MergeReady",
    ("AwaitingReview", "IndependentImplementation", "RequestChanges"): "AwaitingArchitect",
}
```

This slice's fixture cites exactly one entry —
`("AwaitingReview", "IndependentImplementation", "Approve") →
"MergeReady"` — the plain "everything went fine" route: a packet in
`AwaitingReview` whose `IndependentImplementation` review recorded
`Approve` always advances to `MergeReady`, deterministically, with no
human step. The specific packet id (`A.4`), attempt id (`A.4-01`), and
recorded time (`14:31`) are **illustrative example values**, the same
convention this program's own `A2`–`A5` backend packets already used
for example snapshot rows — not a transcription of any mockup scenario
and not a real recorded event. `A.4` is chosen because neither `A.1`
nor `A.2` (the only packets with real reference-file thread content)
is reused, avoiding any contradiction with C1's frozen fixture.

**Read-only, no option list, no footer button — narrower than the
reference file's own anatomy, and this is a real semantic difference,
not a visual simplification.** The reference file's ruling variant
still renders three clickable-looking option rows (one marked
"Architect favours") and a "Decide this myself" footer button, because
its fiction is an *ongoing* deliberation a human could interrupt. Real
M1 routing is not a deliberation — `record_and_route_review` applies
`_REVIEW_ROUTES` as a single deterministic lookup once a verdict is
recorded; there is no in-progress ruling to interrupt and no
alternative outcomes to weigh. Rendering an inert three-option list
here would misrepresent the mechanism as a live decision, which is
exactly the failure mode the roadmap's ruling exists to prevent. This
slice therefore renders only: eyebrow (dot + badge + timestamp) →
headline → lede → chain-chip evidence row — the card's anatomy up to
(not including) the option list, per the README's own ordering (quoted
below). The roadmap's own wording for this item already draws this
line: item 14 says "**Read-only rendering**", while item 15 (C4, the
owner variant) separately says "**Options rendered but inert**" — C4 is
where an option list first appears, not C3.

Source quote (README, Decision card anatomy and ruling-variant
paragraph, verbatim):

> **Decision card** (in-thread, indented to the message column,
> `max-width: 60ch`, radius 14, `rise` animation). Two variants driven
> by who owns the decision:
>
> - *Architect ruling* (default, ~90%): border `#DFD8EE`, bg `#FBFAFE`,
>   ink `#4A28CC`, dot `#5B34E8`, badge `architect agent ruling`, age
>   `ruling 6m`, chain chips `Terra → Coordinator → Architect agent`
>   with the reason "resolved without a human — policy lets the
>   Architect rule here". [...]
>
> Card anatomy, both variants: eyebrow row (dot + badge + right-aligned
> age) → question in Bricolage `17.5px/600`, `-.015em` → lede `13.5px`
> `#6C6376` → chain chip row (mono `11.5px`, `6px` radius chips, `→`
> separators in `#C4AE86`) → option list [...] → footer bar [...]

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from, elided to the eyebrow /
headline / lede / chain-chip row this slice implements):

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
    <!-- option list and footer: not rendered by this slice, see above -->
  </div>
</div>
```

The ruling-variant color object this markup's `blk.*` holes resolve to
(`Atlas Explorations.dc.html`, verbatim):

```js
{ border: '#DFD8EE', bg: '#FBFAFE', ink: '#4A28CC', dotBg: '#5B34E8', dotRing: 'rgba(91,52,232,.18)',
  chip: '#EFEBFB', chipOn: '#5B34E8', chipOnInk: '#FFFFFF',
  badge: 'architect agent ruling', age: 'ruling 6m', target: 'Architect agent',
  why: 'resolved without a human — policy lets the Architect rule here' }
```

**Color discrepancy table — every ruling-variant value checked against
this codebase's real B2 tokens, real matches used, two real gaps
disclosed as literals:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| `ink` `#4A28CC` | `colors.accentHover` | exact |
| `dotBg` `#5B34E8` | `colors.accent` | exact |
| `dotRing` `rgba(91,52,232,.18)` | (no token; derived from `colors.accent`'s RGB) | disclosed literal |
| `chip` `#EFEBFB` | `colors.accentWash[2]` | exact |
| `chipOn` `#5B34E8` | `colors.accent` | exact |
| `chipOnInk` `#FFFFFF` | `colors.surface` | exact |
| `border` `#DFD8EE` | none in `colors.ts` (nearest, `colors.borderStrong[1]` `#DAD2EC`, is a different, real value — not reused) | disclosed literal |
| `bg` `#FBFAFE` | none in `colors.ts` | disclosed literal |
| lede text `#6C6376` | `colors.inkSecondary` | exact |
| `why` text `#8E8299` | `colors.inkMuted` | exact |
| age text `#A1927B` (hardcoded in the markup, applies to both variants, not part of `blk`) | none in `colors.ts` | disclosed literal |
| chain-arrow `#C4AE86` (hardcoded in the markup, applies to both variants) | none in `colors.ts` | disclosed literal |

Five real, checked gaps (`dotRing`, `border`, `bg`, age text, arrow)
exist in the current token set. Per this program's established convention (C1's own
`AVATAR_PALETTE`, B3-02's idle-indicator fix), a real gap is disclosed
as a literal, checked directly against the reference file, inline in
the component — never silently substituted with the nearest existing
token, and never added to `colors.ts` itself (that module is reserved
for the README's own "### Color" table and "Semantic rule" paragraph,
per its own header comment; this card's colors come from a different
prose section, exactly like C1's Coordinator-avatar and `by`-avatar
literals).

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C3-DECISION-CARD-RULING-01` |
| `phase` | `PendingTargetedDecisionFidelityVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:b84f32f163618285d40d7fbd675999866d49c56c","git:full-planning-review-head:e8a87ca782ff58391634b516bed09cde713d9e4c","review:decision-fidelity:request-changes:2-blocking-findings"]` |

## Exact file contents

`apps/atlas/src/decision/fixtures.ts` (new — the evidence data and its
types; no rendering logic):

```ts
/**
 * Real M1 automated-routing evidence, not invented product content.
 * The route cited below is one real, already-reviewed entry from
 * `services/maestro/maestro/operational_state.py`'s `_REVIEW_ROUTES`
 * dict — the M2 Atlas roadmap's "Architecture ruling on the one real
 * gap" is why: the ruling variant renders real recorded routing
 * outcomes, never a simulated "Architect agent" persona. `packetId`,
 * `attemptId`, and `recordedAt` below are illustrative example values
 * (the same convention this program's own A2–A5 backend packets use
 * for example snapshot rows) — not a transcription of any mockup
 * scenario, and not a real recorded event. Keep `route` in sync with
 * `_REVIEW_ROUTES` by hand if that dict ever changes; there is no
 * automated cross-check between this TypeScript fixture and the
 * Python source it cites.
 */
export interface RulingRouteEvidence {
  fromState: string;
  reviewKind: string;
  verdict: string;
  toState: string;
}

export interface RulingExample {
  packetId: string;
  attemptId: string;
  recordedAt: string;
  route: RulingRouteEvidence;
}

/**
 * `_REVIEW_ROUTES[("AwaitingReview", "IndependentImplementation", "Approve")]
 * == "MergeReady"` (`operational_state.py`, line 74 — corrected,
 * blocking finding from Decision Fidelity review: the dict's first two
 * entries occupy lines 72-73, making this cited third entry line 74,
 * not line 73 as an earlier draft said) — an approved
 * independent-implementation review always advances a packet to
 * `MergeReady`, deterministically, with no human step.
 */
export const RULING_EXAMPLE: RulingExample = {
  packetId: "A.4",
  attemptId: "A.4-01",
  recordedAt: "14:31",
  route: {
    fromState: "AwaitingReview",
    reviewKind: "IndependentImplementation",
    verdict: "Approve",
    toState: "MergeReady",
  },
};
```

`apps/atlas/src/decision/DecisionCard.module.css` (new — CSS Module,
`var(--atlas-*)` only, following the exact C1/B3/B4 pattern):

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
  border: 1px solid var(--atlas-decision-border);
  border-radius: 14px;
  background: var(--atlas-decision-bg);
  overflow: hidden;
  padding: 15px 17px 13px;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-decision-ink);
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--atlas-decision-dot);
  box-shadow: 0 0 0 3px var(--atlas-decision-dot-ring);
}

.age {
  margin-left: auto;
  letter-spacing: 0.06em;
  color: var(--atlas-decision-age);
}

.headline {
  margin-top: 9px;
  font-family: var(--atlas-font-display);
  font-size: 17.5px;
  font-weight: 600;
  letter-spacing: -0.015em;
  line-height: 1.3;
  text-wrap: pretty;
  color: var(--atlas-decision-headline);
}

.lede {
  margin: 6px 0 0;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-decision-lede);
  text-wrap: pretty;
}

.chainRow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin-top: 11px;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-decision-ink);
}

.chip {
  padding: 3px 7px;
  border-radius: 6px;
  background: var(--atlas-decision-chip);
}

.chipOn {
  padding: 3px 7px;
  border-radius: 6px;
  background: var(--atlas-decision-chip-on);
  color: var(--atlas-decision-chip-on-ink);
}

.arrow {
  color: var(--atlas-decision-arrow);
}

.why {
  font-family: var(--atlas-font-body);
  font-weight: 400;
  font-size: 12.5px;
  color: var(--atlas-decision-why);
}
```

`apps/atlas/src/decision/DecisionCard.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { RULING_EXAMPLE } from "./fixtures";
import styles from "./DecisionCard.module.css";

/**
 * Ruling-variant colors from `Atlas Explorations.dc.html`'s `blk`
 * object (`mine === false` branch) plus two markup-hardcoded values
 * shared by both variants (`age`, `arrow`). Five have no equivalent B2
 * token and stay disclosed literals, each checked directly against the
 * reference file — see the discrepancy table in this slice's packet
 * contract: `dotRing`, `border`, `bg`, `age`, `arrow`. Every other
 * value below is a direct property of the real `colors` token.
 */
const SHELL_VARS = {
  "--atlas-decision-border": "#DFD8EE",
  "--atlas-decision-bg": "#FBFAFE",
  "--atlas-decision-ink": colors.accentHover,
  "--atlas-decision-dot": colors.accent,
  "--atlas-decision-dot-ring": "rgba(91,52,232,.18)",
  "--atlas-decision-chip": colors.accentWash[2],
  "--atlas-decision-chip-on": colors.accent,
  "--atlas-decision-chip-on-ink": colors.surface,
  "--atlas-decision-age": "#A1927B",
  "--atlas-decision-arrow": "#C4AE86",
  "--atlas-decision-lede": colors.inkSecondary,
  "--atlas-decision-why": colors.inkMuted,
  "--atlas-decision-headline": colors.ink,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function DecisionCard() {
  const { packetId, attemptId, recordedAt, route } = RULING_EXAMPLE;
  return (
    <div className={styles.row} style={SHELL_VARS}>
      <span aria-hidden="true" />
      <div className={styles.card}>
        <div className={styles.eyebrow}>
          <span className={styles.dot} aria-hidden="true" />
          resolved by routing policy
          <span className={styles.age}>recorded {recordedAt}</span>
        </div>
        <div className={styles.headline}>
          {packetId}&rsquo;s independent implementation review was approved — routing moved it to{" "}
          {route.toState} automatically.
        </div>
        <p className={styles.lede}>
          Maestro&rsquo;s routing table advances an approved independent implementation review straight
          to {route.toState} with no human step. This card records that outcome as evidence, not as an
          open question.
        </p>
        <div className={styles.chainRow}>
          <span className={styles.chip}>
            {attemptId} · {route.fromState}
          </span>
          <span className={styles.arrow} aria-hidden="true">
            →
          </span>
          <span className={styles.chip}>
            {route.reviewKind} · {route.verdict}
          </span>
          <span className={styles.arrow} aria-hidden="true">
            →
          </span>
          <span className={styles.chipOn}>{route.toState}</span>
          <span className={styles.why}>
            rule: _REVIEW_ROUTES["{route.fromState}","{route.reviewKind}","{route.verdict}"] → "
            {route.toState}"
          </span>
        </div>
      </div>
    </div>
  );
}

export default DecisionCard;
```

`apps/atlas/src/decision/DecisionCard.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { DecisionCard } from "./DecisionCard";
import { RULING_EXAMPLE } from "./fixtures";

afterEach(cleanup);

describe("DecisionCard (ruling variant)", () => {
  it("renders the real routing-table evidence in the chain-chip row, not the reference file's fictional persona chain", () => {
    render(<DecisionCard />);
    const { attemptId, route } = RULING_EXAMPLE;
    expect(screen.getByText(`${attemptId} · ${route.fromState}`)).toBeInTheDocument();
    expect(screen.getByText(`${route.reviewKind} · ${route.verdict}`)).toBeInTheDocument();
    expect(screen.getByText(route.toState)).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent/)).toBeNull();
    expect(screen.queryByText(/Terra/)).toBeNull();
  });

  it("cites the exact fired rule as text evidence — the roadmap's 'link to the rule that fired' requirement, satisfied as a precise citation rather than an unbuildable hyperlink", () => {
    render(<DecisionCard />);
    const { route } = RULING_EXAMPLE;
    expect(
      screen.getByText(
        (_, node) =>
          node?.textContent ===
          `rule: _REVIEW_ROUTES["${route.fromState}","${route.reviewKind}","${route.verdict}"] → "${route.toState}"`,
      ),
    ).toBeInTheDocument();
  });

  it("labels the eyebrow badge by the real mechanism, not a simulated ruling persona", () => {
    render(<DecisionCard />);
    expect(screen.getByText("resolved by routing policy")).toBeInTheDocument();
    expect(screen.queryByText(/architect agent ruling/i)).toBeNull();
  });

  it("shows a recorded timestamp, not an in-progress ruling duration", () => {
    render(<DecisionCard />);
    expect(screen.getByText(`recorded ${RULING_EXAMPLE.recordedAt}`)).toBeInTheDocument();
    expect(screen.queryByText(/ruling \d/)).toBeNull();
  });

  it("renders no option list and no footer action button — read-only, per this slice's scope", () => {
    render(<DecisionCard />);
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryByText(/Decide this myself/)).toBeNull();
    expect(screen.queryByText(/Allow a sentinel version/)).toBeNull();
  });

  it("sets the card border and background CSS variables to the reference file's real, disclosed literal values, not an existing but wrong token", () => {
    // Matches the established DesktopShell/MobileShell test pattern:
    // jsdom does not apply this project's CSS Modules stylesheet, so
    // these values are asserted on the CSS custom property itself
    // (set inline, on the root element, by SHELL_VARS), not on a
    // child element's resolved/computed style.
    expect(colors.borderStrong[1]).toBe("#DAD2EC");
    const { container } = render(<DecisionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-decision-border")).toBe("#DFD8EE");
    expect(root.style.getPropertyValue("--atlas-decision-border")).not.toBe(colors.borderStrong[1]);
    expect(root.style.getPropertyValue("--atlas-decision-bg")).toBe("#FBFAFE");
  });

  it("sets the dot and highlighted-chip CSS variables to colors.accent, not colors.accentHover", () => {
    expect(colors.accent).toBe("#5B34E8");
    expect(colors.accentHover).toBe("#4A28CC");
    const { container } = render(<DecisionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-decision-dot")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-decision-chip-on")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-decision-chip-on-ink")).toBe(colors.surface);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<DecisionCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files above were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`: 35/35 tests passed (27 existing +
8 new), typecheck and lint were clean, and the production build
succeeded. Two of the originally-drafted tests failed on the first real
run — both asserted a CSS-Module-resolved computed style
(`element.style.border`/`.background`) that jsdom does not populate for
stylesheet-applied rules, only for genuinely inline styles; the fix
(verified working, shown above) asserts the CSS custom property itself
on the root element, matching the exact pattern already established by
`DesktopShell.test.tsx`/`MobileShell.test.tsx`. This is disclosed here
so the Decision Fidelity reviewer knows the code block above is the
corrected, passing version, not the first draft.

**Re-verified after the targeted planning correction below (the "link
to the rule that fired" fix and the line-number fix):** all four files,
with the correction applied, were rebuilt in a scratch copy and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run again for real — 35/35 tests passed (27 existing + 8 new,
the 8th being the new rule-citation test added by this correction),
typecheck, lint, and build all clean.

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `PacketThread`, `DesktopShell`, or
   `App.tsx` — standalone, exactly like C1's `PacketThread` before
   C1B.
2. `RULING_EXAMPLE`'s `route` field cites a real, already-reviewed
   entry from `operational_state.py`'s `_REVIEW_ROUTES`; `packetId`,
   `attemptId`, and `recordedAt` are disclosed illustrative example
   values, not a transcription of the reference file's own decision
   scenario (deliberately not reused — see Scope) and not a real
   recorded event.
3. Every color value is either a real B2 token or a disclosed literal
   checked directly against `Atlas Explorations.dc.html` (the
   discrepancy table above); none is invented or borrowed from a
   near-but-wrong existing token.
4. No option list, no live or inert button, no footer action — this
   slice is fully read-only. C4 (owner variant) is where an option
   list first appears in this program.
5. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`, or
   `apps/atlas/src/thread/` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/decision/fixtures.ts` (new)
- `apps/atlas/src/decision/DecisionCard.module.css` (new)
- `apps/atlas/src/decision/DecisionCard.tsx` (new)
- `apps/atlas/src/decision/DecisionCard.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`, and
`apps/atlas/src/tokens/` are untouched.

The 8 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 35 total after this slice (27 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 7 thread tests, 5 mobile-shell tests, 10 desktop-shell tests
— + 8 new). `npm run build` must still succeed; `DecisionCard` is not
expected to appear in the `dist/` bundle, matching B2's, B4's, and C1's
own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `DecisionCard` renders the ruling variant's
   exact visual anatomy (eyebrow, headline, lede, chain-chip row) using
   real B2 tokens or disclosed reference-file-checked literals, driven
   by one real M1 routing-table entry's evidence, with no fictional
   "Architect agent" persona and no live or inert interactive control.
2. **Operating and threat model:** a trusted local dev box; no user
   interaction (this view has none — fully read-only, no button, no
   clickable option row).
3. **Explicit exclusions:** the owner-decision variant (C4), the
   option list and its footer button (both variants — deferred to C4),
   the Decision Fidelity record (C5), the crash card (C6), any wiring
   into `PacketThread`/`DesktopShell`/`App.tsx`, any second evidence
   example, and a real clickable link/navigable destination for "the
   rule that fired" (rendered here as an exact textual citation
   instead — see Scope; a real rule-inspection surface to link to does
   not exist anywhere in M2 yet, and is not this slice's to invent).
4. **Assurance level:** practical component-rendering correctness with
   an accurately cited real backend mechanism, proportionate to a
   read-only view with no data dependency and no consumer yet —
   identical assurance posture to C1, with the added rigor of citing a
   cross-language (Python routing table → TypeScript fixture) source of
   truth accurately, disclosed as a hand-maintained, unchecked coupling.
5. **Acceptance proof:** the 8 named tests, the existing 27 `apps/atlas`
   tests continuing to pass (35 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color either a real token property or a
   literal checked directly against the reference file; no code path
   reads or imports Python source (the citation is documentation-only).
7. **Proportionality ceiling:** one view component, one fixtures
   module, one CSS Module; no option list, no footer, no second
   variant, no wiring.
8. **Stop and escalation rule:** wiring `DecisionCard` into
   `PacketThread` or a real packet thread is a new, separately reviewed
   slice — not decided implicitly here. Rendering the owner variant,
   the option list, or any interactive control is C4's job, not this
   slice's. If a future backend change alters `_REVIEW_ROUTES`'s cited
   entry, `RULING_EXAMPLE.route` must be updated by hand — a discovered
   drift here is a defect against this slice, not a silent
   acceptability. A discovered proof/contract defect against a frozen
   slice terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
