import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "../history/fixtures";
import { HISTORY_KIND_STYLE } from "../history/historyStyle";
import styles from "./ActivityTab.module.css";

type ActivitySegment = "hist" | "agents" | "cost";

const SEGMENTS: ReadonlyArray<{ key: ActivitySegment; label: string }> = [
  { key: "hist", label: "History" },
  { key: "agents", label: "Agents" },
  { key: "cost", label: "Cost" },
];

/**
 * Mobile Activity-tab colors from `Atlas Mobile.dc.html`'s real `isAct`
 * markup — the header and segmented control (lines 219-227) and the
 * History segment this slice builds (lines 230-249); the real `isAct`
 * block itself continues past line 249 through the Agents (252-278)
 * and Cost (280 onward) segments this slice deliberately does not
 * build yet (see "Scope, deliberately minimal" in this slice's own
 * packet) — checked directly against `colors.ts`. Real token matches: `colors.segmentedTrack[0]`
 * (the segmented control's own track background, `#EDE9F3`, line 222 —
 * a different real index of the same array E3's `PerfBreakdownCard`
 * already uses `[1]` from, both real, not invented), `colors.segmentedSelected`
 * (the selected segment's own white background, `#fff`, matching the
 * real `renderVals()` rule `bg: s.seg===k?'#fff':'transparent'`),
 * `colors.ink`/`colors.inkMuted` (selected/unselected label color,
 * matching the same rule's `color:` branch), and `colors.pageBgMobile`
 * (the timeline dot's own outer ring background, `#F7F5FA`, line 240 —
 * simpler than desktop History's own urgent-ring treatment, since the
 * real mobile markup has no second ring layer at all). The timeline
 * rail (`#E6E0EE`, line 239) has no equivalent token and stays a
 * disclosed literal — a different real value from desktop History's
 * own disclosed rail color (`#EDE8F2`), not a typo of it, checked
 * directly against both reference files.
 *
 * The trailing timeline note reuses the exact real
 * `HISTORY_EMPTY_NOTE` constant E6's own `History.tsx` already
 * established, rather than transcribing the mobile markup's own
 * shorter literal text at line 249 ("...have not been dispatched.",
 * missing the desktop constant's own "— nothing to record yet." tail)
 * — the same real fact, stated once, matching this program's own
 * single-source-of-identity precedent (F2 reused C7's eyebrow/title
 * pair rather than a mockup-specific abbreviation for the same
 * reason).
 */
const SHELL_VARS = {
  "--atlas-seg-track": colors.segmentedTrack[0],
  "--atlas-seg-selected-bg": colors.segmentedSelected,
  "--atlas-seg-selected-ink": colors.ink,
  "--atlas-seg-ink": colors.inkMuted,
  "--atlas-stat-label": colors.inkMuted,
  "--atlas-stat-value": colors.ink,
  "--atlas-rail": "#E6E0EE",
  "--atlas-dot-ring": colors.pageBgMobile,
  "--atlas-entry-detail": colors.inkSecondary,
  "--atlas-empty-note": colors.inkFaint,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const style = HISTORY_KIND_STYLE[entry.kind];
  const dotSize = style.urgent ? 11 : 10;
  const dotBg = style.urgent ? style.dotColor : colors.surface;
  return (
    <div className={styles.row}>
      <div className={styles.railCol}>
        <span className={styles.rail} aria-hidden="true" />
        <span
          className={styles.dot}
          aria-hidden="true"
          style={{ width: dotSize, height: dotSize, background: dotBg, borderColor: style.dotColor }}
        />
      </div>
      <div className={styles.body}>
        <div className={styles.entryLine}>
          <span className={styles.tag} style={{ background: style.tagBg, color: style.tagColor }}>
            {entry.kind}
          </span>
          <span className={styles.entryMeta}>
            {entry.time} · {entry.packet}
          </span>
        </div>
        <div className={styles.entryTitle}>{entry.title}</div>
        <div className={styles.entryDetail}>{entry.detail}</div>
      </div>
    </div>
  );
}

/**
 * Mobile "Activity" tab — the reference file's own `isAct` view: a
 * page title, a real 3-way segmented control (History/Agents/Cost,
 * defaulting to History, matching the reference file's own real
 * `seg: 'hist'` initial state), and the History segment's real content
 * reusing E6's own `HISTORY_STATS`/`HISTORY_ENTRIES`/`HISTORY_KIND_STYLE`
 * fixture and style data restyled as a simpler mobile timeline (no
 * "Open … thread" button — the real mobile markup has no such control
 * on this surface, checked directly). The Agents and Cost segments are
 * real, tappable, and switch the segmented control's own selection
 * state correctly, but render only a placeholder — reusing E4's
 * `AgentsRoster`/E1-E3's performance data for those two segments is
 * separate, future work (roadmap item 35's own remaining scope),
 * matching this program's own established pattern of splitting an
 * oversized roadmap item into independently reviewable slices (E1/E1B,
 * E2/E2B).
 */
export function ActivityTab() {
  const [segment, setSegment] = useState<ActivitySegment>("hist");

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Activity</h1>
        <div className={styles.segmented}>
          {SEGMENTS.map((seg) => (
            <button
              key={seg.key}
              type="button"
              className={`${styles.segButton} ${segment === seg.key ? styles.segSelected : ""}`}
              aria-current={segment === seg.key ? "true" : undefined}
              onClick={() => setSegment(seg.key)}
            >
              {seg.label}
            </button>
          ))}
        </div>
      </div>
      <div className={styles.content}>
        {segment === "hist" ? (
          <>
            <div className={styles.stats}>
              {HISTORY_STATS.map((stat) => (
                <span key={stat.label} className={styles.stat}>
                  {stat.label}
                  <b className={styles.statValue}>{stat.value}</b>
                </span>
              ))}
            </div>
            <div className={styles.timeline}>
              {HISTORY_ENTRIES.map((entry) => (
                <HistoryRow key={`${entry.time}-${entry.title}`} entry={entry} />
              ))}
            </div>
            <div className={styles.emptyNote}>{HISTORY_EMPTY_NOTE}</div>
          </>
        ) : (
          `${SEGMENTS.find((seg) => seg.key === segment)?.label} segment`
        )}
      </div>
    </div>
  );
}

export default ActivityTab;
