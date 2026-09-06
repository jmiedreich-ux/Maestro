# M2 Wave E — Gate Header, Approver, and Releases Panel — Candidate 01

**Slice ID:** `MB-SLICE-M2-E7B-GATE-HEADER-01`
**Status:** `Awaiting Decision Fidelity review`
**Base:** `8aa33ce` (full: `8aa33ce5787e296d95dee0b4921ebd77e2b752dd`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 32, *"E7 — Gate: criteria list + gate-open state
(disabled button, approver/what-opens panel)."* The criteria list half
is already merged (`MB-SLICE-M2-E7-GATE-CRITERIA-LIST-02`,
`GateCriteriaList.tsx`) — its own packet explicitly deferred this
remainder to "a future `E7B`-style candidate," disclosing why: the
gate's own header lede and approver note both reference the mockup's
fictional M4-only "Architect agent" persona and need the same
real-mechanism adaptation Wave C used (C3/C4). This slice is that
candidate: the gate title/state-line/disabled-button header, the
corrected lede, and the approver + "what opening releases" panels.

**This slice does not wire `GateHeader` or `GateCriteriaList` into
`DesktopShell`** — that is separate, later work (a future `E7C`-style
candidate), matching the E7 packet's own already-disclosed exclusion
and every other Wave E component's own established "standalone until
wired" precedent (E1 through E7 were all merged standalone first).

This slice is frontend-only — no backend file touched. It adds exactly
3 new files (`GateHeader.tsx`, `GateHeader.module.css`,
`GateHeader.test.tsx`) under `apps/atlas/src/gate/`; no existing file
is modified. `apps/atlas/src/gate/fixtures.ts` and
`apps/atlas/src/agents/agentStyle.ts` are read-only imports.

## Evidence

`Atlas Explorations.dc.html:214-266` is the real `showGate` header
block, immediately preceding the criteria card (`:234-247`, already
merged) inside the same `<main>`:

1. **Title bar** (`:216-227`): breadcrumb "m1-b · milestone gate", a
   real `<h1>` title ("Overlay and support surfaces"), a state line
   (dashed dot + "Closed · 2 of 5 criteria met, 1 partly"), and a
   disabled "Open gate" button with a "Blocked by 2 open criteria"
   note.
2. **Lede** (`:232`): *"A gate is not a status. Every criterion below
   has to be true before M1-B packets can be dispatched, and the
   Architect agent verifies them against records — not against
   anyone's summary."*
3. **Approver panel** (`:250-257`): avatar "AR" (violet badge,
   `#E7E1FB`/`#3F1FC0`), name "Architect agent", role "rules on the
   gate · records fidelity", and `approverNote`: *"The Architect agent
   opens the gate on its own once the criteria read true — no human
   step. The owner is only asked if opening would require waiving a
   criterion."*
4. **"What opening releases" panel** (`:258-265`): 3 real bullet items
   — "B.0 through B.4 become dispatchable", "Overlay files unlock for
   write", "M1-A packets become read-only records".

**Real derivation** (`:845-862`): `disabled: true`, `btnCursor:
'not-allowed'`, `btnNote: 'Blocked by 2 open criteria'` — the gate is
unconditionally closed in this real snapshot. `metLabel`/`stateLine`/
`btnNote` are all computed from the same real `GATE_CRITERIA` array
already merged (2 yes, 1 part, 2 no of 5) — this slice derives its own
state line and button note the same way (`GATE_CRITERIA.filter(...)`),
not as separately hand-typed numbers.

**Real token matches**, checked directly against `colors.ts`:
`colors.inkFaint` (`#A79BB4`), `colors.borderDashed[2]` (`#B9AFC4`,
the same token `--atlas-ag-wait-dot-border` already uses),
`colors.inkMuted` (`#8E8299`), `colors.border` (`#E7E1EE`),
`colors.inkSecondary` (`#6C6376`), and — for the approver avatar —
`colors.accentWash[1]`/`colors.accentDeepest`, which exactly equal the
reference file's own literal "AR" badge colors (`#E7E1FB`/`#3F1FC0`)
and are *already* the real, established Coordinator avatar pairing
this program's own E4 `AGENT_STYLE.rule` uses. Two literals have no
token match, checked against every color family in `colors.ts`: the
breadcrumb's own separator dot (`#CFC6D6` — the same value
`GateCriteriaList.tsx`'s own `--atlas-gate-mark-no-border` already
discloses as coincidentally equal to `colors.navText` but not scoped
for general reuse), and the disabled button's own background
(`#F6F4F9`).

