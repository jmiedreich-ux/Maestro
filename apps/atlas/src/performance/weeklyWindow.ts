/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * weekly-window strip markup — pure reporting content, no persona, no
 * fictional agent. `unattributedPercent` is the one figure the
 * reference file itself renders in amber (matching this program's own
 * established amber-means-estimate/attention convention); every other
 * figure is ink.
 */
export interface WeeklyWindow {
  reconciledPercent: string;
  coarsePercent: string;
  unattributedPercent: string;
  observedChangePercent: string;
  meta: string;
  caption: string;
}

export const WEEKLY_WINDOW: WeeklyWindow = {
  reconciledPercent: "61%",
  coarsePercent: "14%",
  unattributedPercent: "5%",
  observedChangePercent: "80%",
  meta: "observed 15:02 · resets Mon 00:00",
  caption: "Local Qwen is shown as capacity and time only — it is not subtracted from this window.",
};
