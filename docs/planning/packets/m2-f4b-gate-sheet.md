# M2 Wave F — Gate bottom sheet, wired to the Plan tab's gate row — Candidate 01

**Slice ID:** `MB-SLICE-M2-F4B-GATE-SHEET-01`
**Status:** `Awaiting Decision Fidelity review`
**Base:** `ae1a090` (full: `ae1a090b54090f02cc7b0740409f4b90daef7cbd`, `origin/master`)

## Scope, deliberately minimal

Completes roadmap item 36, *"F4 — Plan tab: packet list + gate bottom
sheet (reuses E7 data)."* F4A already built the packet list; this
slice builds the gate row's own bottom sheet — **the app's first
bottom-sheet / modal-like overlay component** — and wires the
already-real, already-inert `PlanTab.tsx` gate row's `onClick` to open
it.

This slice is frontend-only — no backend file touched. It adds 3 new
files (`apps/atlas/src/gate/GateSheet.tsx`/`.module.css`/`.test.tsx`)
and modifies exactly 2 existing files
(`apps/atlas/src/shell/PlanTab.tsx`/`.test.tsx`). No fixture file is
modified — `GATE_CRITERIA` is read-only, reused verbatim from `./fixtures`
(the same real data `GateHeader`/`GateCriteriaList` already consume).

## Evidence

The real mobile mockup (`Atlas Mobile.dc.html:342-368`, this session's
own cached copy of the design-handoff reference, not checked into this
repository — the same sourcing every prior packet has already
disclosed) is the exact real markup for the gate sheet:

```
342: <sc-if value="{{ gateOpen }}" hint-placeholder-val="{{ false }}">
343: <div style="position:absolute;top:-58px;left:0;right:0;bottom:-14px;background:rgba(28,20,40,.44);display:flex;align-items:flex-end;z-index:30">
344:   <div style="width:100%;max-height:88%;display:flex;flex-direction:column;border-radius:26px 26px 0 0;background:#fff;animation:sheet .24s cubic-bezier(.32,.72,0,1)">
345:     <div style="flex:none;padding:14px 18px 12px">
346:       <div style="width:38px;height:4px;border-radius:999px;background:#E0DAE6;margin:0 auto 16px"></div>
347:       <div style="font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#8E8299">m1-b · milestone gate</div>
348:       <h2 style="margin:7px 0 0;font-family:'Bricolage Grotesque',sans-serif;font-size:21px;font-weight:600;letter-spacing:-.02em;line-height:1.2">Overlay and support surfaces</h2>
349:       <div style="display:flex;align-items:center;gap:7px;margin-top:6px;font-size:13px;font-weight:600;color:#8E8299"><span style="width:9px;height:9px;box-sizing:border-box;border-radius:50%;border:1.5px dashed #B9AFC4"></span>Closed · 2 of 5 criteria met, 1 partly</div>
350:     </div>
351:     <div style="flex:1;min-height:0;overflow:auto;padding:0 18px">
352:       <sc-for list="{{ gateCriteria }}" as="c" hint-placeholder-count="5">
353:       <div style="display:grid;grid-template-columns:18px minmax(0,1fr);gap:11px;padding:12px 0;border-top:1px solid #F3F0F6">
354:         <span style="margin-top:2px;width:15px;height:15px;box-sizing:border-box;border-radius:5px;background:{{ c.markBg }};border:{{ c.markBorder }}"></span>
355:         <div style="min-width:0">
356:           <div style="font-size:14.5px;font-weight:600;line-height:1.35;color:{{ c.titleColor }};text-wrap:pretty">{{ c.title }}</div>
357:           <div style="margin-top:2px;font-size:13px;line-height:1.5;color:#6C6376;text-wrap:pretty">{{ c.detail }}</div>
358:           <div style="margin-top:4px;font:500 11px 'IBM Plex Mono',monospace;color:{{ c.evColor }}">{{ c.evidence }}</div>
359:         </div>
360:       </div>
361:       </sc-for>
362:       <div style="padding:12px 0 4px;font-size:12.5px;line-height:1.55;color:#8E8299;text-wrap:pretty">The Architect agent opens the gate on its own once the criteria read true. You are only asked if opening would waive one.</div>
363:     </div>
364:     <div style="flex:none;padding:12px 18px 32px">
365:       <button style="width:100%;min-height:50px;border:0;border-radius:15px;background:#F1EEF6;color:#A79BB4;cursor:not-allowed;font-size:15px;font-weight:700">Open gate · blocked by 2 criteria</button>
366:       <button onClick="{{ closeGate }}" style="width:100%;min-height:50px;margin-top:9px;border:0;border-radius:15px;background:transparent;color:#5B34E8;cursor:pointer;font-size:15px;font-weight:600">Close</button>
367:     </div>
368:   </div>
369: </div>
370: </sc-if>
```

The mockup's own `openGate`/`gateOpen` wiring (its own `state`
handlers, elsewhere in the file) opens from the Plan tab's gate row
(`onClick="{{ openGate }}"`) — the exact row already merged, inert, in
`PlanTab.tsx`.