## Design rationale

1. **Real persona substitution, matching Wave C's own established
   pattern (C3/C4) and E4's own already-reviewed precedent.** The
   fictional M4-only "Architect agent" is substituted with the real
   Coordinator actor: avatar initials "CO" (matching `AGENTS`'s own
   real Coordinator entry), the same avatar-color pairing E4's own
   `AGENT_STYLE.rule` already established (a real, already-reviewed
   match to the reference file's own literal colors, not invented
   here), and the lede corrected from "the Architect agent verifies
   them against records" to "the Coordinator verifies them against
   records" — the same real, sound claim (M1's own Coordinator role
   already does exactly this kind of record-based verification, per
   this session's own D2/D6 findings), just the real actor's name.
2. **Real-mechanism correction, not just a persona swap.** The
   reference file's own `approverNote` claims the gate opens itself
   "on its own... no human step" — a fully autonomous decision, the
   same class of not-yet-real M4 autonomous-loop capability D4/D5 were
   rescheduled to M4 for. A repository-wide check of
   `services/maestro/maestro/*.py` confirms no code implements an
   autonomous milestone-gate-opening decision — the only real "gate"
   concept in that codebase is `packet_contract.py`'s own per-attempt
   synthetic validation gates, an unrelated mechanism. This slice's own
   `approverNote` states the real, current mechanism honestly instead
   (no automated opening exists yet; it remains manual and
   owner-reviewed; automatic opening depends on the same real M4
   autonomous Architect loop D4/D5 already named) — matching this
   program's own "never render a fictional capability as real"
   discipline (already applied to crash-recovery options in D6/the
   crash fixture's own footer note), applied here to a mechanism
   claim, not merely a name.
3. **Real, derived counts, not a second hardcoded literal.** The state
   line and button note are both computed directly from the already-
   real, already-merged `GATE_CRITERIA` fixture's own `met` field, not
   separately hand-typed numbers that could silently drift from
   `GATE_CRITERIA`'s own real content — matching this program's own C7
   single-state-source discipline.
4. **The releases panel's 3 items are transcribed verbatim** — pure
   reporting content about M1-B/M1-A structure, no persona, no
   adaptation needed.
5. **Every new `--atlas-gate-*` CSS custom property is consumed by at
   least one real CSS rule** — checked exhaustively (the specific
   class of defect an earlier Decision Fidelity review caught in F3's
   own first draft).

## Guards

1. This slice adds exactly 3 new files under `apps/atlas/src/gate/`
   (`GateHeader.tsx`, `GateHeader.module.css`, `GateHeader.test.tsx`)
   — no existing file, no backend file, touched.
   `apps/atlas/src/gate/fixtures.ts` (already merged) and
   `apps/atlas/src/agents/agentStyle.ts` (E4's own, already merged)
   are read-only imports, never modified.
2. `GateHeader` is not imported or mounted by `GateCriteriaList.tsx`,
   `DesktopShell.tsx`, or any other file — genuinely standalone,
   verified by the diff touching no other file.
3. No reference to the fictional "Architect agent" persona survives
   anywhere in this component's real, rendered text — a dedicated test
   asserts its absence (`queryByText(/Architect agent/)`).
4. No reference to the reference file's own autonomous-opening claim
   ("opens the gate on its own", "no human step") survives — a
   dedicated test asserts both phrases' absence.
5. The "Open gate" button is genuinely `disabled` (a real HTML
   attribute, not just styled to look disabled) — a dedicated test
   asserts `toBeDisabled()`.

## `apps/atlas/src/gate/GateHeader.tsx` (new)

```tsx
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
 * verification, per this session's own D2/D6 findings), just the real
 * actor's name.
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
```

## `apps/atlas/src/gate/GateHeader.module.css` (new)

```css
.headBlock {
  padding: 16px 34px 15px;
  background: var(--atlas-gate-head-surface);
  border-bottom: 1px solid var(--atlas-gate-head-border);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 9px;
  font: 500 11px var(--atlas-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--atlas-gate-breadcrumb);
}

.breadcrumbDot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--atlas-gate-breadcrumb-dot);
}

.headRow {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-top: 7px;
}

.headMain {
  min-width: 0;
  flex: 1;
}

.title {
  margin: 0;
  font-family: var(--atlas-font-display);
  font-size: 25px;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.15;
  color: var(--atlas-gate-title);
  text-wrap: pretty;
}

.stateLine {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 7px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--atlas-gate-state);
}

.stateDot {
  width: 9px;
  height: 9px;
  box-sizing: border-box;
  border-radius: 50%;
  border: 1.5px dashed var(--atlas-gate-state-dot-border);
}

.buttonBlock {
  flex: none;
  text-align: right;
}

.openButton {
  height: 34px;
  padding: 0 14px;
  border: 1px solid var(--atlas-gate-button-border);
  border-radius: 9px;
  background: var(--atlas-gate-button-bg);
  color: var(--atlas-gate-button-ink);
  cursor: not-allowed;
  font-size: 13px;
  font-weight: 600;
}

.buttonNote {
  margin-top: 5px;
  font-size: 12px;
  color: var(--atlas-gate-button-note);
}

.body {
  max-width: 66ch;
  padding: 22px 34px 30px;
}

.lede {
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--atlas-gate-lede);
  text-wrap: pretty;
}

.panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 14px;
}

.panel {
  border: 1px solid var(--atlas-gate-panel-border);
  border-radius: 14px;
  padding: 14px 16px;
}

.panelLabel {
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-gate-panel-label);
}

.approverIdentity {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.approverAvatar {
  width: 32px;
  height: 32px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  background: var(--atlas-gate-approver-avatar-bg);
  color: var(--atlas-gate-approver-avatar-ink);
  font: 600 11px var(--atlas-font-mono);
}

.approverText {
  min-width: 0;
}

.approverName {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--atlas-gate-approver-name);
}

.approverRole {
  font-size: 12.5px;
  color: var(--atlas-gate-approver-role);
}

.approverNote {
  margin-top: 11px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--atlas-gate-approver-note);
  text-wrap: pretty;
}

.releasesList {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}

.releaseItem {
  position: relative;
  padding-left: 14px;
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--atlas-gate-release-text);
  text-wrap: pretty;
}

.releaseItem::before {
  content: "";
  position: absolute;
  left: 0;
  top: 6px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--atlas-gate-release-dot);
}
```

## `apps/atlas/src/gate/GateHeader.test.tsx` (new)

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { AGENT_STYLE } from "../agents/agentStyle";
import { GateHeader } from "./GateHeader";
import { GATE_CRITERIA } from "./fixtures";

afterEach(cleanup);

describe("GateHeader", () => {
  it("renders the real breadcrumb and title", () => {
    render(<GateHeader />);
    expect(screen.getByText("m1-b")).toBeInTheDocument();
    expect(screen.getByText("milestone gate")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
  });

  it("derives the state line and button note directly from the real GATE_CRITERIA counts, not a second hardcoded literal", () => {
    const counts = { yes: 0, part: 0, no: 0 };
    for (const criterion of GATE_CRITERIA) {
      counts[criterion.met] += 1;
    }
    expect(counts).toEqual({ yes: 2, part: 1, no: 2 });

    render(<GateHeader />);
    expect(
      screen.getByText(`Closed · ${counts.yes} of ${GATE_CRITERIA.length} criteria met, ${counts.part} partly`),
    ).toBeInTheDocument();
    expect(screen.getByText(`Blocked by ${counts.no} open criteria`)).toBeInTheDocument();
  });

  it("renders a genuinely disabled 'Open gate' button", () => {
    render(<GateHeader />);
    const button = screen.getByRole("button", { name: "Open gate" });
    expect(button).toBeDisabled();
  });

  it("renders the real, corrected lede naming the Coordinator, not the fictional 'Architect agent'", () => {
    render(<GateHeader />);
    expect(
      screen.getByText(
        "A gate is not a status. Every criterion has to be true before M1-B packets can be dispatched, and the Coordinator verifies them against records — not against anyone's summary.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent/)).toBeNull();
  });

  it("renders the real approver panel naming the Coordinator, with the real Coordinator avatar identity from E4's own AGENT_STYLE", () => {
    const { container } = render(<GateHeader />);
    expect(screen.getByText("approver")).toBeInTheDocument();
    expect(screen.getByText("Coordinator")).toBeInTheDocument();
    expect(screen.getByText("rules on the gate · records fidelity")).toBeInTheDocument();
    expect(screen.getByText("CO")).toBeInTheDocument();

    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-approver-avatar-bg")).toBe(AGENT_STYLE.rule.avBg);
    expect(root.style.getPropertyValue("--atlas-gate-approver-avatar-ink")).toBe(AGENT_STYLE.rule.avColor);
  });

  it("renders the real, corrected approver note disclosing no automated gate-opening exists yet", () => {
    render(<GateHeader />);
    expect(
      screen.getByText(
        "No automated gate-opening exists in Maestro today — opening the gate remains a manual, owner-reviewed action. This becomes an automatic Coordinator decision once M4's own autonomous Architect loop exists.",
      ),
    ).toBeInTheDocument();
    // The reference file's own fictional-automation claim must not survive.
    expect(screen.queryByText(/opens the gate on its own/)).toBeNull();
    expect(screen.queryByText(/no human step/)).toBeNull();
  });

  it("renders the real 'what opening releases' panel with all 3 real items", () => {
    render(<GateHeader />);
    expect(screen.getByText("what opening releases")).toBeInTheDocument();
    expect(screen.getByText("B.0 through B.4 become dispatchable")).toBeInTheDocument();
    expect(screen.getByText("Overlay files unlock for write")).toBeInTheDocument();
    expect(screen.getByText("M1-A packets become read-only records")).toBeInTheDocument();
  });

  it("sets the real, checked B2 tokens and the two disclosed literals", () => {
    expect(colors.inkFaint).toBe("#A79BB4");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");
    expect(colors.inkMuted).toBe("#8E8299");
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.inkSecondary).toBe("#6C6376");

    const { container } = render(<GateHeader />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-breadcrumb")).toBe(colors.inkFaint);
    expect(root.style.getPropertyValue("--atlas-gate-state-dot-border")).toBe(colors.borderDashed[2]);
    expect(root.style.getPropertyValue("--atlas-gate-state")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-gate-button-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-gate-lede")).toBe(colors.inkSecondary);
    // Two disclosed literals with no real token match.
    expect(root.style.getPropertyValue("--atlas-gate-breadcrumb-dot")).toBe("#CFC6D6");
    expect(root.style.getPropertyValue("--atlas-gate-button-bg")).toBe("#F6F4F9");
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<GateHeader />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to this
scratch worktree (`/tmp/maestro-m2-e7b-header`, branch
`architecture/m2-e7b-gate-header`, base `8aa33ce`) and run through the
real frontend toolchain from `apps/atlas` (`npm install`, then each
script below), before this packet was finalized. Zero corrections were
needed — every check passed on the first attempt.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **23/23 test files, 179/179 tests
  passed** (9 new in `GateHeader.test.tsx`; zero regressions in the
  other 22 files, including `GateCriteriaList.test.tsx` and
  `AgentsRoster.test.tsx`, neither of which this slice modifies).
- `npm run build` (`vite build`) — clean, `39 modules transformed`, no
  warnings.
- Every declared `--atlas-gate-*` custom property was cross-checked
  programmatically against `GateHeader.module.css`'s own `var(...)`
  references — zero orphans either direction.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** a real, standalone `GateHeader` component
   renders the gate's title/state/disabled-button header, a corrected
   lede, and the approver/releases panels — with the fictional
   "Architect agent" persona and its fictional autonomous-opening claim
   both replaced by real, honest, Coordinator-attributed content —
   with zero backend change and zero regression to any of the 23
   existing test files.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** wiring `GateHeader`/`GateCriteriaList` into
   `DesktopShell`'s nav/content pane (a future `E7C`-style candidate);
   any mobile bottom-sheet variant of this content (roadmap item 36,
   F4, reuses this same fixture data separately).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every rendered surface is exercised by a
   React Testing Library render test, including negative assertions
   proving the fictional persona/mechanism text does not survive; no
   browser-based visual verification was performed (tooling failure,
   already disclosed in this session for M2-E4/F1/F2/F3/F3B/F3C, same
   root cause).
5. **Acceptance proof:** 23/23 test files, 179/179 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 3 new files, 0 modified files, all
   within `apps/atlas/src/gate`; zero backend files; no new
   third-party dependency; `gate/fixtures.ts` and
   `agents/agentStyle.ts` read-only, never modified.
7. **Proportionality ceiling:** one new presentational component, one
   new CSS module — no new fixture data invented beyond the 3 verbatim
   `RELEASES` strings and the corrected lede/approver-note sentences,
   both explicitly disclosed as real-mechanism corrections, not
   invented capability.
8. **Stop and escalation rule:** wiring this component into any shell,
   or building the mobile bottom-sheet variant, is explicitly out of
   scope — future slices' job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E7B-GATE-HEADER-01` |
| `phase` | `AwaitingReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-e7b-gate-header.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
