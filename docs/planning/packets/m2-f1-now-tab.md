# M2 Wave F — Mobile Now Tab — Candidate 01

**Slice ID:** `MB-SLICE-M2-F1-NOW-TAB-01`
**Status:** `Draft — Targeted correction applied (the first draft's progress-fill color used the mockup's non-blocked barColor value on a genuinely blocked progress bar, contradicting this same packet's own avatar-styling principle; two color-token audit misses; a stale base-commit citation in Pre-verification; and three new-field test assertions were tautological, only cross-checked against derivePacketHeaderState's own live output, not a hardcoded literal), pending Targeted Decision Fidelity Verification`
**Base:** `09545e6` (full: `09545e6d2ba2d8fe7d0177c776618ee53f0ab930`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 33, *"F1 — Now tab: hero card, state-table-driven
headline/bar/timestamps, 'what happens next' panel."* Wave F's own
header says it plainly: *"Mobile remaining tabs (reuse Wave C/E logic;
no new backend)."* This slice is frontend-only — no backend file is
touched, no new command, no new persisted state.

This slice does two things:

1. **Extends** the already-real, already-shared
   `derivePacketHeaderState` (`apps/atlas/src/thread/headerState.ts`,
   B-wave/desktop C-wave code, already consumed by
   `PacketHeader.tsx`) with the additional fields the mobile hero card
   needs (`headline`, `subline`, `progressPercent`, `boundaryBegin`,
   `boundaryHeld`, `nextPanelHeading`, `nextPanelText`) — the exact
   extension this function's own doc comment already anticipated
   ("the hero card and mobile 'what happens next' panel are separate,
   later Wave F work that should call this same function once it's
   extended to those surfaces").
2. **Adds** a new `NowTab.tsx` component, wired into the real, already-
   merged `MobileShell.tsx`'s `"now"` tab (replacing its placeholder
   text), that renders that state plus the real, already-reviewed C4
   `OwnerDecisionCard` component (reused verbatim, not re-derived).

No Chat/Plan/Activity tab content is touched beyond the one line in
`MobileShell.tsx` that routes `"now"` to the new component — those are
F2/F3/F4's own separate roadmap items.

## Independent research before design

Before writing any code, I re-derived every claim below directly from
source (not from a prior research summary) — reading
`Atlas Mobile.dc.html` myself, `headerState.ts`, `PacketHeader.tsx`,
`MobileShell.tsx`, `fixtures.ts`, `agentStyle.ts`, `OwnerDecisionCard.tsx`,
`ownerFixtures.ts`, `colors.ts`, and `shape.ts` directly.

## Evidence: the one real trajectory, and what is genuinely new

`PACKET_A2_ENTRIES` (`apps/atlas/src/thread/fixtures.ts:32-82`, C1,
frozen) contains exactly one real, fixture-backed narrative: Terra
becomes blocked at 14:52 and the Coordinator escalates to the owner at
14:56 (`escalate: true`). `headerState.ts`'s own doc comment (already
merged, unmodified content quoted here) established the discipline
this slice follows: implement only that one real trajectory; report
`"unavailable"` for every other branch, never invent a plausible
number.

