import type { ThreadEntry } from "./fixtures";

/**
 * The README's own single-state-source rule (verbatim): "Picking an
 * option appends resolution messages to the thread and updates the
 * header summary, session label, hero card, boundary timestamps, and
 * 'what happens next' together — they must all read from one state
 * value, not be set independently." This is that one function for the
 * packet-thread header, extended by F1 to also cover the mobile hero
 * card and "what happens next" panel — the desktop `PacketHeader.tsx`
 * (this function's original, only consumer) and the new mobile
 * `NowTab.tsx` both call it, so neither surface re-derives its own copy.
 *
 * `eyebrow` and `title` are `PACKETS['A.2']`'s own real `id`/`title`
 * (`Atlas Explorations.dc.html`, verbatim), minus the mockup's own
 * "issue #970" segment — checked directly against this real
 * repository (`gh issue view 970` — no such issue exists here), so it
 * is not real, verifiable content for this project and is excluded,
 * not transcribed.
 *
 * The derivation below only implements the one real trajectory
 * `PACKET_A2_ENTRIES` (C1, frozen) actually contains: escalated,
 * waiting on the owner. The reference file's own "not blocked" values
 * depend entirely on simulated, interactive UI state (a `decided`/
 * `running` toggle) with no backing real fixture — inventing plausible
 * numbers for that branch would violate this program's own
 * fixture-content discipline (never invent product content). A future
 * slice with a second real scenario should extend this function then;
 * until it exists, the non-blocked branch reports `"unavailable"`,
 * per this project's own real M0-D14 reporting-honesty convention
 * (reported beats estimated; an unsupported field reads `unavailable`,
 * never a guess).
 *
 * `progressPercent` (added by F1) is the one genuinely new derived
 * value: `PACKET_A2_ENTRIES[1]`'s own real `plan.steps` array (present
 * in the real reference data, unused by any slice before F1) has 2
 * "done" of 5 real steps — a real, non-invented 40%, not the
 * reference file's own fabricated "41%" (`Atlas Mobile.dc.html`'s
 * `pct: ... blocked ? '41%' ...` has no real formula behind it — a
 * plausible-looking illustrative number, not derivable from any real
 * fixture field, so it is not reused here). `boundaryBegin`/
 * `boundaryHeld` are likewise real: the first real "wk" (Terra) entry's
 * own timestamp, and the entry where Terra reports being blocked.
 */
export interface PacketHeaderState {
  eyebrow: string;
  title: string;
  isBlocked: boolean;
  stateLine: string;
  lastReport: string;
  blocker: string;
  nextLabel: string;
  next: string;
  headline: string;
  subline: string;
  progressPercent: number | "unavailable";
  boundaryBegin: string;
  boundaryHeld: string;
  nextPanelHeading: string;
  nextPanelText: string;
}

export function derivePacketHeaderState(entries: ThreadEntry[]): PacketHeaderState {
  const escalation = entries.find((entry) => entry.escalate === true);
  const isBlocked = escalation !== undefined;
  const lastImplementorReport = [...entries].reverse().find((entry) => entry.k === "wk");
  const firstImplementorEntry = entries.find((entry) => entry.k === "wk");
  const planEntry = [...entries].reverse().find((entry) => entry.plan !== undefined);
  const progressPercent =
    planEntry?.plan !== undefined
      ? Math.round(
          (planEntry.plan.steps.filter((step) => step.status === "done").length /
            planEntry.plan.steps.length) *
            100,
        )
      : "unavailable";
  return {
    eyebrow: "m1-a · a.2",
    title: "Add output-specific Runtime Package creation",
    isBlocked,
    stateLine: isBlocked
      ? "Terra is blocked and waiting on your decision"
      : "unavailable",
    lastReport: lastImplementorReport?.time ?? "unavailable",
    blocker: isBlocked ? "theme version for theme-free outputs" : "none",
    nextLabel: isBlocked ? "Waiting on you" : "unavailable",
    next: isBlocked ? "41m" : "unavailable",
    headline: isBlocked ? "Blocked" : "unavailable",
    subline: isBlocked ? "Escalated to you · worktree held" : "unavailable",
    progressPercent: isBlocked ? progressPercent : "unavailable",
    boundaryBegin: isBlocked ? (firstImplementorEntry?.time ?? "unavailable") : "unavailable",
    boundaryHeld: isBlocked ? (lastImplementorReport?.time ?? "unavailable") : "unavailable",
    nextPanelHeading: "what happens next",
    nextPanelText: isBlocked
      ? "Nothing is expected from Terra until you answer — its worktree stays held while the packet is blocked."
      : "unavailable",
  };
}
