import { colors } from "../tokens";
import type { AgentStyleKey } from "./agents";

/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `AG_STYLE` map (`[avBg, avColor, stateColor, barColor, border]` per
 * style key). Every value is a real B2 token except two disclosed
 * literals, checked directly against `colors.ts`: `run`'s own border
 * (`#E0DAF2`) and `rev`'s own border (`#EFE0D8`) — neither matches any
 * real token property (checked against `colors.borderStrong`,
 * `colors.borderDashed`, `colors.accentWash`, and every other color
 * family directly, not assumed). `wait`'s bar color (`#CFC6D6`) does
 * match a real token, `colors.navText` — the same coincidental-match,
 * no-nav-consumer literal this program's own History-timeline slice
 * already disclosed and used the same way (checked again here
 * independently, not copied from that disclosure).
 */
export interface AgentStyle {
  avBg: string;
  avColor: string;
  stateColor: string;
  barColor: string;
  border: string;
}

export const AGENT_STYLE: Record<AgentStyleKey, AgentStyle> = {
  run: {
    avBg: colors.accentWash[0],
    avColor: colors.accentHover,
    stateColor: colors.accent,
    barColor: colors.accentLight,
    border: "#E0DAF2",
  },
  wait: {
    avBg: colors.neutralChip,
    avColor: colors.neutralChipText,
    stateColor: colors.inkMuted,
    barColor: colors.navText,
    border: colors.border,
  },
  rev: {
    avBg: colors.reviewWash,
    avColor: colors.reviewText,
    stateColor: colors.reviewText,
    barColor: colors.review,
    border: "#EFE0D8",
  },
  rule: {
    avBg: colors.accentWash[1],
    avColor: colors.accentDeepest,
    stateColor: colors.accentHover,
    barColor: colors.accent,
    border: colors.borderStrong[1],
  },
};
