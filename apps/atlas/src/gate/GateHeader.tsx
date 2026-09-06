import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { AGENT_STYLE } from "../agents/agentStyle";
import { GATE_CRITERIA } from "./fixtures";
import styles from "./GateHeader.module.css";

const YES_COUNT = GATE_CRITERIA.filter((c) => c.met === "yes").length;
const PART_COUNT = GATE_CRITERIA.filter((c) => c.met === "part").length;
const NO_COUNT = GATE_CRITERIA.filter((c) => c.met === "no").length;
const TOTAL_COUNT = GATE_CRITERIA.length;

/**
 * Real, verbatim from `Atlas Explorations.dc.html`'s own `gate.releases`
 * array — pure reporting content about M1-B/M1-A structure, no persona.
 */
const RELEASES = [
  "B.0 through B.4 become dispatchable",
  "Overlay files unlock for write",
  "M1-A packets become read-only records",
];

/**
 * Colors from `Atlas Explorations.dc.html`'s real gate-header markup
 * (lines 214-266), checked directly against `colors.ts`. Real token
 * matches: `colors.inkFaint` (`#A79BB4`, breadcrumb/button-note/role
 * text), `colors.borderDashed[2]` (`#B9AFC4`, both the state-line dot's
 * own dashed border and the releases-panel bullet dots — the same
 * token this program's own `--atlas-ag-wait-dot-border` already uses),
 * `colors.inkMuted` (`#8E8299`, the state-line text and panel-label
 * text), `colors.border` (`#E7E1EE`, both the disabled button's own
 * border and each panel's own border), `colors.inkSecondary`
 * (`#6C6376`, the lede and approver-note body text). Two literals have
 * no token match, checked against every color family in `colors.ts`:
 * the breadcrumb's own separator dot (`#CFC6D6` — the same value
 * `GateCriteriaList.tsx`'s own `--atlas-gate-mark-no-border` already
 * discloses as coincidentally equal to `colors.navText` but not scoped
 * for general reuse, so re-disclosed here rather than imported as a
 * token), and the disabled button's own background (`#F6F4F9`).
 *
 * **Real persona substitution, matching Wave C's own established
 * pattern (C3/C4) and E4's own already-reviewed precedent.** The
 * reference file's own approver panel names the fictional M4-only
 * "Architect agent" persona (avatar initials "AR", violet badge). This
 * component substitutes the real Coordinator actor instead — same
 * avatar-color pairing E4's own `AGENTS`/`AGENT_STYLE` already
 * established for the Coordinator (`AGENT_STYLE.rule.avBg`/`.avColor`,
 * exactly `colors.accentWash[1]`/`colors.accentDeepest` — a real,
 * already-reviewed match to the reference file's own literal "AR"
 * badge colors, not a coincidence invented here), avatar initials
 * "CO" (matching `AGENTS`'s own real Coordinator entry), and the lede
 * paragraph above the criteria card corrected from "the Architect
 * agent verifies them against records" to "the Coordinator verifies
 * them against records" — the same real, sound claim (M1's own
 * Coordinator role already does exactly this kind of record-based
 * verification, per this session's own D2/D6 findings), the real
 * actor's name. **Corrected — non-blocking finding from Decision
 * Fidelity review:** a second, undisclosed wording change also shipped
 * in the first draft — the reference file's own lede reads "Every
 * criterion **below** has to be true," and "below" was silently
 * dropped. Defensible (this standalone component never renders a
 * criteria list beneath it — that lives in the separately-merged,
 * not-yet-wired `GateCriteriaList`), but not previously disclosed;
 * disclosed explicitly now. Revisit once a future `E7C`-style
 * candidate wires `GateHeader` directly above `GateCriteriaList`.
 *
 * **Real-mechanism correction, not just a persona swap.** The
 * reference file's own `approverNote` claims *"The Architect agent
 * opens the gate on its own once the criteria read true — no human
 * step. The owner is only asked if opening would require waiving a
 * criterion."* This describes a fully autonomous gate-opening
 * decision — the same class of not-yet-real M4 autonomous-loop
 * capability D4/D5 were rescheduled to M4 for, and the same "no
 * automatic dispatch yet" honesty D6's own crash-recovery command and
 * the crash fixture's own footer note already established
 * ("NeedsReplan has no automatic resume in Maestro today ... none of
 * them dispatch anything yet"). No code anywhere in
 * `services/maestro/maestro/*.py` implements an autonomous
 * milestone-gate-opening decision — the only real "gate" concept in
 * that codebase is `packet_contract.py`'s own per-attempt synthetic
 * validation gates, an unrelated mechanism. This component's own
 * `approverNote` is corrected to state the real, current mechanism
 * honestly (no automated opening exists yet; it remains a manual,
 * owner-reviewed action; automatic opening depends on the same real
 * M4 autonomous Architect loop D4/D5 already named) — matching this
 * program's own established "never render a fictional capability as
 * real" discipline, applied here to a mechanism claim, not merely a
 * name.
 *
 * **Corrected — non-blocking finding from independent implementation
 * review:** the reference file's own `approverNote` has a second
 * clause this component's own rationale above did not separately
 * disclose dropping — *"The owner is only asked if opening would
 * require waiving a criterion."* Since no automated opening exists at
 * all today (the correction above), a separate "the owner is asked
 * for waivers" escalation path describes a step in that same not-yet-
 * real autonomous flow, so it is dropped for the same real reason, not
 * a second, independent edit — disclosed explicitly now, the same
 * footing as the lede's own "below" disclosure above.
 *
 * **Real, derived counts, not a second hardcoded literal.** The state
 * line ("Closed · N of 5 criteria met, M partly") and the button note
 * ("Blocked by K open criteria") are both computed directly from the
 * already-real, already-merged `GATE_CRITERIA` fixture's own `met`
 * field (`YES_COUNT`/`PART_COUNT`/`NO_COUNT`/`TOTAL_COUNT` above) —
 * not separately hand-typed numbers that could silently drift from
 * `GATE_CRITERIA`'s own real content if it ever changes, matching this
 * program's own C7 single-state-source discipline.
 */