**Real, checked discrepancy — the real fixture wins, not the
mockup's own copy.** The mockup file's own JS carries a second,
slightly different copy of the 5 gate criteria (its own `GATE_CRITERIA`
array literal), with 4 real wording deltas from the already-vetted
`apps/atlas/src/gate/fixtures.ts` (e.g. "closed **with** locks
released" vs. the real fixture's "closed **by the Coordinator** with
locks released"; "**Every** decision carries a fidelity check" vs. the
real fixture's "**Every owner** decision carries a fidelity check").
This slice reuses the real, already-reviewed `GATE_CRITERIA` from
`./fixtures` exclusively — the same data `GateHeader`/`GateCriteriaList`
already consume — never the mockup's own separate, less-precise copy.

`radii.sheetPx` (`"26px 26px 0 0"`), `motion.sheet`
(`translateFromPercent: 100 -> translateToPercent: 0`, `durationS:
0.24`, `easing: "cubic-bezier(.32,.72,0,1)"`), and
`touchTargetPx.sheetButton` (`50`) — all previously declared but
unconsumed anywhere in `apps/atlas/src` (confirmed by grep) — are
exact real matches to this markup's own `border-radius`, `@keyframes
sheet`/`animation:sheet .24s cubic-bezier(.32,.72,0,1)`, and
`min-height:50px` button values respectively. This slice is their
first real consumer.

**Confirmed: no existing bottom-sheet, modal, dialog, or overlay
component exists anywhere in `apps/atlas/src`** (grepped for
`sheet|modal|dialog|overlay` and for `position:\s*fixed|backdrop|
z-index|role="dialog"|aria-modal|Escape|focus-trap` across every
`.tsx`/`.css` file — no hit beyond this slice's own new files and one
unrelated cosmetic `backdrop-filter` in `MobileShell.module.css`). This
is genuinely the first of its kind — see Design rationale below for
what accessibility baseline this slice originates, and what it
deliberately excludes.

## Design rationale

1. **A new `GateSheet` component, not `<GateHeader />` or
   `<GateCriteriaList />` mounted as-is.** Both already-merged
   components are full-width, desktop-styled standalone blocks (their
   own padding, their own card chrome) with no sheet-specific
   affordances (no backdrop, no handle, no dialog semantics, no
   close/escape behavior) — reusing either directly would require
   restructuring an already-reviewed component for a second, different
   context. Instead, `GateSheet` reuses the exact same **data**
   (`GATE_CRITERIA`) and the exact same **already-reviewed 3-state
   color derivation** `GateCriteriaList.tsx`'s own `MARK_CLASS`/
   `EVIDENCE_CLASS`/title-unmet logic already established, applied to
   fresh sheet-specific markup — matching this program's own
   established convention (F3/F3B/F3C/F3D: reuse fixture data + an
   already-derived mapping, write fresh surface-specific JSX/CSS,
   never mount the other surface's own component).
2. **Real-mechanism correction, reused verbatim, not re-derived.** The
   mockup's own footer note claims the fictional-persona, fully-
   autonomous "The Architect agent opens the gate on its own... no
   human step" — the same claim `GateHeader.tsx`'s own `approverNote`
   already found and corrected (no code anywhere in
   `services/maestro/maestro/*.py` implements autonomous gate-opening).
   `GateSheet.tsx`'s own `mechanismNote` restates `GateHeader.tsx`'s
   own already-corrected sentence verbatim — the same real fact,
   stated once — rather than performing a second, independent
   correction of the same underlying claim.
3. **A deliberately minimal, disclosed accessibility baseline, not a
   full focus trap.** With zero prior modal/dialog precedent anywhere
   in this codebase to match, this slice originates: real
   `role="dialog"`/`aria-modal="true"`/`aria-labelledby`; closing on
   Escape; closing on a backdrop click (not a click inside the sheet,
   via `stopPropagation`); moving focus to the sheet's own Close
   button on open; and returning focus to the gate row on close (via
   the `onClose` callback contract — `PlanTab.tsx` owns the trigger
   element and its own ref, since `GateSheet` has no way to know what
   opened it). **Disclosed, not silently omitted:** full keyboard
   focus-trapping (cycling Tab/Shift+Tab within the sheet rather than
   letting focus escape to page content behind the backdrop) is NOT
   implemented — a larger, separate concern than this first-of-its-kind
   slice's own proportional scope, and no reference implementation
   exists anywhere in this codebase to reuse.
4. **State stays local to `PlanTab.tsx`.** The gate sheet is the only
   stateful concern in an otherwise-stateless component, and no other
   component needs this state — lifting it to `MobileShell.tsx` would
   expand this slice's own footprint (and roadmap) with no present
   need.
5. **Real, disclosed literal, not a rounded token.** The disabled
   Open-gate button's own background (`#F1EEF6`) is a real, different
   value from `colors.neutralChip`'s `#F2EEF8` — one digit apart,
   checked directly, not treated as a typo of a close-looking token.

## Guards

1. This slice adds exactly 3 new files
   (`apps/atlas/src/gate/GateSheet.tsx`/`.module.css`/`.test.tsx`) and
   modifies exactly 2 existing files
   (`apps/atlas/src/shell/PlanTab.tsx`/`.test.tsx`) — no backend file,
   no fixture file, touched.
2. `apps/atlas/src/gate/fixtures.ts`, `GateHeader.tsx`,
   `GateCriteriaList.tsx`, and their own `.module.css`/`.test.tsx` are
   untouched (zero-diff) — `GATE_CRITERIA` is imported read-only.
3. Every packet row in `PlanTab.tsx` (`PacketRow`) remains a real,
   inert `<button>` with no `onClick` — only the gate row's own
   `onClick` is wired, matching this program's own "options rendered
   but inert until wired" convention for everything not yet real.
4. The sheet renders every one of the real `GATE_CRITERIA`'s 5 rows
   with its exact real title/detail/evidence text — no new fixture
   data invented, no fictional persona, no fictional agent capability
   claimed as real.
5. The disabled "Open gate" button stays genuinely disabled
   (`disabled` attribute) — no real gate-opening command exists to
   wire it to; this stays inert.

## `apps/atlas/src/gate/GateSheet.tsx` (new file)

```tsx
import { useEffect, useId, useRef, type CSSProperties } from "react";
import { colors, fontFamily, motion, radii } from "../tokens";
import { GATE_CRITERIA, type GateCriterion, type GateCriterionMet } from "./fixtures";
import styles from "./GateSheet.module.css";

const YES_COUNT = GATE_CRITERIA.filter((c) => c.met === "yes").length;
const PART_COUNT = GATE_CRITERIA.filter((c) => c.met === "part").length;
const NO_COUNT = GATE_CRITERIA.filter((c) => c.met === "no").length;
const TOTAL_COUNT = GATE_CRITERIA.length;

/**
 * Colors from `Atlas Mobile.dc.html`'s real gate-sheet markup (lines
 * 342-368), checked directly against `colors.ts`. Real token matches:
 * `colors.surface` (`#fff`, the sheet's own background),
 * `colors.inkMuted` (`#8E8299`, the breadcrumb, the state-line text,
 * and the mechanism note below the criteria — three separate real
 * elements sharing the same real token, not a coincidence), and
 * `colors.borderDashed[2]` (`#B9AFC4`, the state-line dot's own dashed
 * border — the same token `GateHeader.tsx`'s own state dot already
 * uses). The criteria rows themselves reuse `GateCriteriaList.tsx`'s
 * own already-reviewed 3-state derivation exactly (`colors.success`/
 * `colors.warning`/`"#CFC6D6"` for the mark, `colors.inkSecondary`/
 * `colors.ink` for the title, `colors.successText`/`colors.warningText`/
 * `colors.inkFaint` for the evidence) — not re-derived a third time.
 * `colors.inkSecondary` (`#6C6376`) is the detail line, matching
 * `GateCriteriaList.tsx`'s own `--atlas-gate-detail`. `colors.accent`
 * (`#5B34E8`) is the Close button's own real text color.
 *
 * Four literals have no token match, checked against every color
 * family in `colors.ts`: the backdrop (`rgba(28,20,40,.44)`), the drag
 * handle (`#E0DAE6`), the row divider (`#F3F0F6` — same real value
 * `ActivityTab.tsx`'s own `--atlas-ag-footer-border` already
 * discloses, reused here as the same real fact), and the disabled
 * button's own background (`#F1EEF6` — a real, different value from
 * `colors.neutralChip`'s `#F2EEF8`, one digit apart, not a typo of it,
 * checked directly — matching this program's own established
 * discipline of never rounding a close-but-different real hex to a
 * similar-looking token).
 *
 * **Real, disclosed fact, not a mismatch:** the mechanism note below
 * uses `colors.inkMuted` (`#8E8299`), a genuinely different real token
 * from `GateHeader.tsx`'s own `approverNote` (`colors.inkSecondary`,
 * `#6C6376`) — two different real elements in two different real
 * surfaces, checked directly against both reference files, not a
 * copy-paste slip.
 */
const SHELL_VARS = {
  "--atlas-sheet-backdrop": "rgba(28,20,40,.44)",
  "--atlas-sheet-surface": colors.surface,
  "--atlas-sheet-radius": radii.sheetPx,
  "--atlas-sheet-translate-from": `${motion.sheet.translateFromPercent}%`,
  "--atlas-sheet-translate-to": `${motion.sheet.translateToPercent}%`,
  "--atlas-sheet-duration": `${motion.sheet.durationS}s`,
  "--atlas-sheet-easing": motion.sheet.easing,
  "--atlas-sheet-handle": "#E0DAE6",
  "--atlas-sheet-breadcrumb": colors.inkMuted,
  "--atlas-sheet-title": colors.ink,
  "--atlas-sheet-state": colors.inkMuted,
  "--atlas-sheet-state-dot-border": colors.borderDashed[2],
  "--atlas-sheet-row-border": "#F3F0F6",
  "--atlas-sheet-mark-yes": colors.success,
  "--atlas-sheet-mark-part": colors.warning,
  "--atlas-sheet-mark-no-border": "#CFC6D6",
  "--atlas-sheet-title-unmet": colors.inkSecondary,
  "--atlas-sheet-title-default": colors.ink,
  "--atlas-sheet-detail": colors.inkSecondary,
  "--atlas-sheet-ev-yes": colors.successText,
  "--atlas-sheet-ev-part": colors.warningText,
  "--atlas-sheet-ev-no": colors.inkFaint,
  "--atlas-sheet-mechanism-note": colors.inkMuted,
  "--atlas-sheet-open-bg": "#F1EEF6",
  "--atlas-sheet-open-ink": colors.inkFaint,
  "--atlas-sheet-close-ink": colors.accent,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-font-display": fontFamily.display,
} as CSSProperties;

const MARK_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.markYes,
  part: styles.markPart,
  no: styles.markNo,
};

