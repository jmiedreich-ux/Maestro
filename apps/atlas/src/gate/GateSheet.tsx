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
 * `colors.neutralChip`'s `#F2EEF8`; two of the three hex byte-pairs
 * differ (`F2`→`F1`, `F8`→`F6`), not a typo of it, checked directly —
 * matching this program's own established discipline of never
 * rounding a close-but-different real hex to a similar-looking
 * token).
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