const SHELL_VARS = {
  "--atlas-gate-head-surface": colors.surface,
  "--atlas-gate-head-border": colors.borderDivider[0],
  "--atlas-gate-breadcrumb": colors.inkFaint,
  "--atlas-gate-breadcrumb-dot": "#CFC6D6",
  "--atlas-gate-title": colors.ink,
  "--atlas-gate-state": colors.inkMuted,
  "--atlas-gate-state-dot-border": colors.borderDashed[2],
  "--atlas-gate-button-border": colors.border,
  "--atlas-gate-button-bg": "#F6F4F9",
  "--atlas-gate-button-ink": colors.inkFaint,
  "--atlas-gate-button-note": colors.inkFaint,
  "--atlas-gate-lede": colors.inkSecondary,
  "--atlas-gate-panel-border": colors.border,
  "--atlas-gate-panel-label": colors.inkMuted,
  "--atlas-gate-approver-avatar-bg": AGENT_STYLE.rule.avBg,
  "--atlas-gate-approver-avatar-ink": AGENT_STYLE.rule.avColor,
  "--atlas-gate-approver-name": colors.ink,
  "--atlas-gate-approver-role": colors.inkMuted,
  "--atlas-gate-approver-note": colors.inkSecondary,
  "--atlas-gate-release-dot": colors.borderDashed[2],
  "--atlas-gate-release-text": colors.ink,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-font-display": fontFamily.display,
} as CSSProperties;

/**
 * Standalone gate header — the roadmap's own "gate-open state"
 * remainder of item 32 (E7): title, real derived state line, disabled
 * "Open gate" button with its own real derived note, a corrected lede,
 * and two panels (approver, what-opening-releases). Not wired into
 * `DesktopShell` — that is separate, later work (a future `E7C`-style
 * candidate), matching every other Wave E component's own established
 * "standalone until wired" precedent.
 */
export function GateHeader() {
  return (
    <div style={SHELL_VARS}>
      <div className={styles.headBlock}>
        <div className={styles.breadcrumb}>
          <span>m1-b</span>
          <span className={styles.breadcrumbDot} aria-hidden="true" />
          <span>milestone gate</span>
        </div>
        <div className={styles.headRow}>
          <div className={styles.headMain}>
            <h1 className={styles.title}>Overlay and support surfaces</h1>
            <div className={styles.stateLine}>
              <span className={styles.stateDot} aria-hidden="true" />
              Closed · {YES_COUNT} of {TOTAL_COUNT} criteria met, {PART_COUNT} partly
            </div>
          </div>
          <div className={styles.buttonBlock}>
            <button type="button" className={styles.openButton} disabled>
              Open gate
            </button>
            <div className={styles.buttonNote}>Blocked by {NO_COUNT} open criteria</div>
          </div>
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.lede}>
          A gate is not a status. Every criterion has to be true before M1-B packets can be dispatched, and the
          Coordinator verifies them against records — not against anyone's summary.
        </div>

        <div className={styles.panels}>
          <div className={styles.panel}>
            <div className={styles.panelLabel}>approver</div>
            <div className={styles.approverIdentity}>
              <span className={styles.approverAvatar}>CO</span>
              <div className={styles.approverText}>
                <div className={styles.approverName}>Coordinator</div>
                <div className={styles.approverRole}>rules on the gate · records fidelity</div>
              </div>
            </div>
            <div className={styles.approverNote}>
              No automated gate-opening exists in Maestro today — opening the gate remains a manual, owner-reviewed
              action. This becomes an automatic Coordinator decision once M4's own autonomous Architect loop exists.
            </div>
          </div>
          <div className={styles.panel}>
            <div className={styles.panelLabel}>what opening releases</div>
            <ul className={styles.releasesList}>
              {RELEASES.map((release) => (
                <li key={release} className={styles.releaseItem}>
                  {release}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GateHeader;
