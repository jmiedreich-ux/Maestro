import type { ThreadEntry } from "./fixtures";

/**
 * The README's own single-state-source rule (verbatim): "Picking an
 * option appends resolution messages to the thread and updates the
 * header summary, session label, hero card, boundary timestamps, and
 * 'what happens next' together — they must all read from one state
 * value, not be set independently." This is that one function for the
 * packet-thread header (the hero card and mobile "what happens next"
 * panel are separate, later Wave F work that should call this same
 * function once it's extended to those surfaces, not re-derive their
 * own copy of this logic).
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
}

export function derivePacketHeaderState(entries: ThreadEntry[]): PacketHeaderState {
  const escalation = entries.find((entry) => entry.escalate === true);
  const isBlocked = escalation !== undefined;
  const lastImplementorReport = [...entries].reverse().find((entry) => entry.k === "wk");
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
  };
}
