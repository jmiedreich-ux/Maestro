# M2 Wave C — Decision Fidelity Record (`DF-2`) Rendering — Candidate 01

**Slice ID:** `MB-SLICE-M2-C5-FIDELITY-RECORD-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `abf7183` (`origin/master`)

## Scope, deliberately minimal

Wave C5 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the Decision
Fidelity record card's visual anatomy — eyebrow (mark + label + record
id), subject/evidence header, one row per verified claim, and the
overall-verdict bar. No wiring into `PacketThread`, `DesktopShell`, or
`App.tsx`. `FidelityRecord` is a new, standalone component, exactly
like C3's `DecisionCard` and C4's `OwnerDecisionCard`.

**This slice's central content decision is different in kind from C3's
and C4's, and is worth stating plainly up front.** The reference
file's own domain model (README, "Domain model" section, quoted below)
describes a "Decision Fidelity check" as *"a record attached to a
ruling, listing claims verified against named evidence, each
matches/drifts/n/a, plus an overall verdict and a binding scope
note."* That is not a fictional mechanic invented for the mockup's
simulation — it is, structurally, the exact same concept as **this
project's own, real Decision Fidelity review process**: the one used
to review every M2 packet this session, this one included, which also
verifies specific claims against named evidence and renders a verdict.
Where C3 needed to invent an illustrative example grounded in a real
backend mechanism (`_REVIEW_ROUTES`), and C4 could reuse a real,
already-established scenario (C1's `A.2` escalation), this slice does
something new: it renders a real record *of this very program's own
review history* — specifically, C3's own closed Decision Fidelity
review (`MB-SLICE-M2-C3-DECISION-CARD-RULING-01`, PR #92) — instead of
the reference file's fictional "Architect agent ruled on a sentinel
version" narrative. This is not a stretch or a coincidence: it is the
literal, real referent the mockup's own domain-model language already
points to, once M2 does not invent an M4 Architect agent (per the
roadmap's standing architecture ruling).

Source quote (README, "Domain model" section, verbatim):

> **Decision Fidelity check** (e.g. `DF-2`): a record attached to a
> ruling, listing claims verified against named evidence, each
> `matches` / `drifts` / `n/a`, plus an overall verdict and a binding
> scope note.

**The reference file's own `DF-2` example content is not reused,
because it is inseparable from the fictional "Architect agent ruling"
narrative C3/C4 already established the program does not render.**
`Atlas Explorations.dc.html`'s only populated `fid` object (verbatim):

```js
fid: { id: 'DF-2', subject: 'Sentinel version for theme-free outputs', against: 'owner decision 15:02 · A.1 contract 9d3e1a2',
  rows: [
    ['Does not widen the frozen-presentation contract', 'matches', 'A.1 unchanged · 9d3e1a2'],
    ['Sentinel is derived, not a second identity source', 'matches', 'runtime layer only · no Core edit'],
    ['Stays inside A.2 scope: one Runtime file, one test', 'matches', 'no new file locks claimed'],
    ['Reviewer of record is unchanged', 'n/a', 'no correction consumed'],
  ], verdict: 'Faithful', note: 'Terra may resume A.2 with theme-less:1. Binding on A.3 through A.6 — a later packet that re-derives the version fails this check.' }
```

Every claim here is evidence for the mockup's own simulated
"Architect agent" ruling on the theme-free sentinel-version question —
a scenario this program has already, twice, deliberately declined to
render (C3's Scope section; C4's Scope section). Reusing this content
verbatim would reintroduce that fictional narrative through a side
door. This slice's own record (below) matches the *shape* exactly (one
`id`, one `subject`, one `against`, 4 claim rows each with
claim/evidence/verdict, one overall `verdict`, one `note`) but is
populated with real content from this project's own history.

**This slice's Decision Fidelity record, in full — real, verifiable,
not invented:**

| Field | Value |
|---|---|
| `id` | `DF-M2-C3` |
| `subject` | `M2-C3 decision-card packet: real-routing-table citation` |
| `against` | `PR #92 Decision Fidelity review · commit e8a87ca` |