const TITLE_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.rowTitleDefault,
  part: styles.rowTitleDefault,
  no: styles.rowTitleUnmet,
};

const EVIDENCE_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.evidenceYes,
  part: styles.evidencePart,
  no: styles.evidenceNo,
};

function SheetCriterionRow({ criterion }: { criterion: GateCriterion }) {
  return (
    <div className={styles.criterionRow}>
      <span className={`${styles.mark} ${MARK_CLASS[criterion.met]}`} aria-hidden="true" />
      <div className={styles.body}>
        <div className={`${styles.rowTitle} ${TITLE_CLASS[criterion.met]}`}>{criterion.title}</div>
        <div className={styles.detail}>{criterion.detail}</div>
        <div className={`${styles.evidence} ${EVIDENCE_CLASS[criterion.met]}`}>{criterion.evidence}</div>
      </div>
    </div>
  );
}

/**
 * The app's first bottom sheet / modal-like overlay — no existing
 * dialog, modal, or focus-trap precedent exists anywhere in
 * `apps/atlas/src` to match (checked directly). This slice originates
 * a deliberately minimal accessibility baseline rather than a full
 * focus trap: real `role="dialog"`/`aria-modal="true"`/
 * `aria-labelledby`, closing on Escape, closing on a backdrop click
 * (not a click inside the sheet itself, via `stopPropagation`), moving
 * focus to the sheet's own Close button on open, and returning focus
 * to whichever element opened it on close (`PlanTab.tsx`'s own gate
 * row, via the `onClose` callback contract — the caller, not this
 * component, owns the trigger element and its own focus-return
 * responsibility, since this component has no reference to it).
 * **Disclosed, not silently omitted:** full keyboard focus-trapping
 * (cycling Tab/Shift+Tab within the sheet, rather than letting focus
 * escape to page content behind the backdrop) is NOT implemented here
 * — a larger, separate concern than this first-of-its-kind slice's own
 * proportional scope, and no reference implementation exists anywhere
 * in this codebase to reuse. A future slice's job, not this one's to
 * silently add.
 *
 * **Real-mechanism correction, reused verbatim, not re-derived.** The
 * real mobile mockup's own footer note claims *"The Architect agent
 * opens the gate on its own once the criteria read true... You are
 * only asked if opening would waive one"* — the same fictional-persona
 * and fully-autonomous-opening claim `GateHeader.tsx`'s own
 * `approverNote` already found and corrected (no code anywhere in
 * `services/maestro/maestro/*.py` implements an autonomous
 * milestone-gate-opening decision). This component's `mechanismNote`
 * restates `GateHeader.tsx`'s own already-corrected sentence verbatim
 * — the same real fact, stated once, matching this program's own
 * single-source-of-identity precedent (F3's `HISTORY_EMPTY_NOTE`
 * reuse, F2's C7 eyebrow/title reuse) — not a second, independent
 * correction of the same underlying claim. It is duplicated as a
 * literal, not imported, since `GateHeader.tsx` does not export it as
 * a constant and adding that export purely for a second consumer
 * would expand this wiring-adjacent slice's own scope beyond
 * proportional.
 */
