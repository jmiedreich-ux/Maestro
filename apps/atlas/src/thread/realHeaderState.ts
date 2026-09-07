import type { ThreadEntry } from "./fixtures";
import { labelForState, splitEntryText } from "./realEventSynthesis";

/**
 * A real-data header state — distinct from `headerState.ts`'s own
 * `derivePacketHeaderState`, which only implements the one fixture
 * trajectory (`PACKET_A2_ENTRIES`'s escalation story) and has no real
 * field to derive a status from real backend events. Rather than show
 * that fixture's own unrelated title next to a different real packet's
 * events, or report "unavailable" for a status this program actually
 * knows, this reads the one real, current fact every packet event
 * carries: its own latest recorded state.
 */
export interface RealHeaderState {
  eyebrow: string;
  title: string;
  /**
   * The real reason for the packet's single most recent event (e.g.
   * "work started") — a prominent subtitle, separate from `stateLine`,
   * so the header doesn't read as a settled, past state ("Assigned")
   * with no acknowledgment of what actually just happened.
   */
  latestDetail: string | null;
  stateLine: string;
}

export function deriveRealHeaderState(
  packetId: string,
  entries: ThreadEntry[],
  // The packet's own real, authoritative current state, read directly
  // from /snapshot/packets (see useRealPacketThread.ts's own doc
  // comment on `packetState` for why this can't be reliably inferred
  // from `entries` alone: a state change from starting/finishing an
  // attempt's execution is recorded under that Attempt's own
  // entity_id, never the packet's). Falls back to inferring from
  // entries only when this hasn't loaded yet.
  authoritativeState: string | null = null,
): RealHeaderState {
  const latestWithState = [...entries].reverse().find((entry) => entry.afterState !== undefined);
  const currentState = authoritativeState ?? latestWithState?.afterState ?? null;
  const latest = entries[entries.length - 1];
  const latestDetail = latest ? splitEntryText(latest.text).detail : null;
  return {
    eyebrow: packetId.replace(/^packet-/, ""),
    title: currentState ? labelForState(currentState) : "Waiting for events",
    latestDetail,
    stateLine:
      entries.length === 0
        ? "No real events recorded yet"
        : `${entries.length} real event${entries.length === 1 ? "" : "s"} recorded`,
  };
}
