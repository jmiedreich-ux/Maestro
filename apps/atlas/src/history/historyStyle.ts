import { colors } from "../tokens";
import type { HistoryKind } from "./fixtures";

/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `HIST_STYLE` map: `[tagBg, tagColor, dotColor, urgent]` per kind.
 * Every value below is a real B2 token except `report`'s dot color
 * (`#CFC6D6`): that exact hex also happens to equal `colors.navText`,
 * which — per this program's own exhaustively-checked precedent from
 * the Gate-criteria slice — has no real consumer anywhere in this
 * codebase and is scoped to the dark nav sidebar by name and grouping,
 * not a general-purpose light-mode dot color. It is disclosed as a
 * literal here too, not reused from that unrelated token.
 */
export interface HistoryKindStyle {
  tagBg: string;
  tagColor: string;
  dotColor: string;
  urgent: boolean;
}

export const HISTORY_KIND_STYLE: Record<HistoryKind, HistoryKindStyle> = {
  dispatch: { tagBg: colors.neutralChip, tagColor: colors.neutralChipText, dotColor: colors.borderDashed[2], urgent: false },
  handoff: { tagBg: colors.accentWash[0], tagColor: colors.accentHover, dotColor: colors.accentLight, urgent: false },
  review: { tagBg: colors.reviewWash, tagColor: colors.reviewText, dotColor: colors.review, urgent: false },
  correction: { tagBg: colors.reviewWash, tagColor: colors.reviewText, dotColor: colors.review, urgent: false },
  accepted: { tagBg: colors.successWash, tagColor: colors.successText, dotColor: colors.success, urgent: false },
  report: { tagBg: colors.neutralChip, tagColor: colors.inkSecondary, dotColor: "#CFC6D6", urgent: false },
  blocked: { tagBg: colors.warningChip, tagColor: colors.warningText, dotColor: colors.warning, urgent: true },
  escalated: { tagBg: colors.warningChip, tagColor: colors.warningText, dotColor: colors.warning, urgent: true },
};