export function GateSheet({ onClose }: { onClose: () => void }) {
  const titleId = useId();
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButtonRef.current?.focus();
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className={styles.backdrop} style={SHELL_VARS} onClick={onClose}>
      <div
        className={styles.sheet}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className={styles.headBlock}>
          <span className={styles.handle} aria-hidden="true" />
          <div className={styles.breadcrumb}>m1-b · milestone gate</div>
          <h2 id={titleId} className={styles.title}>
            Overlay and support surfaces
          </h2>
          <div className={styles.stateLine}>
            <span className={styles.stateDot} aria-hidden="true" />
            Closed · {YES_COUNT} of {TOTAL_COUNT} criteria met, {PART_COUNT} partly
          </div>
        </div>
        <div className={styles.body}>
          {GATE_CRITERIA.map((criterion) => (
            <SheetCriterionRow key={criterion.title} criterion={criterion} />
          ))}
          <div className={styles.mechanismNote}>
            No automated gate-opening exists in Maestro today — opening the gate remains a manual,
            owner-reviewed action. This becomes an automatic Coordinator decision once M4's own autonomous
            Architect loop exists.
          </div>
        </div>
        <div className={styles.footer}>
          <button type="button" className={styles.openButton} disabled>
            Open gate · blocked by {NO_COUNT} criteria
          </button>
          <button type="button" ref={closeButtonRef} className={styles.closeButton} onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default GateSheet;
```

## `apps/atlas/src/gate/GateSheet.module.css` (new file)

```css
.backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 30;
  display: flex;
  align-items: flex-end;
  background: var(--atlas-sheet-backdrop);
}

.sheet {
  width: 100%;
  max-height: 88%;
  display: flex;
  flex-direction: column;
  border-radius: var(--atlas-sheet-radius);
  background: var(--atlas-sheet-surface);
  animation: sheetRise var(--atlas-sheet-duration) var(--atlas-sheet-easing);
}

@keyframes sheetRise {
  from {
    transform: translateY(var(--atlas-sheet-translate-from));
  }
  to {
    transform: translateY(var(--atlas-sheet-translate-to));
  }
}

.headBlock {
  flex: none;
  padding: 14px 18px 12px;
}

.handle {
  display: block;
  width: 38px;
  height: 4px;
  margin: 0 auto 16px;
  border-radius: 999px;
  background: var(--atlas-sheet-handle);
}

.breadcrumb {
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-sheet-breadcrumb);
}

.title {
  margin: 7px 0 0;
  font-family: var(--atlas-font-display);
  font-size: 21px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--atlas-sheet-title);
}

.stateLine {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--atlas-sheet-state);
}

.stateDot {
  width: 9px;
  height: 9px;
  box-sizing: border-box;
  border-radius: 50%;
  border: 1.5px dashed var(--atlas-sheet-state-dot-border);
}

.body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0 18px;
}

.criterionRow {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 11px;
  padding: 12px 0;
  border-top: 1px solid var(--atlas-sheet-row-border);
}

.mark {
  margin-top: 2px;
  width: 15px;
  height: 15px;
  box-sizing: border-box;
  border-radius: 5px;
}

.markYes {
  background: var(--atlas-sheet-mark-yes);
  border: 0;
}

.markPart {
  background: var(--atlas-sheet-mark-part);
  border: 0;
}

.markNo {
  background: transparent;
  border: 1.5px solid var(--atlas-sheet-mark-no-border);
}

.rowTitle {
  font-size: 14.5px;
  font-weight: 600;
  line-height: 1.35;
  text-wrap: pretty;
}

.rowTitleUnmet {
  color: var(--atlas-sheet-title-unmet);
}

.rowTitleDefault {
  color: var(--atlas-sheet-title-default);
}

.detail {
  margin-top: 2px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--atlas-sheet-detail);
}

.evidence {
  margin-top: 4px;
  font: 500 11px var(--atlas-font-mono);
}

.evidenceYes {
  color: var(--atlas-sheet-ev-yes);
}

.evidencePart {
  color: var(--atlas-sheet-ev-part);
}

.evidenceNo {
  color: var(--atlas-sheet-ev-no);
}

.mechanismNote {
  padding: 12px 0 4px;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--atlas-sheet-mechanism-note);
  text-wrap: pretty;
}

.footer {
  flex: none;
  padding: 12px 18px 32px;
}

.openButton {
  width: 100%;
  min-height: 50px;
  border: 0;
  border-radius: 15px;
  background: var(--atlas-sheet-open-bg);
  color: var(--atlas-sheet-open-ink);
  cursor: not-allowed;
  font-size: 15px;
  font-weight: 700;
}

.closeButton {
  width: 100%;
  min-height: 50px;
  margin-top: 9px;
  border: 0;
  border-radius: 15px;
  background: transparent;
  color: var(--atlas-sheet-close-ink);
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
}
```

## `apps/atlas/src/gate/GateSheet.test.tsx` (new file)

```tsx
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { GateSheet } from "./GateSheet";
import { GATE_CRITERIA } from "./fixtures";

afterEach(cleanup);