**The one genuinely new derived value this slice adds:**
`PACKET_A2_ENTRIES[1]` (`fixtures.ts:39-55`, Terra's first message) has
a real `plan.steps` array — present in the real reference data,
unused by any slice before this one (`fixtures.ts:19`'s own comment:
*"Present in the real reference data; not yet rendered by any
slice"*):

```
steps: [
  { text: "...", status: "done" },
  { text: "...", status: "done" },
  { text: "...", status: "now" },
  { text: "...", status: "open" },
  { text: "...", status: "open" },
]
```

2 of 5 steps are `"done"` — a real, non-invented **40%**. The
reference file's own hero card (`Atlas Mobile.dc.html:686`) shows
`pct: sys === 'crashed' || blocked ? '41%' : ...` for this exact
branch — a plausible-looking illustrative number with **no real
formula behind it anywhere in the reference file's own JS** (checked
directly: `pct` is a hand-picked literal in every branch of that
ternary chain, never computed from `steps` or any other field). This
slice's own 40% is deliberately **not** the mockup's 41% — it is
independently derived from real fixture data the mockup itself never
used for this purpose, and the two numbers' closeness is coincidental,
not copied.

`boundaryBegin`/`boundaryHeld` are likewise real: the reference file's
blocked-branch `bar` object (`Atlas Mobile.dc.html:691-692`) is
`{ a: 'began 13:51', b: 'held at 14:52', c: 'clock paused', ... }` — the
`a`/`b` timestamps are real (they match `PACKET_A2_ENTRIES`' own first
`"wk"` entry at `13:51` and the entry where Terra reports being
blocked at `14:52`, exactly), so this slice derives them from the real
entries rather than hardcoding the mockup's own literal strings. The
third value, `c: 'clock paused'`, is **not** reused — it asserts a
system behavior (elapsed-time accounting pausing while a packet is
blocked) that is not verified anywhere in this codebase's real backend,
so this slice omits it rather than assert an unverified claim.

`headline`/`subline`/`nextPanelText` are honest paraphrases of real
entry content, following the same convention `stateLine` (already
merged, unmodified) already established — not verbatim mockup text:
`subline: "Escalated to you · worktree held"` and `nextPanelText`
reflect the Coordinator's own real 14:56 entry text (*"...so this one
goes to the owner. Terra holds its worktree meanwhile."*) —
paraphrased, not fabricated.

## Design rationale

1. **`derivePacketHeaderState` is extended, not duplicated.** Both
   `PacketHeader.tsx` (desktop) and the new `NowTab.tsx` (mobile) call
   the same function — the README's own single-state-source rule,
   already quoted in this function's doc comment, requires exactly
   this.
2. **`OwnerDecisionCard` (C4) is reused verbatim, not re-derived.**
   Wave F's own header rule is "reuse Wave C/E logic; no new backend."
   `OwnerDecisionCard.tsx` already renders the real escalation
   question, the real chain-of-custody chips, and the real two options
   (`ownerFixtures.ts`'s `OWNER_DECISION_EXAMPLE`) — options rendered
   but inert, exactly matching C4's own already-reviewed scope ("no
   command wiring yet"). This slice adds zero new escalation-rendering
   logic.
3. **No Stop/Start or "Open conversation" control is rendered.** The
   roadmap's own Wave D header states the rule this slice follows:
   *"a command is available through Atlas only once its own guarded
   command exists and passes review"* (M0-D01's amendment). No real
   backend command exists for stopping/starting an agent's work or
   opening the thread view from this tab. Rendering an inert-but-
   visible button for a capability this build genuinely does not have
   would misrepresent it — unlike C4's decision options, which are
   inert only because D2/D3's wiring hasn't landed *yet* for an action
   whose backend command already exists and is reviewed.
4. **Avatar styling reuses `AGENT_STYLE.wait`, not `AGENT_STYLE.run`.**
   E4's own `agents.ts` fixture (`agents.ts:50-65`) shows Terra with
   `styleKey: "run"` and `pct: "58%"` — but that is a different,
   later, still-running simulated moment of the same persona (Wave
   E's own Agents-roster scenario). This slice's own real trajectory
   has Terra genuinely blocked/idle, so `AGENT_STYLE.wait` (the honest
   choice for "idle") is used instead — reusing `run`'s styling here
   would visually imply Terra is still working, which is false for
   this trajectory.
5. **Every color is routed through a token or a disclosed literal, none
   left as a bare hex in the CSS module** — matching every other
   component's own established convention in this codebase (checked
   directly against `PacketHeader.tsx`, `OwnerDecisionCard.tsx`,
   `MobileShell.tsx`, `AgentsRoster.tsx`). See the full token audit in
   the `NowTab.tsx` code block's own doc comment below — every real
   token match and every disclosed literal was independently checked
   against `colors.ts` and `shape.ts`, not assumed. (Self-caught before
   dispatch: an earlier draft left `#8C6BFF`/`#A78BFF`/`#8E8299`/`#fff`
   as bare CSS literals despite each having a real token match, and
   its own doc comment falsely claimed `colors.accentLight` was used
   when it was not actually referenced anywhere in that draft — fixed
   before this packet was finalized, see Pre-verification.)

## Guards

1. This slice modifies exactly 4 existing files
   (`apps/atlas/src/thread/headerState.ts`,
   `apps/atlas/src/thread/PacketHeader.test.tsx`,
   `apps/atlas/src/shell/MobileShell.tsx`,
   `apps/atlas/src/shell/MobileShell.test.tsx`) and adds exactly 3 new
   files (`apps/atlas/src/shell/NowTab.tsx`,
   `apps/atlas/src/shell/NowTab.module.css`,
   `apps/atlas/src/shell/NowTab.test.tsx`) — no backend file, no other
   frontend file, touched.
2. `PacketHeader.tsx` and its existing test assertions are **not**
   modified beyond adding new test cases for the new fields —
   `PacketHeaderState`'s existing fields (`eyebrow`, `title`,
   `isBlocked`, `stateLine`, `lastReport`, `blocker`, `nextLabel`,
   `next`) keep their exact existing values for the exact existing
   inputs; only new fields are added to the interface and its return
   object.
3. `MobileShell.test.tsx`'s pre-existing
   `"renders exactly four tabs..."` test now scopes its button query
   to the tab bar's own `<nav aria-label="Atlas tabs">` — with real
   content now rendered in the Now tab (the reused `OwnerDecisionCard`
   renders 2 real `<button>`s of its own), an unscoped
   `getAllByRole("button")` would pick those up too. This is the
   correct, intended consequence of rendering real content, not a
   defect — the same pattern this session's own M2-D2 slice applied to
   an analogous test.
4. `MobileShell.test.tsx`'s pre-existing "defaults to Now selected"
   test's assertion of the literal placeholder text `"Now tab"` is
   replaced with an assertion that the real `<h1>Now</h1>` heading
   renders and the placeholder text does not — the correct, intended
   consequence of F1 replacing that placeholder, not a regression.
5. No new command, no new `OperationalStateStore` interaction, no
   backend file touched at all.
6. **Disclosed visual-layout debt (not fixed in this slice):**
   `OwnerDecisionCard`'s own CSS (`OwnerDecisionCard.module.css:1-6`)
   uses a desktop-sized horizontal padding (`34px`, matching desktop's
   own content gutter) and a `36px` leading icon-gutter grid column
   sized for its desktop list context. Embedded directly inside the
   mobile Now tab's own `18px` gutter, this will not visually align
   flush with the rest of the tab's content — a real, disclosed seam,
   not fixed here, since restyling `OwnerDecisionCard` for a second
   consumption context is a larger, separate concern than reusing it
   (Wave F's own explicit "reuse ... logic" directive, not "reuse
   pixel-identical layout"). No automated browser-rendering
   verification was performed for this same reason previously
   disclosed in this session (M2-E4's packet): the available browser
   automation tooling failed outright in this environment.
7. This slice does not implement F2 (Chat tab), F3 (Activity tab), or
   F4 (Plan tab) — those are separate, future roadmap items.

## `apps/atlas/src/thread/headerState.ts` (modified — full new content)

```typescript
import type { ThreadEntry } from "./fixtures";

/**
 * The README's own single-state-source rule (verbatim): "Picking an
 * option appends resolution messages to the thread and updates the
 * header summary, session label, hero card, boundary timestamps, and
 * 'what happens next' together — they must all read from one state
 * value, not be set independently." This is that one function for the
 * packet-thread header, extended by F1 to also cover the mobile hero
 * card and "what happens next" panel — the desktop `PacketHeader.tsx`
 * (this function's original, only consumer) and the new mobile
 * `NowTab.tsx` both call it, so neither surface re-derives its own copy.
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
 *
 * `progressPercent` (added by F1) is the one genuinely new derived
 * value: `PACKET_A2_ENTRIES[1]`'s own real `plan.steps` array (present
 * in the real reference data, unused by any slice before F1) has 2
 * "done" of 5 real steps — a real, non-invented 40%, not the
 * reference file's own fabricated "41%" (`Atlas Mobile.dc.html`'s
 * `pct: ... blocked ? '41%' ...` has no real formula behind it — a
 * plausible-looking illustrative number, not derivable from any real
 * fixture field, so it is not reused here). `boundaryBegin`/
 * `boundaryHeld` are likewise real: the first real "wk" (Terra) entry's
 * own timestamp, and the entry where Terra reports being blocked.
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
  headline: string;
  subline: string;
  progressPercent: number | "unavailable";
  boundaryBegin: string;
  boundaryHeld: string;
  nextPanelHeading: string;
  nextPanelText: string;
}

export function derivePacketHeaderState(entries: ThreadEntry[]): PacketHeaderState {
  const escalation = entries.find((entry) => entry.escalate === true);
  const isBlocked = escalation !== undefined;
  const lastImplementorReport = [...entries].reverse().find((entry) => entry.k === "wk");
  const firstImplementorEntry = entries.find((entry) => entry.k === "wk");
  const planEntry = [...entries].reverse().find((entry) => entry.plan !== undefined);
  const progressPercent =
    planEntry?.plan !== undefined
      ? Math.round(
          (planEntry.plan.steps.filter((step) => step.status === "done").length /
            planEntry.plan.steps.length) *
            100,
        )
      : "unavailable";
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
    headline: isBlocked ? "Blocked" : "unavailable",
    subline: isBlocked ? "Escalated to you · worktree held" : "unavailable",
    progressPercent: isBlocked ? progressPercent : "unavailable",
    boundaryBegin: isBlocked ? (firstImplementorEntry?.time ?? "unavailable") : "unavailable",
    boundaryHeld: isBlocked ? (lastImplementorReport?.time ?? "unavailable") : "unavailable",
    nextPanelHeading: "what happens next",
    nextPanelText: isBlocked
      ? "Nothing is expected from Terra until you answer — its worktree stays held while the packet is blocked."
      : "unavailable",
  };
}
```

## `apps/atlas/src/shell/NowTab.tsx` (new)

```typescript
import type { CSSProperties } from "react";
import { colors, fontFamily, radii, spacing } from "../tokens";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import { AGENT_STYLE } from "../agents/agentStyle";
import { OwnerDecisionCard } from "../decision/OwnerDecisionCard";
import styles from "./NowTab.module.css";

/**
 * Hero-card colors from `Atlas Mobile.dc.html`'s real Now-tab markup
 * (lines 48-63 of the reference file), checked directly against
 * `colors.ts`. Real token matches: `colors.navGround` (card
 * background), `colors.accentLight` (live dot), `colors.navTextInactive`
 * (the progress track's fill — the mockup's own real blocked-branch
 * `barColor` is `#B7ADC1`, not `#A78BFF`; `#A78BFF` is that same
 * ternary's *non-blocked* branch, checked directly at
 * `Atlas Mobile.dc.html:687` — corrected by targeted correction, see
 * below), `colors.navActiveBg` (the progress track's own background,
 * `rgba(255,255,255,.13)` — an exact string match, also corrected by
 * targeted correction), `colors.inkFaint` (role text and boundary
 * timestamps — the same hex the mockup uses, `#A79BB4`), `colors.inkMuted`
 * (eyebrow label), and `colors.surface` (the meta-grid cards' white
 * background — the mockup's own `#fff`). The avatar bg/ink reuse the
 * real, already-reviewed `AGENT_STYLE.wait` pair from E4's
 * `agentStyle.ts` — Terra is genuinely idle/blocked in this real
 * trajectory, not running, so the "wait" style key is the honest
 * choice, not "run" (which E4's own Agents-roster fixture uses for a
 * different, later simulated moment of the same persona — not reused
 * here to avoid implying this hero card shows that same moment). The
 * same "blocked, not running" principle applies to the progress fill
 * color: an independent Decision Fidelity review found the first
 * draft picked the mockup's own *non-blocked* fill color here, which
 * directly contradicted this same principle already correctly applied
 * to the avatar — fixed to the real blocked-branch value.
 * Three values have no equivalent token and stay disclosed literals,
 * checked against every color family in `colors.ts`, not assumed: the
 * headline/name text (`#EDE8F1`), the subline text (`#C6BCD2`), the
 * "what happens next" panel's own body text color (`#3D3350`), and the
 * card's own 24px corner radius (`radii.mobileCardPx` only states an
 * 18-22px range; the reference file's own hero card is 24px, not
 * forced into the stated range). The hero card's own drop shadow
 * (`0 16px 34px rgba(30,20,45,.22)`, transcribed directly into
 * `NowTab.module.css`) is also a disclosed, unmatched literal — an
 * `rgba` shadow value, not a solid color, so it was not caught by the
 * hex-literal check above; noted here for completeness.
 */
const SHELL_VARS = {
  "--atlas-hero-bg": colors.navGround,
  "--atlas-hero-ink": "#EDE8F1",
  "--atlas-hero-ink-muted": colors.inkFaint,
  "--atlas-hero-avatar-bg": AGENT_STYLE.wait.avBg,
  "--atlas-hero-avatar-ink": AGENT_STYLE.wait.avColor,
  "--atlas-hero-track": colors.navActiveBg,
  "--atlas-hero-fill": colors.navTextInactive,
  "--atlas-hero-radius": "24px",
  "--atlas-card-radius": `${radii.mobileCardPx.max}px`,
  "--atlas-gutter": `${spacing.mobileGutterPx}px`,
  "--atlas-eyebrow": colors.inkMuted,
  "--atlas-live-dot": colors.accentLight,
  "--atlas-card-surface": colors.surface,
  "--atlas-subline": "#C6BCD2",
  "--atlas-next-text": "#3D3350",
  "--atlas-owner-bg": colors.warningWash,
  "--atlas-owner-ink": colors.warningText,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * Mobile "Now" tab — the single-state-source hero card, boundary
 * timestamps, meta grid, real escalation decision (reusing C4's
 * `OwnerDecisionCard` verbatim per the roadmap's own Wave F rule —
 * "reuse Wave C/E logic; no new backend"), and "what happens next"
 * panel, all read from one `derivePacketHeaderState` call. No Stop/
 * Start or "Open conversation" affordance is rendered — those need
 * their own guarded backend commands (per this roadmap's own M0-D01
 * amendment: "a command is available through Atlas only once its own
 * guarded command exists and passes review"), none of which exist yet;
 * adding inert-but-visible buttons for actions with no real backend at
 * all (unlike D2/D3's already-real resolve-decision command) would
 * misrepresent capability this build does not have.
 */
export function NowTab() {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
  const progressWidth =
    state.progressPercent === "unavailable" ? "0%" : `${state.progressPercent}%`;

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.eyebrowRow}>
        <span className={styles.eyebrow}>{state.eyebrow}</span>
        <span className={styles.live}>
          <span className={styles.liveDot} aria-hidden="true" />
          live
        </span>
      </div>
      <h1 className={styles.pageTitle}>Now</h1>

      <div className={styles.hero}>
        <div className={styles.heroHead}>
          <span className={styles.avatar} aria-hidden="true">
            TE
          </span>
          <div className={styles.identity}>
            <div className={styles.name}>Terra</div>
            <div className={styles.role}>Implementor · A.2 Runtime Package</div>
          </div>
        </div>
        <div className={styles.headline}>{state.headline}</div>
        <div className={styles.subline}>{state.subline}</div>

        <div className={styles.progressBlock}>
          <div className={styles.track}>
            <span className={styles.fill} style={{ width: progressWidth }} />
          </div>
          <div className={styles.boundaryRow}>
            <span>
              {state.boundaryBegin === "unavailable"
                ? "unavailable"
                : `began ${state.boundaryBegin}`}
            </span>
            <span>
              {state.boundaryHeld === "unavailable"
                ? "unavailable"
                : `held at ${state.boundaryHeld}`}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.metaGrid}>
        <div className={styles.metaCard}>
          <div className={styles.metaLabel}>Last report</div>
          <div className={styles.metaValue}>{state.lastReport}</div>
        </div>
        <div className={styles.metaCard}>
          <div className={styles.metaLabel}>Blocker</div>
          <div className={styles.metaValue}>{state.blocker}</div>
        </div>
      </div>

      {state.isBlocked ? <OwnerDecisionCard /> : null}

      <div className={styles.nextPanel}>
        <div className={styles.nextHeading}>{state.nextPanelHeading}</div>
        <p className={styles.nextText}>{state.nextPanelText}</p>
      </div>
    </div>
  );
}

export default NowTab;
```

## `apps/atlas/src/shell/NowTab.module.css` (new)

```css
.tab {
  padding: 8px var(--atlas-gutter) 22px;
  font-family: var(--atlas-font-body);
}

.eyebrowRow {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 4px 0 2px;
}

.eyebrow {
  font: 600 11px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-eyebrow);
}

.live {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--atlas-eyebrow);
}