Claim rows:

| Claim | Evidence | Verdict |
|---|---|---|
| Cites a real, existing `_REVIEW_ROUTES` entry as ruling evidence | `operational_state.py:74 · verified by grep` | `matches` |
| Renders the roadmap's required "link to the rule that fired" | exact rule citation in the `why` span · corrected 2026-09-05 | `matches` |
| No fictional "Architect agent" persona anywhere in rendered copy | badge/copy audit, `DecisionCard.tsx` | `matches` |
| Reuses C1's frozen `A.2` fixture thread | deliberately not reused — see the C3 packet's own Scope section | `n/a` |

Overall verdict: `Faithful`. Note: *"MB-SLICE-M2-C3-DECISION-CARD-RULING-01
closed clean after one targeted correction (PR #92). Binding on any
later slice that reuses this routing-table-citation pattern — the
cited rule must stay traceable to real `operational_state.py` source,
not restated from memory."*

Every one of these 4 claims is independently checkable against this
project's own real, public history: `operational_state.py:74` is the
same line C3's own packet cites (and whose citation was itself
corrected once — the `74` here is the corrected value, not the
original packet's mistaken `73`); PR #92 is the real, merged planning
PR for C3; the "no fictional persona" and "does not reuse A.2" claims
are directly checkable against C3's merged `DecisionCard.tsx` and its
packet's own Scope section. `id` (`DF-M2-C3`) deliberately does **not**
reuse the reference file's literal `DF-2` — reusing that exact string
would misleadingly imply this is the same record as the mockup's own
fictional one; this project's own slice-naming convention is used
instead.

**No message wrapper, no avatar, no chat-bubble context — a
simplification the reference markup's own structure already supports,
not an invented one.** Unlike the decision cards (which have their own
`display:grid;grid-template-columns:36px minmax(0,1fr)` row wrapper
with an empty avatar cell, matching the thread's own row layout), the
`DF-2` markup has no such wrapper — it is `margin-top:13px` continuation
content nested directly inside an existing chat message's body (see
markup below). Since M2 has no message-authoring agent to attach this
card to yet, this slice renders the same card markup directly,
standalone — matching the reference file's own structure exactly,
simply without the enclosing message it would normally sit inside.

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from):

```html
<sc-if value="{{ e.hasFidelity }}" hint-placeholder-val="{{ false }}">
<div style="margin-top:13px;max-width:60ch;border:1px solid #DAD2EC;border-radius:14px;background:#FBFAFE;overflow:hidden">
  <div style="display:flex;align-items:center;gap:9px;padding:12px 16px 0;font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#4A28CC"><span style="width:11px;height:11px;box-sizing:border-box;border-radius:3px;border:2px solid #5B34E8"></span>decision fidelity<span style="margin-left:auto;letter-spacing:.06em;color:#8E8299">{{ e.fid.id }}</span></div>
  <div style="padding:9px 16px 13px">
    <div style="font-size:15px;font-weight:600;line-height:1.4;text-wrap:pretty">{{ e.fid.subject }}</div>
    <div style="margin-top:4px;font-size:12.5px;color:#8E8299">verified against {{ e.fid.against }}</div>
  </div>
  <div style="display:flex;flex-direction:column;border-top:1px solid #EDE8F6">
    <sc-for list="{{ e.fid.rows }}" as="r" hint-placeholder-count="4">
    <div style="display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:baseline;gap:10px 14px;padding:10px 16px;border-bottom:1px solid #F3F0FA">
      <div style="min-width:0"><div style="font-size:13.5px;line-height:1.45;color:#221C29;text-wrap:pretty">{{ r.claim }}</div><div style="margin-top:2px;font:500 11.5px 'IBM Plex Mono',monospace;color:#8E8299">{{ r.evidence }}</div></div>
      <span style="flex:none;padding:3px 8px;border-radius:6px;background:{{ r.bg }};color:{{ r.color }};font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.07em;text-transform:uppercase">{{ r.verdict }}</span>
    </div>
    </sc-for>
  </div>
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:12px 16px;background:#F4F0FE">
    <span style="display:flex;align-items:center;gap:8px;font-size:13.5px;font-weight:700;color:#3F1FC0"><span style="width:12px;height:12px;border-radius:4px;background:#5B34E8"></span>{{ e.fid.verdict }}</span>
    <span style="min-width:0;flex:1;font-size:12.5px;line-height:1.5;color:#6C6376;text-wrap:pretty">{{ e.fid.note }}</span>
  </div>
</div>
</sc-if>
```