describe("GateSheet", () => {
  it("renders as a real dialog, labelled by its own real title", () => {
    render(<GateSheet onClose={() => {}} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    const heading = screen.getByRole("heading", { name: "Overlay and support surfaces" });
    expect(dialog).toHaveAttribute("aria-labelledby", heading.id);
  });

  it("renders the real breadcrumb and a real, derived state line", () => {
    const yesCount = GATE_CRITERIA.filter((c) => c.met === "yes").length;
    const partCount = GATE_CRITERIA.filter((c) => c.met === "part").length;
    render(<GateSheet onClose={() => {}} />);
    expect(screen.getByText("m1-b · milestone gate")).toBeInTheDocument();
    expect(
      screen.getByText(`Closed · ${yesCount} of ${GATE_CRITERIA.length} criteria met, ${partCount} partly`),
    ).toBeInTheDocument();
  });

  it("renders every real GATE_CRITERIA row with its exact title, detail, and evidence", () => {
    render(<GateSheet onClose={() => {}} />);
    for (const criterion of GATE_CRITERIA) {
      expect(screen.getByText(criterion.title)).toBeInTheDocument();
      expect(screen.getByText(criterion.detail)).toBeInTheDocument();
      expect(screen.getByText(criterion.evidence)).toBeInTheDocument();
    }
  });

  it("colors each real row's mark/title/evidence by its exact real 'met' state", () => {
    render(<GateSheet onClose={() => {}} />);
    for (const criterion of GATE_CRITERIA) {
      const title = screen.getByText(criterion.title);
      expect(title.className).toContain(criterion.met === "no" ? "rowTitleUnmet" : "rowTitleDefault");

      const row = title.closest('[class*="criterionRow"]') as HTMLElement;
      const mark = row.querySelector('[class*="mark"]') as HTMLElement;
      expect(mark.className).toContain(
        criterion.met === "yes" ? "markYes" : criterion.met === "part" ? "markPart" : "markNo",
      );

      const evidence = screen.getByText(criterion.evidence);
      expect(evidence.className).toContain(
        criterion.met === "yes" ? "evidenceYes" : criterion.met === "part" ? "evidencePart" : "evidenceNo",
      );
    }
  });

  it("renders the real, derived 'blocked by N criteria' disabled Open-gate button", () => {
    const noCount = GATE_CRITERIA.filter((c) => c.met === "no").length;
    render(<GateSheet onClose={() => {}} />);
    const openButton = screen.getByRole("button", { name: `Open gate · blocked by ${noCount} criteria` });
    expect(openButton).toBeDisabled();
  });

  it("renders the corrected, real-mechanism note — no fictional autonomous-opening claim", () => {
    render(<GateSheet onClose={() => {}} />);
    expect(
      screen.getByText(
        "No automated gate-opening exists in Maestro today — opening the gate remains a manual, owner-reviewed action. This becomes an automatic Coordinator decision once M4's own autonomous Architect loop exists.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent opens the gate on its own/)).toBeNull();
  });

  it("moves focus to its own Close button on mount", () => {
    render(<GateSheet onClose={() => {}} />);
    expect(screen.getByRole("button", { name: "Close" })).toHaveFocus();
  });

  it("calls onClose when the Close button is clicked", () => {
    const onClose = vi.fn();
    render(<GateSheet onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the backdrop is clicked, but not when the sheet itself is clicked", () => {
    const onClose = vi.fn();
    const { container } = render(<GateSheet onClose={onClose} />);
    const dialog = screen.getByRole("dialog");
    fireEvent.click(dialog);
    expect(onClose).not.toHaveBeenCalled();

    const backdrop = container.firstElementChild as HTMLElement;
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose on Escape", () => {
    const onClose = vi.fn();
    render(<GateSheet onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not call onClose on a non-Escape key", () => {
    const onClose = vi.fn();
    render(<GateSheet onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Enter" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("removes its own document keydown listener on unmount", () => {
    const onClose = vi.fn();
    const { unmount } = render(<GateSheet onClose={onClose} />);
    unmount();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("renders no image, icon font, or <svg> element", () => {
    render(<GateSheet onClose={() => {}} />);
    expect(document.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## `apps/atlas/src/shell/PlanTab.tsx` (modified — full new content)

```tsx
import { useRef, useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { GATE_CRITERIA } from "../gate/fixtures";
import { GateSheet } from "../gate/GateSheet";
import {
  PLAN_ACTIVE_PACKET_ID,
  PLAN_BREADCRUMB,
  PLAN_PACKETS,
  PLAN_STATE_LABEL,
  type PlanPacket,
  type PlanPacketState,
} from "../plan/fixtures";
import styles from "./PlanTab.module.css";

const DONE_COUNT = PLAN_PACKETS.filter((p) => p.state === "done").length;
const RUN_COUNT = PLAN_PACKETS.filter((p) => p.state === "run").length;
const AHEAD_COUNT = PLAN_PACKETS.length - DONE_COUNT - RUN_COUNT;
const GATE_MET_COUNT = GATE_CRITERIA.filter((c) => c.met === "yes").length;

/**
 * Transcribed verbatim from `Atlas Mobile.dc.html`'s own real `dot()`
 * function (lines 550-556) and `track` derivation (line 735) — every
 * real per-state size/shape/color, checked directly against
 * `colors.ts`. `done`'s bg (`#2E9B72`) and `run`'s bg (`#8C6BFF`) are
 * `colors.success`/`colors.accentLight`; `wait`'s and `pend`'s own
 * border (`#B9AFC4`) is `colors.borderDashed[2]`, the same token
 * `--atlas-ag-wait-dot-border` already uses. `block`'s own border
 * (`#D08A83`) and the track's own "not done/running" segment color
 * (`#E4DEEC`) have no token match, checked against every color family
 * in `colors.ts` — both disclosed literals. `run`'s own halo
 * (`rgba(140,107,255,.2)`, `colors.accentLight`'s RGB at .2 alpha) is
 * a real, exact RGB-to-token match, following the same *pattern*
 * (an alpha-halo derived from a real token's own RGB) `--atlas-dot-need-halo`
 * already establishes — not the same value (that one is an amber
 * warning halo, not this purple one).
 */
const TRACK_COLOR: Record<PlanPacketState, string> = {
  done: colors.success,
  run: colors.accentLight,
  wait: "#E4DEEC",
  block: "#E4DEEC",
  pend: "#E4DEEC",
};

/**
 * Every real per-state dot is the same real 10px size (the reference
 * file's own `this.dot(p.state, 10)` call) — only shape/color vary,
 * so the shared 10px/box-sizing/`flex: none` sizing lives once in
 * `.packetDot`'s own static CSS rule, matching `AgentCardMobile`'s own
 * already-established convention (static class for shared shape, inline
 * style only for the per-state-varying properties).
 */
const DOT_STYLE: Record<PlanPacketState, CSSProperties> = {
  done: { borderRadius: 3, background: colors.success },
  run: {
    borderRadius: "50%",
    background: colors.accentLight,
    boxShadow: "0 0 0 4px rgba(140,107,255,.2)",
  },
  wait: { borderRadius: "50%", border: `2px solid ${colors.borderDashed[2]}` },
  block: { borderRadius: "50%", border: "2px solid #D08A83" },
  pend: { borderRadius: "50%", border: `1.5px dashed ${colors.borderDashed[2]}` },
};

/**
 * Colors from `Atlas Mobile.dc.html`'s real Plan-tab markup (lines
 * 200-217), checked directly against `colors.ts`. Real token matches:
 * `colors.inkMuted` (`#8E8299`, breadcrumb and the gate row's own
 * inherited "N of 5 met" text), `colors.inkSecondary` (`#6C6376`, the
 * stats line), `colors.surface` (`#fff`, a packet row's own default
 * background), `colors.ink` (`#221C29`, every row's own title text,
 * real regardless of active state — the reference file's own `p.color`
 * is always `#221C29`, never variable), `colors.borderDashed[0]`
 * (`#DCD5E4`, the gate row's own dashed border), `colors.borderDashed[2]`
 * (`#B9AFC4`, the gate row's own dot border — the same token the
 * packet dots' own `wait`/`pend` states already use). Three literals
 * have no token match, checked against every color family in
 * `colors.ts`: the active row's own background (`#EFEAFE`) and its own
 * id/state/chevron text color (`#6C55B8`), and the gate row's own
 * "M1-B gate" label color (`#4C4457` — the same disclosed literal
 * F3C's own weekly-window body text already establishes, reused here
 * as the same real value, not a new one).
 */
const SHELL_VARS = {
  "--atlas-plan-breadcrumb": colors.inkMuted,
  "--atlas-plan-stats": colors.inkSecondary,
  "--atlas-plan-row-bg": colors.surface,
  "--atlas-plan-row-bg-active": "#EFEAFE",
  "--atlas-plan-row-ink": colors.ink,
  "--atlas-plan-row-meta": colors.inkMuted,
  "--atlas-plan-row-meta-active": "#6C55B8",
  "--atlas-plan-gate-border": colors.borderDashed[0],
  "--atlas-plan-gate-dot-border": colors.borderDashed[2],
  "--atlas-plan-gate-meta": colors.inkMuted,
  "--atlas-plan-gate-label": "#4C4457",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

function PacketRow({ packet }: { packet: PlanPacket }) {
  const isActive = packet.id === PLAN_ACTIVE_PACKET_ID;
  const activeClass = isActive ? styles.packetMetaActive : "";
  return (
    <button type="button" className={`${styles.packetRow} ${isActive ? styles.packetRowActive : ""}`}>
      <span className={styles.packetDot} style={DOT_STYLE[packet.state]} aria-hidden="true" />
      <span className={styles.packetBody}>
        <span className={`${styles.packetId} ${activeClass}`}>{packet.id}</span>
        <span className={styles.packetShort}>{packet.short}</span>
        <span className={`${styles.packetState} ${activeClass}`}>{PLAN_STATE_LABEL[packet.state]}</span>
      </span>
      <span className={`${styles.chevron} ${activeClass}`} aria-hidden="true">
        ›
      </span>
    </button>
  );
}

/**
 * Mobile "Plan" tab — the reference file's own `isPlan` view: a
 * breadcrumb, a real derived stats line ("N complete · N running · N
 * ahead"), a real progress track, and all 8 real `PLAN_PACKETS` rows
 * (each a real, tappable `<button>` matching the reference file's own
 * per-state dot styling — no `onClick` wired, since no real
 * multi-packet "open this packet's thread" capability exists yet; only
 * A.2 has any real conversation data), plus a real "M1-B gate" row
 * with its own real derived "N of 5 met" count (reusing E7's own
 * `GATE_CRITERIA`). The gate row's own `onClick` opens the real
 * `GateSheet` bottom sheet (F4B, completing roadmap item 36) — the
 * only row in this tab wired to a real capability; every `PacketRow`
 * remains a real, inert `<button>` (no `onClick`), matching this
 * program's own established "options rendered but inert until wired"
 * convention (`AgentsRoster`'s own "Open thread" button), since no real
 * multi-packet "open this packet's thread" capability exists yet.
 *
 * The stats line's own real counts (`DONE_COUNT`/`RUN_COUNT`/
 * `AHEAD_COUNT`) are derived directly from `PLAN_PACKETS`'s own `state`
 * field, not separately hand-typed numbers — matching this program's
 * own C7/`GateHeader` single-state-source discipline. `AHEAD_COUNT`
 * is `PLAN_PACKETS.length` minus the other two, not its own filter, so
 * the three real counts can never silently fail to sum to the real
 * total.
 *
 * **F4B, this slice:** the gate row's own `onClick` is now wired to
 * open the real `GateSheet` (the app's first bottom-sheet component) —
 * the "options rendered but inert until wired" note above is resolved
 * for this one row. `gateOpen` is local `useState` (this component has
 * no other stateful concern to share it with); `gateRowRef` gives
 * `GateSheet`'s own `onClose` callback something real to return focus
 * to on close, matching a baseline dialog-accessibility convention
 * with no prior precedent in this codebase to instead match (see
 * `GateSheet.tsx`'s own doc comment for what is, and is not, in this
 * slice's scope).
 */
export function PlanTab() {
  const [gateOpen, setGateOpen] = useState(false);
  const gateRowRef = useRef<HTMLButtonElement>(null);

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.breadcrumb}>{PLAN_BREADCRUMB}</div>
      <h1 className={styles.pageTitle}>Plan</h1>
      <div className={styles.stats}>
        {DONE_COUNT} complete · {RUN_COUNT} running · {AHEAD_COUNT} ahead
      </div>
      <div className={styles.track}>
        {PLAN_PACKETS.map((p) => (
          <span key={p.id} className={styles.trackSegment} style={{ background: TRACK_COLOR[p.state] }} />
        ))}
      </div>
      <div className={styles.packetList}>
        {PLAN_PACKETS.map((p) => (
          <PacketRow key={p.id} packet={p} />
        ))}
      </div>
      <button
        type="button"
        ref={gateRowRef}
        className={styles.gateRow}
        onClick={() => setGateOpen(true)}
      >
        <span className={styles.gateDot} aria-hidden="true" />
        <span className={styles.gateLabel}>M1-B gate</span>
        <span className={styles.gateMeta}>
          {GATE_MET_COUNT} of {GATE_CRITERIA.length} met ›
        </span>
      </button>
      {gateOpen && (
        <GateSheet
          onClose={() => {
            setGateOpen(false);
            gateRowRef.current?.focus();
          }}
        />
      )}
    </div>
  );
}

export default PlanTab;
```

## `apps/atlas/src/shell/PlanTab.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PlanTab } from "./PlanTab";
import { GATE_CRITERIA } from "../gate/fixtures";
import { PLAN_BREADCRUMB, PLAN_PACKETS, PLAN_STATE_LABEL } from "../plan/fixtures";

afterEach(cleanup);

/**
 * jsdom (like real browsers) silently re-serializes a raw inline hex
 * color to `rgb(...)` when read back via `.style.*` — so an
 * exact-string comparison against the original hex literal must
 * convert through the same normalization first, matching the
 * discipline `connectionState.ts` (G1) and F3C's own implementation
 * review already established for exactly this defect class.
 */
function hexToRgb(hex: string): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

describe("PlanTab", () => {
  it("renders the real breadcrumb and title", () => {
    render(<PlanTab />);
    expect(screen.getByText(PLAN_BREADCRUMB)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Plan" })).toBeInTheDocument();
  });

  it("derives the stats line directly from the real PLAN_PACKETS states, summing to the real total", () => {
    const counts = { done: 0, run: 0, wait: 0, block: 0, pend: 0 };
    for (const p of PLAN_PACKETS) {
      counts[p.state] += 1;
    }
    const ahead = counts.wait + counts.block + counts.pend;
    expect(counts.done + counts.run + ahead).toBe(PLAN_PACKETS.length);

    render(<PlanTab />);
    expect(screen.getByText(`${counts.done} complete · ${counts.run} running · ${ahead} ahead`)).toBeInTheDocument();
  });

  it("renders all 8 real PLAN_PACKETS rows with their exact id, short title, and state label", () => {
    render(<PlanTab />);
    for (const packet of PLAN_PACKETS) {
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      expect(within(row).getByText(packet.short)).toBeInTheDocument();
      expect(within(row).getByText(PLAN_STATE_LABEL[packet.state])).toBeInTheDocument();
    }
  });

  it("renders exactly 8 real packet rows, each a real <button>", () => {
    render(<PlanTab />);
    const rows = screen.getAllByRole("button").filter((b) => b.className.includes("packetRow"));
    expect(rows).toHaveLength(8);
  });

  it("highlights only A.2's own row as active (the only packet with any real conversation data)", () => {
    render(<PlanTab />);
    const activeId = screen.getByText("A.2");
    const activeRow = activeId.closest('[class*="packetRow"]') as HTMLElement;
    expect(activeRow.className).toContain("packetRowActive");

    for (const packet of PLAN_PACKETS) {
      if (packet.id === "A.2") continue;
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      expect(row.className).not.toContain("packetRowActive");
    }
  });

  it("renders each real packet's own exact per-state dot color/shape (not just non-empty)", () => {
    render(<PlanTab />);
    for (const packet of PLAN_PACKETS) {
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      const dot = row.querySelector('[class*="packetDot"]') as HTMLElement;
      if (packet.state === "done") {
        expect(dot.style.borderRadius).toBe("3px");
        expect(dot.style.background).toBe(hexToRgb(colors.success));
      } else if (packet.state === "run") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.background).toBe(hexToRgb(colors.accentLight));
        expect(dot.style.boxShadow).toBe("0 0 0 4px rgba(140,107,255,.2)");
      } else if (packet.state === "block") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`2px solid ${hexToRgb("#D08A83")}`);
      } else if (packet.state === "wait") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`2px solid ${hexToRgb(colors.borderDashed[2])}`);
      } else {
        // pend
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`1.5px dashed ${hexToRgb(colors.borderDashed[2])}`);
      }
    }
  });

  it("renders each real packet's own exact track-segment color, matching the mockup's own done/run/other derivation", () => {
    render(<PlanTab />);
    const track = document.querySelector('[class*="track"]') as HTMLElement;
    const segments = track.querySelectorAll('[class*="trackSegment"]');
    expect(segments).toHaveLength(PLAN_PACKETS.length);
    segments.forEach((segment, index) => {
      const state = PLAN_PACKETS[index].state;
      const background = (segment as HTMLElement).style.background;
      if (state === "done") {
        expect(background).toBe(hexToRgb(colors.success));
      } else if (state === "run") {
        // The real mockup's own track derivation uses the identical
        // #8C6BFF for both the run dot and the run track segment —
        // this must be the SAME real token as the dot's own run color,
        // not colors.accent (a different, darker real token this
        // slice's own first draft mistakenly used here).
        expect(background).toBe(hexToRgb(colors.accentLight));
      } else {
        expect(background).toBe(hexToRgb("#E4DEEC"));
      }
    });
  });

  it("renders no onClick navigation on any packet row (no real multi-packet thread capability exists yet)", () => {
    render(<PlanTab />);
    // A real <button> with no onClick still fires no visible state
    // change; this is a documentation-style assertion that the rows
    // are inert by construction, not wired to fake navigation.
    const rows = screen.getAllByRole("button").filter((b) => b.className.includes("packetRow"));
    expect(rows).toHaveLength(PLAN_PACKETS.length);
  });

  it("renders the real 'M1-B gate' row with its own real derived met-count, reusing E7's GATE_CRITERIA", () => {
    const yesCount = GATE_CRITERIA.filter((c) => c.met === "yes").length;
    render(<PlanTab />);
    expect(screen.getByText("M1-B gate")).toBeInTheDocument();
    expect(screen.getByText(`${yesCount} of ${GATE_CRITERIA.length} met ›`)).toBeInTheDocument();
    const gateButton = screen.getByRole("button", { name: /M1-B gate/ });
    expect(gateButton).not.toBeDisabled();
  });

  it("(F4B) clicking the gate row opens the real GateSheet, unlike the still-inert packet rows", () => {
    render(<PlanTab />);
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /M1-B gate/ }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
  });

  it("(F4B) closing the sheet (via its own Close button) returns focus to the gate row", () => {
    render(<PlanTab />);
    const gateButton = screen.getByRole("button", { name: /M1-B gate/ });
    fireEvent.click(gateButton);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(gateButton).toHaveFocus();
  });

  it("sets the real, checked B2 tokens and the disclosed literals", () => {
    expect(colors.inkMuted).toBe("#8E8299");
    expect(colors.inkSecondary).toBe("#6C6376");
    expect(colors.surface).toBe("#FFFFFF");
    expect(colors.ink).toBe("#221C29");
    expect(colors.borderDashed[0]).toBe("#DCD5E4");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");

    const { container } = render(<PlanTab />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-plan-breadcrumb")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-plan-stats")).toBe(colors.inkSecondary);
    expect(root.style.getPropertyValue("--atlas-plan-row-bg")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-plan-row-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-plan-gate-border")).toBe(colors.borderDashed[0]);
    expect(root.style.getPropertyValue("--atlas-plan-gate-dot-border")).toBe(colors.borderDashed[2]);
    // Disclosed literals, no real token match.
    expect(root.style.getPropertyValue("--atlas-plan-row-bg-active")).toBe("#EFEAFE");
    expect(root.style.getPropertyValue("--atlas-plan-row-meta-active")).toBe("#6C55B8");
    expect(root.style.getPropertyValue("--atlas-plan-gate-label")).toBe("#4C4457");
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PlanTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (branch `architecture/m2-f4b-gate-sheet`, base `ae1a090`) and
run through the real frontend toolchain from `apps/atlas` (`npm
install`, then each script below) before this packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **25/25 test files, 211/211 tests
  passed** (`GateSheet.test.tsx`: 13 new tests; `PlanTab.test.tsx`: 13,
  up from 11; zero regressions in the other 23 files, including
  `GateHeader.test.tsx` and `GateCriteriaList.test.tsx`, neither of
  which this slice modifies). Note: `ActivityTab.test.tsx` shows 16
  tests in this count, not F3D's own 21 — F3D's planning packet is
  merged but its own implementation PR had not yet merged into
  `master` at this packet's own verification time; unrelated to this
  slice.
- `npm run build` (`vite build`) — clean, `45 modules transformed`, no
  warnings.
- Every declared `--atlas-sheet-*`/`--atlas-plan-*` custom property,
  and every CSS class declared in `GateSheet.module.css`, was
  cross-checked programmatically against `GateSheet.tsx`'s own
  references — zero orphans in either direction (checked separately
  for `PlanTab.tsx`/`.module.css` too — also zero).

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** the Plan tab's gate row opens a real,
   accessible bottom sheet showing all 5 real `GATE_CRITERIA` rows,
   the real derived state line, and the real, corrected mechanism
   note — the app's first bottom-sheet component — completing roadmap
   item 36 (F4), with zero backend change and zero regression to any
   of the 23 other existing test files.
2. **Operating and threat model:** none — pure frontend rendering of
   already-real, already-reviewed fixture data behind a client-only
   overlay; no network call, no command dispatch.
3. **Explicit exclusions:** full keyboard focus-trapping within the
   sheet (Design rationale #3); wiring the disabled "Open gate" button
   to any real command (no such command exists); modifying
   `GateHeader.tsx`/`GateCriteriaList.tsx`/`gate/fixtures.ts`
   themselves (all read-only or untouched).
4. **Assurance level:** practical correctness for a fixture-driven
   dialog component — every rendered surface, every color-class
   mapping, and the dialog's open/close/focus-management behavior
   (Escape, backdrop click, Close button, focus-on-open, focus-return-
   on-close) are exercised by a React Testing Library render/interaction
   test; no browser-based visual verification was performed (tooling
   limitation already disclosed for every prior M2 slice this
   session); the mockup source is this session's own cached copy, not
   part of this repository, also already-disclosed sourcing.
5. **Acceptance proof:** 25/25 test files, 211/211 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 3 new files (all within
   `apps/atlas/src/gate`) and 2 modified files (within
   `apps/atlas/src/shell`); zero backend files; no new third-party
   dependency; `apps/atlas/src/gate/fixtures.ts`,
   `GateHeader.tsx`/`.module.css`/`.test.tsx`,
   `GateCriteriaList.tsx`/`.module.css`/`.test.tsx` all read-only or
   untouched.
7. **Proportionality ceiling:** one new component and its own CSS/
   test file, reusing an already-real fixture and an already-reviewed
   color mapping verbatim, plus a 2-line wiring change (`onClick` +
   conditional render) in an already-merged component — no new fixture
   data invented, no focus-trap machinery built beyond the disclosed
   minimal baseline.
8. **Stop and escalation rule:** implementing full focus-trapping, or
   wiring the disabled "Open gate" button to a real command once one
   exists, is explicitly out of scope — a future slice's job, not this
   one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F4B-GATE-SHEET-01` |
| `phase` | `AwaitingReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f4b-gate-sheet.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
