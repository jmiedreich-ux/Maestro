import type { ThreadEntry } from "./fixtures";
import { labelForState } from "./realEventSynthesis";

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
  stateLine: string;
}

export function deriveRealHeaderState(packetId: string, entries: ThreadEntry[]): RealHeaderState {
  const latestWithState = [...entries].reverse().find((entry) => entry.afterState !== undefined);
  return {
    eyebrow: packetId.replace(/^packet-/, ""),
    title: latestWithState ? labelForState(latestWithState.afterState as string) : "Waiting for events",
    stateLine:
      entries.length === 0
        ? "No real events recorded yet"
        : `${entries.length} real event${entries.length === 1 ? "" : "s"} recorded`,
  };
}