Verdict-tag color mapping (`Atlas Explorations.dc.html`, verbatim —
the `r.bg`/`r.color` template holes above):

```js
bg: v === 'matches' ? '#E4F6EE' : v === 'drifts' ? '#FBEAE7' : '#F2EEF8',
color: v === 'matches' ? '#1F6B4E' : v === 'drifts' ? '#A63F36' : '#6C6376'
```

**Color discrepancy table — every value checked against this
codebase's real B2 tokens; 4 real gaps, one already disclosed by C3:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| card border `#DAD2EC` | `colors.borderStrong[1]` | exact |
| card bg `#FBFAFE` | none in `colors.ts` (already disclosed once by C3's `DecisionCard.tsx`) | disclosed literal |
| eyebrow ink `#4A28CC` | `colors.accentHover` | exact |
| mark border `#5B34E8` | `colors.accent` | exact |
| record-id / against text `#8E8299` | `colors.inkMuted` | exact |
| subject text `#221C29` (implicit default, not explicitly styled in the reference markup) | `colors.ink` | exact |
| row divider (top) `#EDE8F6` | none in `colors.ts` (nearest, `colors.borderDivider[0]` `#EEEAF2`, is a different, real value — not reused) | disclosed literal |
| row divider (between rows) `#F3F0FA` | none in `colors.ts` (nearest, `colors.borderDivider[1]` `#F3F0F6`, is a different, real value — not reused) | disclosed literal |
| claim text `#221C29` | `colors.ink` | exact |
| evidence text `#8E8299` | `colors.inkMuted` | exact |
| `matches` tag `#E4F6EE`/`#1F6B4E` | `colors.successWash`/`colors.successText` | exact |
| `drifts` tag bg `#FBEAE7` | none in `colors.ts` (`colors.dangerWash` is `#FEF7F6`, a different, real value — not reused) | disclosed literal |
| `drifts` tag text `#A63F36` | `colors.dangerText` | exact |
| `n/a` tag `#F2EEF8`/`#6C6376` | `colors.neutralChip`/`colors.inkSecondary` | exact |
| bar bg `#F4F0FE` | `colors.accentWash[4]` | exact |
| bar square `#5B34E8` | `colors.accent` | exact |
| overall-verdict text `#3F1FC0` | `colors.accentDeepest` | exact |
| note text `#6C6376` | `colors.inkSecondary` | exact |

4 real, checked gaps (`bg`, both row dividers, `drifts` tag bg). The
`drifts` verdict is implemented (color mapping and CSS class) even
though this slice's own chosen evidence never exercises it (all 4 real
claims are `matches` or `n/a`) — kept for a complete, correct 3-verdict
palette matching the reference file's own enumeration, the same
reasoning C1 used to keep its full, unexercised avatar palette (the
`by` role, never rendered by `A.2`'s fixture).

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C5-FIDELITY-RECORD-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:abf71832efd6e42bad9abaabdb7b45d1936c0199"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`. The first real run found one
genuine defect in the test file (not the component): a test asserted
no rendered text matches `/Architect agent/`, but this record's own
4th claim ("No fictional \"Architect agent\" persona anywhere in
rendered copy") legitimately contains that exact phrase as the subject
of a real claim — a real self-referential content collision, not a
component bug. Fixed by narrowing that assertion to what actually must
be absent (the reference file's fictional sentinel-version narrative
and its literal `DF-2` id), not the substring "Architect agent" on its
own. After that fix: 50/50 tests passed (43 existing + 7 new),
typecheck and lint clean, production build succeeded.

`apps/atlas/src/decision/fidelityFixtures.ts` (new — the evidence data
and its types; no rendering logic):

```ts
/**
 * Real content, not a simulated "Architect agent" ruling. The
 * reference file's own domain model describes a "Decision Fidelity
 * check" as "a record attached to a ruling, listing claims verified
 * against named evidence, each matches/drifts/n/a, plus an overall
 * verdict and a binding scope note" (README, "Domain model" section) —
 * that is structurally the exact same concept as THIS project's own,
 * real Decision Fidelity review process (the one used to review every
 * M2 packet this session, including C3 and C4). So this record cites a
 * real, already-closed review from this project's own history — C3's
 * (`MB-SLICE-M2-C3-DECISION-CARD-RULING-01`, PR #92) — rather than
 * inventing a fictional Architect-agent ruling on a fictional
 * contract question. `id` is a real, traceable identifier following
 * this project's own slice-naming convention, not the reference
 * file's arbitrary "DF-2" (reusing that literal id would misleadingly
 * imply continuity with the mockup's own, different, fictional
 * narrative).
 */
export interface FidelityRow {
  claim: string;
  evidence: string;
  verdict: "matches" | "drifts" | "n/a";
}

export interface FidelityRecordExample {
  id: string;
  subject: string;
  against: string;
  rows: FidelityRow[];
  verdict: string;
  note: string;
}

export const FIDELITY_RECORD_EXAMPLE: FidelityRecordExample = {
  id: "DF-M2-C3",
  subject: "M2-C3 decision-card packet: real-routing-table citation",
  against: "PR #92 Decision Fidelity review · commit e8a87ca",
  rows: [
    {
      claim: "Cites a real, existing _REVIEW_ROUTES entry as ruling evidence",
      evidence: "operational_state.py:74 · verified by grep",
      verdict: "matches",
    },
    {
      claim: "Renders the roadmap's required \"link to the rule that fired\"",
      evidence: "exact rule citation in the why span · corrected 2026-09-05",
      verdict: "matches",
    },
    {
      claim: "No fictional \"Architect agent\" persona anywhere in rendered copy",
      evidence: "badge/copy audit, DecisionCard.tsx",
      verdict: "matches",
    },
    {
      claim: "Reuses C1's frozen A.2 fixture thread",
      evidence: "deliberately not reused — see the C3 packet's own Scope section",
      verdict: "n/a",
    },
  ],
  verdict: "Faithful",
  note: "MB-SLICE-M2-C3-DECISION-CARD-RULING-01 closed clean after one targeted correction (PR #92). Binding on any later slice that reuses this routing-table-citation pattern — the cited rule must stay traceable to real operational_state.py source, not restated from memory.",
};
```

`apps/atlas/src/decision/FidelityRecord.module.css` (new — CSS Module,
`var(--atlas-*)` only, following the exact C1/C3/C4/B3/B4 pattern):

```css
.card {
  margin-top: 13px;
  max-width: 60ch;
  border: 1px solid var(--atlas-df-border);
  border-radius: 14px;
  background: var(--atlas-df-bg);
  overflow: hidden;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 12px 16px 0;
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-df-ink);
}

.mark {
  width: 11px;
  height: 11px;
  box-sizing: border-box;
  border-radius: 3px;
  border: 2px solid var(--atlas-df-mark-border);
}

.recordId {
  margin-left: auto;
  letter-spacing: 0.06em;
  color: var(--atlas-df-id-color);
}

.head {
  padding: 9px 16px 13px;
}

.subject {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  text-wrap: pretty;
  color: var(--atlas-df-subject-color);
}

.against {
  margin-top: 4px;
  font-size: 12.5px;
  color: var(--atlas-df-against-color);
}

.rows {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--atlas-df-row-divider-top);
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: baseline;
  gap: 10px 14px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--atlas-df-row-divider);
}

.claim {
  font-size: 13.5px;
  line-height: 1.45;
  color: var(--atlas-df-claim-color);
  text-wrap: pretty;
}

.evidence {
  margin-top: 2px;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-df-evidence-color);
}

.verdictTag {
  flex: none;
  padding: 3px 8px;
  border-radius: 6px;
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.verdictMatches {
  background: var(--atlas-df-verdict-matches-bg);
  color: var(--atlas-df-verdict-matches-color);
}

.verdictDrifts {
  background: var(--atlas-df-verdict-drifts-bg);
  color: var(--atlas-df-verdict-drifts-color);
}

.verdictNa {
  background: var(--atlas-df-verdict-na-bg);
  color: var(--atlas-df-verdict-na-color);
}

.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: var(--atlas-df-bar-bg);
}

.overallVerdict {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 700;
  color: var(--atlas-df-verdict-text);
}

.barSquare {
  width: 12px;
  height: 12px;
  border-radius: 4px;
  background: var(--atlas-df-bar-square);
}

.note {
  min-width: 0;
  flex: 1;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--atlas-df-note-color);
  text-wrap: pretty;
}
```

`apps/atlas/src/decision/FidelityRecord.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { FIDELITY_RECORD_EXAMPLE, type FidelityRow } from "./fidelityFixtures";
import styles from "./FidelityRecord.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real, non-templated DF-2
 * markup (this card's colors are hardcoded in the markup, not driven
 * by a `blk`-style variant object — there is only one visual
 * treatment). Three values have no equivalent B2 token and stay
 * disclosed literals, each checked directly against the reference
 * file: `bg` (`#FBFAFE`, already disclosed once by C3's ruling-variant
 * `DecisionCard.tsx`), and the two row-divider colors (`#EDE8F6`,
 * `#F3F0FA`) — close to, but distinct from, `colors.borderDivider`'s
 * three real values. The `drifts` verdict background (`#FBEAE7`) also
 * has no exact token match and stays a disclosed literal, even though
 * this slice's own chosen evidence never exercises the `drifts`
 * verdict — kept for a complete, correct 3-verdict palette matching
 * the reference file's own enumeration, the same reasoning C1 used to
 * keep its full, unexercised avatar palette.
 */
const SHELL_VARS = {
  "--atlas-df-border": colors.borderStrong[1],
  "--atlas-df-bg": "#FBFAFE",
  "--atlas-df-ink": colors.accentHover,
  "--atlas-df-mark-border": colors.accent,
  "--atlas-df-id-color": colors.inkMuted,
  "--atlas-df-subject-color": colors.ink,
  "--atlas-df-against-color": colors.inkMuted,
  "--atlas-df-row-divider-top": "#EDE8F6",
  "--atlas-df-row-divider": "#F3F0FA",
  "--atlas-df-claim-color": colors.ink,
  "--atlas-df-evidence-color": colors.inkMuted,
  "--atlas-df-verdict-matches-bg": colors.successWash,
  "--atlas-df-verdict-matches-color": colors.successText,
  "--atlas-df-verdict-drifts-bg": "#FBEAE7",
  "--atlas-df-verdict-drifts-color": colors.dangerText,
  "--atlas-df-verdict-na-bg": colors.neutralChip,
  "--atlas-df-verdict-na-color": colors.inkSecondary,
  "--atlas-df-bar-bg": colors.accentWash[4],
  "--atlas-df-bar-square": colors.accent,
  "--atlas-df-verdict-text": colors.accentDeepest,
  "--atlas-df-note-color": colors.inkSecondary,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const VERDICT_CLASS: Record<FidelityRow["verdict"], string> = {
  matches: styles.verdictMatches,
  drifts: styles.verdictDrifts,
  "n/a": styles.verdictNa,
};

/**
 * The reference file nests this card inside a chat message body (no
 * avatar/row grid of its own — see the markup this slice transcribes).
 * There is no message-authoring agent in M2 to attribute it to, so
 * this slice renders the same card markup directly, standalone,
 * exactly like every other C-wave component before its own wiring
 * slice.
 */
export function FidelityRecord() {
  const { id, subject, against, rows, verdict, note } = FIDELITY_RECORD_EXAMPLE;
  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.eyebrow}>
        <span className={styles.mark} aria-hidden="true" />
        decision fidelity
        <span className={styles.recordId}>{id}</span>
      </div>
      <div className={styles.head}>
        <div className={styles.subject}>{subject}</div>
        <div className={styles.against}>verified against {against}</div>
      </div>
      <div className={styles.rows}>
        {rows.map((row) => (
          <div key={row.claim} className={styles.row}>
            <div>
              <div className={styles.claim}>{row.claim}</div>
              <div className={styles.evidence}>{row.evidence}</div>
            </div>
            <span className={`${styles.verdictTag} ${VERDICT_CLASS[row.verdict]}`}>{row.verdict}</span>
          </div>
        ))}
      </div>
      <div className={styles.bar}>
        <span className={styles.overallVerdict}>
          <span className={styles.barSquare} aria-hidden="true" />
          {verdict}
        </span>
        <span className={styles.note}>{note}</span>
      </div>
    </div>
  );
}

