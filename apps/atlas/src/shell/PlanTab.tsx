import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { GATE_CRITERIA } from "../gate/fixtures";
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
 * `GATE_CRITERIA`). The gate row is also a real `<button>` with no
 * `onClick` — opening the gate's own bottom sheet is separate, future
 * work (roadmap item 36's own remaining scope, a future `F4B`-style
 * candidate), matching this program's own established "options
 * rendered but inert until wired" convention (`AgentsRoster`'s own
 * "Open thread" button).
 *
 * The stats line's own real counts (`DONE_COUNT`/`RUN_COUNT`/
 * `AHEAD_COUNT`) are derived directly from `PLAN_PACKETS`'s own `state`
 * field, not separately hand-typed numbers — matching this program's
 * own C7/`GateHeader` single-state-source discipline. `AHEAD_COUNT`
 * is `PLAN_PACKETS.length` minus the other two, not its own filter, so
 * the three real counts can never silently fail to sum to the real
 * total.
 */
export function PlanTab() {
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
      <button type="button" className={styles.gateRow}>
        <span className={styles.gateDot} aria-hidden="true" />
        <span className={styles.gateLabel}>M1-B gate</span>
        <span className={styles.gateMeta}>
          {GATE_MET_COUNT} of {GATE_CRITERIA.length} met ›
        </span>
      </button>
    </div>
  );
}

export default PlanTab;
