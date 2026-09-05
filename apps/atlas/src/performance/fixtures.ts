/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `pfStats` array and the Performance screen's header lede — this is
 * pure reporting content (no persona, no fictional agent), and its
 * honesty rule is the same real M0-D14 convention already quoted
 * elsewhere in this program's own docs (reported beats estimated, an
 * unsupported field reads `unavailable`, local compute stays separate
 * from the hosted allowance). The lede is split around the one word
 * the reference markup wraps in its own mono `<code>` element
 * (`unavailable`), so the component can reproduce that exact inline
 * styling rather than flattening it into one plain string.
 */
export interface PerformanceStat {
  label: string;
  value: string;
  color: "ink" | "warning";
}

export const PERFORMANCE_LEDE_BEFORE =
  "One record per worker attempt, tied to it from preflight through handoff. Reported counters win over estimates, an unsupported field reads ";
export const PERFORMANCE_LEDE_CODE = "unavailable";
export const PERFORMANCE_LEDE_AFTER =
  " rather than zero, and local compute is never folded into the hosted allowance.";

export const PERFORMANCE_STATS: PerformanceStat[] = [
  { label: "Actions recorded", value: "5", color: "ink" },
  { label: "Billed", value: "$2.27", color: "ink" },
  { label: "Estimated", value: "$0.52", color: "warning" },
  { label: "Hosted time", value: "47m", color: "ink" },
];