export default FidelityRecord;
```

`apps/atlas/src/decision/FidelityRecord.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { FidelityRecord } from "./FidelityRecord";
import { FIDELITY_RECORD_EXAMPLE } from "./fidelityFixtures";

afterEach(cleanup);

describe("FidelityRecord", () => {
  it("renders the real record id, subject, and evidence citation — not the reference file's fictional DF-2 sentinel-version narrative", () => {
    render(<FidelityRecord />);
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.id)).toBeInTheDocument();
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.subject)).toBeInTheDocument();
    expect(screen.getByText(`verified against ${FIDELITY_RECORD_EXAMPLE.against}`)).toBeInTheDocument();
    // Not a substring check for "Architect agent" — one of this record's
    // own real claims is honestly ABOUT the absence of that persona and
    // names it explicitly. What must be absent is the reference file's
    // fictional sentinel-version ruling narrative and record id.
    expect(screen.queryByText(/theme-free|theme-less|sentinel version/)).toBeNull();
    expect(screen.queryByText("DF-2")).toBeNull();
  });

  it("renders all 4 real claim rows with their evidence and verdicts", () => {
    render(<FidelityRecord />);
    for (const row of FIDELITY_RECORD_EXAMPLE.rows) {
      expect(screen.getByText(row.claim)).toBeInTheDocument();
      expect(screen.getByText(row.evidence)).toBeInTheDocument();
    }
    expect(screen.getAllByText("matches")).toHaveLength(3);
    expect(screen.getAllByText("n/a")).toHaveLength(1);
    expect(screen.queryByText("drifts")).toBeNull();
  });

  it("renders the overall verdict and binding note", () => {
    render(<FidelityRecord />);
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.verdict)).toBeInTheDocument();
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.note)).toBeInTheDocument();
  });

  it("sets the card border, background, and eyebrow-ink CSS variables to the real, checked reference values", () => {
    expect(colors.borderStrong[1]).toBe("#DAD2EC");
    expect(colors.accentHover).toBe("#4A28CC");
    const { container } = render(<FidelityRecord />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-df-border")).toBe(colors.borderStrong[1]);
    expect(root.style.getPropertyValue("--atlas-df-bg")).toBe("#FBFAFE");
    expect(root.style.getPropertyValue("--atlas-df-ink")).toBe(colors.accentHover);
  });

  it("sets the matches/n/a verdict tag CSS variables to the real success/neutral tokens", () => {
    expect(colors.successWash).toBe("#E4F6EE");
    expect(colors.successText).toBe("#1F6B4E");
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<FidelityRecord />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-df-verdict-matches-bg")).toBe(colors.successWash);
    expect(root.style.getPropertyValue("--atlas-df-verdict-matches-color")).toBe(colors.successText);
    expect(root.style.getPropertyValue("--atlas-df-verdict-na-bg")).toBe(colors.neutralChip);
  });

  it("sets the overall-verdict bar CSS variables to the real accent-wash and accent-deepest tokens", () => {
    expect(colors.accentWash[4]).toBe("#F4F0FE");
    expect(colors.accentDeepest).toBe("#3F1FC0");
    const { container } = render(<FidelityRecord />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-df-bar-bg")).toBe(colors.accentWash[4]);
    expect(root.style.getPropertyValue("--atlas-df-verdict-text")).toBe(colors.accentDeepest);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<FidelityRecord />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `PacketThread`, `DesktopShell`, or
   `App.tsx` — standalone, exactly like C3's `DecisionCard` and C4's
   `OwnerDecisionCard`.
2. This slice does not import from `apps/atlas/src/thread/fixtures.ts`,
   C3's `fixtures.ts`/`DecisionCard.*`, or C4's `ownerFixtures.ts`/
   `OwnerDecisionCard.*` — `fidelityFixtures.ts` is an independent
   object.
3. Every color value is either a real B2 token or a disclosed literal
   checked directly against `Atlas Explorations.dc.html` (the
   discrepancy table above); none is invented or borrowed from a
   near-but-wrong existing token.
4. The rendered evidence cites this project's own real, closed
   Decision Fidelity review history (C3's), not the reference file's
   fictional sentinel-version ruling narrative; `id` deliberately does
   not reuse the reference file's literal `DF-2`.
5. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, or either of C3's/C4's own files is
   modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/decision/fidelityFixtures.ts` (new)
- `apps/atlas/src/decision/FidelityRecord.module.css` (new)
- `apps/atlas/src/decision/FidelityRecord.tsx` (new)
- `apps/atlas/src/decision/FidelityRecord.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/tokens/`, and C3's/C4's own files are untouched.

The 7 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 50 total after this slice (43 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7 thread
tests, 5 mobile-shell tests, 10 desktop-shell tests — + 7 new). `npm run
build` must still succeed; `FidelityRecord` is not expected to appear
in the `dist/` bundle, matching every prior standalone slice's own
build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `FidelityRecord` renders the Decision
   Fidelity record's exact visual anatomy (eyebrow, subject/evidence
   header, claim rows, overall-verdict bar) using real B2 tokens or
   disclosed reference-file-checked literals, populated with a real
   record of this project's own closed C3 Decision Fidelity review —
   not the reference mockup's fictional "Architect agent" ruling.
2. **Operating and threat model:** a trusted local dev box; fully
   read-only, no interactive element of any kind.
3. **Explicit exclusions:** the crash card (C6), header/state-source
   wiring (C7), any wiring into `PacketThread`/`DesktopShell`/
   `App.tsx`, any second evidence example, any message/avatar wrapper
   (there is no message-authoring agent to attach this card to yet).
4. **Assurance level:** practical component-rendering correctness with
   an accurately cited real project history (a real PR, a real,
   correctly-numbered source line, a real merged component's actual
   behavior), proportionate to a read-only view with no data dependency
   and no consumer yet — identical assurance posture to C3/C4, with the
   added discipline of citing this project's own history accurately
   rather than a backend mechanism or a sibling fixture.
5. **Acceptance proof:** the 7 named tests, the existing 43 `apps/atlas`
   tests continuing to pass (50 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color either a real token property or a
   literal checked directly against the reference file; no import of
   any sibling C1/C3/C4 module.
7. **Proportionality ceiling:** one view component, one fixtures
   module, one CSS Module; no message wrapper, no wiring, no second
   record example.
8. **Stop and escalation rule:** wiring `FidelityRecord` into a real
   message/thread context, or generating this record's content from a
   live review-readiness/review-outcome data source instead of a
   hand-authored citation of C3's history, is new, separately reviewed
   work — not decided implicitly here. Rendering the crash card is
   C6's job, not this slice's. If this record's cited evidence (PR #92,
   `operational_state.py:74`, C3's merged source) ever changes or is
   found inaccurate, that is a defect against this slice requiring
   correction, not a silent acceptability. A discovered proof/contract
   defect against a frozen slice terminally returns that slice. One
   planning correction and one implementation correction are the
   maximum available.