.liveDot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--atlas-live-dot);
}

.pageTitle {
  margin: 6px 0 16px;
  font-family: var(--atlas-font-display);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.hero {
  padding: 20px;
  border-radius: var(--atlas-hero-radius);
  background: var(--atlas-hero-bg);
  color: var(--atlas-hero-ink);
  box-shadow: 0 16px 34px rgba(30, 20, 45, 0.22);
}

.heroHead {
  display: flex;
  align-items: center;
  gap: 11px;
}

.avatar {
  width: 36px;
  height: 36px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--atlas-hero-avatar-bg);
  color: var(--atlas-hero-avatar-ink);
  font: 600 12px var(--atlas-font-mono);
}

.identity {
  min-width: 0;
  flex: 1;
}

.name {
  font-size: 15px;
  font-weight: 700;
}

.role {
  font-size: 12.5px;
  color: var(--atlas-hero-ink-muted);
}

.headline {
  font-family: var(--atlas-font-display);
  font-size: 27px;
  font-weight: 600;
  letter-spacing: -0.025em;
  margin-top: 16px;
}

.subline {
  font-size: 13.5px;
  color: var(--atlas-subline);
  margin-top: 3px;
}

.progressBlock {
  margin-top: 18px;
}

.track {
  position: relative;
  height: 6px;
  border-radius: 999px;
  background: var(--atlas-hero-track);
}

.fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 999px;
  background: var(--atlas-hero-fill);
}

.boundaryRow {
  display: flex;
  justify-content: space-between;
  margin-top: 9px;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-hero-ink-muted);
}

.metaGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 12px;
}

.metaCard {
  padding: 15px 16px;
  border-radius: var(--atlas-card-radius);
  background: var(--atlas-card-surface);
}

.metaLabel {
  font-size: 12px;
  color: var(--atlas-eyebrow);
}

.metaValue {
  font-size: 19px;
  font-weight: 600;
  font-family: var(--atlas-font-mono);
  margin-top: 2px;
}

.nextPanel {
  margin-top: 12px;
  padding: 16px;
  border-radius: var(--atlas-card-radius);
  background: var(--atlas-owner-bg);
}

.nextHeading {
  font: 600 11px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-owner-ink);
}

.nextText {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--atlas-next-text);
}
```

## `apps/atlas/src/shell/NowTab.test.tsx` (new)

```typescript
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NowTab } from "./NowTab";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";

afterEach(cleanup);

describe("NowTab", () => {
  it("renders the real hero card identity, headline, and subline, all from one derived state object", () => {
    const { container } = render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    // Scoped to the hero card: the reused OwnerDecisionCard below it also
    // renders "Terra" (its own real chain-of-escalation chip).
    const hero = container.querySelector('[class*="hero"]') as HTMLElement;
    expect(within(hero).getByText("Terra")).toBeInTheDocument();
    expect(within(hero).getByText("Implementor · A.2 Runtime Package")).toBeInTheDocument();
    // Hardcoded literals, not just cross-checked against the function's own
    // live return value — a wording regression inside
    // derivePacketHeaderState itself must still fail this test.
    expect(state.headline).toBe("Blocked");
    expect(state.subline).toBe("Escalated to you · worktree held");
    expect(within(hero).getByText(state.headline)).toBeInTheDocument();
    expect(within(hero).getByText(state.subline)).toBeInTheDocument();
  });

  it("renders the real 40% progress fill width, derived from the real fixture's plan steps", () => {
    const { container } = render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.progressPercent).toBe(40);
    const fill = container.querySelector('[class*="fill"]') as HTMLElement;
    expect(fill.style.width).toBe("40%");
  });

  it("renders the real boundary timestamps", () => {
    render(<NowTab />);
    expect(screen.getByText("began 13:51")).toBeInTheDocument();
    expect(screen.getByText("held at 14:52")).toBeInTheDocument();
  });

  it("renders the meta grid's Last report and Blocker, consistent with the derived state", () => {
    render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText("Last report")).toBeInTheDocument();
    expect(screen.getByText(state.lastReport)).toBeInTheDocument();
    expect(screen.getByText("Blocker")).toBeInTheDocument();
    expect(screen.getByText(state.blocker)).toBeInTheDocument();
  });

  it("renders the real owner-decision card (C4, reused verbatim) because this real trajectory is blocked", () => {
    render(<NowTab />);
    expect(
      screen.getByText(
        "Should a theme-free output get a sentinel version, or does the frozen contract change?",
      ),
    ).toBeInTheDocument();
  });

  it("renders the 'what happens next' panel with the real derived text", () => {
    render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    // Hardcoded literal, not just cross-checked against the function's own
    // live return value — a wording regression inside
    // derivePacketHeaderState itself must still fail this test.
    expect(state.nextPanelText).toBe(
      "Nothing is expected from Terra until you answer — its worktree stays held while the packet is blocked.",
    );
    expect(screen.getByText("what happens next")).toBeInTheDocument();
    expect(screen.getByText(state.nextPanelText)).toBeInTheDocument();
  });

  it("renders no Stop/Start or Open-conversation control (no real backend command exists for them yet)", () => {
    render(<NowTab />);
    expect(screen.queryByRole("button", { name: /stop/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /start/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /open conversation/i })).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<NowTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## `apps/atlas/src/shell/MobileShell.tsx` (modified — full new content)

```typescript
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { NowTab } from "./NowTab";
import styles from "./MobileShell.module.css";

export type MobileShellTab = "now" | "chat" | "plan" | "activity";

const TABS: ReadonlyArray<{ tab: MobileShellTab; label: string }> = [
  { tab: "now", label: "Now" },
  { tab: "chat", label: "Chat" },
  { tab: "plan", label: "Plan" },
  { tab: "activity", label: "Activity" },
];

/**
 * Every value here is either a direct property of the real, reviewed
 * `colors`/`fontFamily` tokens, or — where no token exists yet — a
 * literal with an inline comment naming its actual source (all five
 * non-token values here are from `Atlas Mobile.dc.html`, none
 * invented — corrected from an earlier draft that left one,
 * `backdrop-filter: blur(12px)`, as a bare CSS literal instead of
 * routing it through this same disclosed mechanism). Matches the
 * pattern `DesktopShell.tsx` (B3) already established.
 */
const SHELL_VARS = {
  "--atlas-page-bg-mobile": colors.pageBgMobile,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-font-body": fontFamily.body,
  // Not tokens: the reference file's own tab-bar chrome
  // (Atlas Mobile.dc.html's bottom <nav>) — no equivalent values exist
  // in colors.ts.
  "--atlas-tab-bar-bg": "rgba(255,255,255,.92)",
  "--atlas-tab-bar-border": "#EAE5F0",
  "--atlas-tab-bar-blur": "blur(12px)",
  // Reference file: `const col = k => s.tab === k ? '#5B34E8' : '#9A90A6'`.
  // The selected color is the real `colors.accent` token; the inactive
  // color (#9A90A6) has no equivalent token, so it stays a disclosed
  // literal.
  "--atlas-tab-selected": colors.accent,
  "--atlas-tab-inactive": "#9A90A6",
} as CSSProperties;

const TAB_LABEL: Record<MobileShellTab, string> = {
  now: "Now",
  chat: "Chat",
  plan: "Plan",
  activity: "Activity",
};

export function MobileShell() {
  const [selected, setSelected] = useState<MobileShellTab>("now");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <main className={styles.content}>
        {selected === "now" ? <NowTab /> : `${TAB_LABEL[selected]} tab`}
      </main>
      <nav className={styles.tabBar} aria-label="Atlas tabs">
        {TABS.map((t) => (
          <button
            key={t.tab}
            type="button"
            className={`${styles.tab} ${selected === t.tab ? styles.tabSelected : ""}`}
            aria-current={selected === t.tab ? "true" : undefined}
            onClick={() => setSelected(t.tab)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

export default MobileShell;
```

## `apps/atlas/src/shell/MobileShell.test.tsx` (modified — full new content)

```typescript
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import MobileShell from "./MobileShell";

afterEach(cleanup);

describe("MobileShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, plus the disclosed reference-file literals", () => {
    const { container } = render(<MobileShell />);
    const root = container.firstChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-page-bg-mobile")).toBe(colors.pageBgMobile);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-tab-bar-bg")).toBe("rgba(255,255,255,.92)");
    expect(root.style.getPropertyValue("--atlas-tab-bar-border")).toBe("#EAE5F0");
    expect(root.style.getPropertyValue("--atlas-tab-bar-blur")).toBe("blur(12px)");
    expect(root.style.getPropertyValue("--atlas-tab-selected")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-tab-inactive")).toBe("#9A90A6");
  });

  it("renders exactly four tabs, in the reference file's actual order (not the README prose order)", () => {
    render(<MobileShell />);
    // Scoped to the tab bar itself: F1's real Now-tab content also
    // contains real buttons (the reused owner-decision options), so an
    // unscoped `getAllByRole("button")` now picks those up too.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    const tabs = within(nav).getAllByRole("button");
    expect(tabs.map((t) => t.textContent)).toEqual(["Now", "Chat", "Plan", "Activity"]);
  });

  it("defaults to Now selected, with only one tab marked current, rendering the real Now tab (F1) rather than the placeholder", () => {
    render(<MobileShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("tapping a tab makes it the sole selected tab and updates the content pane", () => {
    render(<MobileShell />);
    fireEvent.click(screen.getByRole("button", { name: "Activity" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Activity");
    expect(screen.getByText("Activity tab")).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<MobileShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## `apps/atlas/src/thread/PacketHeader.test.tsx` (modified — full new content)

```typescript
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

  it("(F1) derives a real 40% progress from PACKET_A2_ENTRIES' own real plan.steps (2 of 5 marked done), not the reference file's fabricated 41%", () => {
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    const planEntry = PACKET_A2_ENTRIES.find((entry) => entry.plan !== undefined);
    expect(planEntry?.plan?.steps.filter((step) => step.status === "done")).toHaveLength(2);
    expect(planEntry?.plan?.steps).toHaveLength(5);
    expect(state.progressPercent).toBe(40);
  });

  it("(F1) derives real boundary timestamps from the first and last real Terra (wk) entries", () => {
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.boundaryBegin).toBe("13:51");
    expect(state.boundaryHeld).toBe("14:52");
  });

  it("(F1) reports headline/subline/progress/boundaries/next-panel as unavailable for a synthetic non-escalated thread", () => {
    const synthetic: ThreadEntry[] = [
      { k: "co", who: "Coordinator", text: "Go.", time: "10:00" },
      { k: "wk", who: "Terra", text: "On it.", time: "10:05" },
    ];
    const state = derivePacketHeaderState(synthetic);
    expect(state.headline).toBe("unavailable");
    expect(state.subline).toBe("unavailable");
    expect(state.progressPercent).toBe("unavailable");
    expect(state.boundaryBegin).toBe("unavailable");
    expect(state.boundaryHeld).toBe("unavailable");
    expect(state.nextPanelText).toBe("unavailable");
    expect(state.nextPanelHeading).toBe("what happens next");
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

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (`/tmp/maestro-m2-f1`, branch `architecture/m2-f1`, base
`09545e6` — **corrected by targeted correction: an earlier draft of
this section cited `ed200d1`, a real commit but not an ancestor of
this branch (it landed on `origin/master` after this worktree was
already forked); an independent Decision Fidelity review found this
left the packet internally contradicting its own, correct, header
`Base:` line**) and run through the real frontend toolchain from
`apps/atlas` (`npm install`, then each script below), before this
packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean, zero errors.
- `npm run lint` (`eslint .`) — clean, zero warnings or errors.
- `npm test` (`vitest run`) — **19/19 test files, 140/140 tests
  passed** (zero regressions across the entire Atlas suite — every
  Wave A-E component's own tests included, not just the files this
  slice touches).
  - First full run surfaced two expected, self-caught failures from
    real content now existing where a placeholder used to be: (1)
    `NowTab.test.tsx`'s own first assertion found multiple "Terra"
    matches (the hero card's own name and the reused
    `OwnerDecisionCard`'s chain-of-custody chip) — fixed by scoping the
    query to the hero card with `within()`; (2)
    `MobileShell.test.tsx`'s pre-existing four-tabs test found 6
    buttons instead of 4 (the reused `OwnerDecisionCard`'s own 2 real
    option buttons) — fixed by scoping the query to the tab bar's own
    `<nav>`. Both are the correct, intended consequence of F1 replacing
    a placeholder with real interactive content, not defects. Re-run
    confirmed 140/140.
  - A second self-caught issue, found by auditing this slice's own
    `NowTab.tsx` doc comment against its actual `SHELL_VARS` object
    before dispatch: the comment claimed `colors.accentLight` was a
    real token match in use, but the draft never actually referenced
    it (the live dot and progress fill were still bare CSS hex
    literals despite each having a real token match —
    `colors.accentLight` and `colors.accentLiveDot` respectively), and
    three more real token matches (`colors.inkFaint`, `colors.inkMuted`,
    `colors.surface`) were similarly left as bare CSS literals instead
    of routed through the established CSS-custom-property convention.
    Fixed before this packet was finalized: every declared
    `--atlas-*` custom property is now consumed by exactly one CSS
    rule, and zero bare hex literals remain in `NowTab.module.css`
    (verified by grep, not by inspection alone).
- `npm run build` (`vite build`) — clean, `38 modules transformed`, no
  warnings.

**Targeted correction (found by an independent Decision Fidelity
review, fixed before merge):** four defects, all fixed together and
re-verified with the same toolchain run above (still 19/19 test files,
140/140 tests, clean typecheck/lint/build):

1. **Wrong progress-fill color.** The first draft's `--atlas-hero-fill`
   used `colors.accentLiveDot` (`#A78BFF`), described as "the mockup's
   real blocked-fill color." Checked directly against
   `Atlas Mobile.dc.html:687`:
   `barColor: sys === 'crashed' ? '#D08A83' : blocked || s.decided === 'amend' ? '#B7ADC1' : '#A78BFF'`
   — `#A78BFF` is that ternary's *non-blocked* branch; the real
   blocked-branch value is `#B7ADC1`. This directly contradicted this
   same packet's own Design rationale item 4 (use `AGENT_STYLE.wait`,
   not `run`, because Terra is genuinely idle here, not working) —
   applied correctly to the avatar but missed on the progress fill.
   Fixed: `#B7ADC1` is itself a real token, `colors.navTextInactive`
   (`colors.ts:16`), now used instead.
2. **Missed a real token match for the progress track's background.**
   `rgba(255,255,255,.13)` was disclosed as an unmatched literal, but
   it is an exact match for `colors.navActiveBg` (`colors.ts:18`) —
   missed because the audit checked hex colors, not `rgba()` strings,
   against every family. Fixed: now uses `colors.navActiveBg`.
3. **Stale base-commit citation in this section** (see the correction
   note above it).
4. **Tautological test coverage for three new fields.** `headline`,
   `subline`, and `nextPanelText` were only ever compared against
   `derivePacketHeaderState`'s own live return value in
   `NowTab.test.tsx` — a wording regression inside the function itself
   would have passed undetected (unlike `progressPercent`/
   `boundaryBegin`/`boundaryHeld`, which already had hardcoded literal
   assertions). Fixed: `NowTab.test.tsx` now asserts
   `state.headline === "Blocked"`, `state.subline === "Escalated to
   you · worktree held"`, and the exact `nextPanelText` string, in
   addition to the existing render assertions.

One further defect the review flagged was independently confirmed
**not** a real defect: `nextPanelHeading` returning the static
`"what happens next"` unconditionally (not gated behind `isBlocked`)
matches the pre-existing, unmodified precedent `eyebrow`/`title`
already established in this same function — a constant UI label is
never `"unavailable"`, only a derived fact is. No change made for
this item. Two further non-blocking notes (a CSS-variable-naming
coincidence between this component and the reused `OwnerDecisionCard`,
and the hero card's own drop-shadow not being itemized in the
disclosed-literal audit) were addressed in the doc comment above for
completeness, at zero cost, without consuming this slice's one
targeted correction on their own.

## M0-D12 bounded quality contract

1. **Protected outcome:** the mobile Atlas app's "Now" tab renders the
   one real packet trajectory this codebase has fixture data for
   (Terra blocked, escalated to the owner) — hero card, real 40%
   progress, real boundary timestamps, the real reused escalation
   decision, and a real "what happens next" panel — with zero backend
   change and zero regression to any of the 19 existing test files.
2. **Operating and threat model:** none — this is a pure frontend
   rendering slice with no network call, no command dispatch, no
   backend interaction of any kind. `OwnerDecisionCard`'s own options
   remain inert (no `onClick` wired), exactly matching C4's own already
   -reviewed scope.
3. **Explicit exclusions:** F2 (Chat tab), F3 (Activity tab), F4 (Plan
   tab); any Stop/Start or "Open conversation" control (no real backend
   command exists for them); the mockup's own "architect agent ruling"
   decision-card variant, "crash" card, and every non-blocked hero-card
   branch (`s.decided`/`s.running` toggle states) — none have real
   fixture backing; a pixel-exact visual match between
   `OwnerDecisionCard`'s desktop-sized padding and the mobile Now tab's
   own gutter (disclosed layout debt, Guards item 6).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every derived field is exercised by a direct
   unit test against `derivePacketHeaderState`, and every rendered
   surface is exercised by a React Testing Library render test; no
   browser-based visual verification was performed (tooling failure,
   already disclosed in this session for M2-E4, same root cause).
5. **Acceptance proof:** 19/19 test files, 140/140 tests passing
   (zero regressions), clean typecheck, clean lint, clean production
   build.
6. **Implementation boundary:** 4 modified files, 3 new files, all
   within `apps/atlas/src`; zero backend files; no new third-party
   dependency.
7. **Proportionality ceiling:** one extended shared state-derivation
   function, one new presentational component, one new CSS module, one
   wiring change in an already-real shell — no new fixture data
   invented, no new design tokens invented (every color is either a
   real token or an explicitly disclosed literal).
8. **Stop and escalation rule:** rendering any of the mockup's
   fictional/non-fixture-backed branches (the "architect agent ruling"
   variant, "crash" recovery, any `decided`/`running` toggle state), or
   wiring any button to a command, is explicitly out of scope — future
   slices' job (F2-F4, and any future real second scenario), not this
   one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F1-NOW-TAB-01` |
| `phase` | `PendingTargetedDecisionFidelityVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f1-now-tab.md"]` |
