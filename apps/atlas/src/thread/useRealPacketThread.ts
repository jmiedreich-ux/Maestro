import { useEffect, useState } from "react";
import type { ThreadEntry } from "./fixtures";
import { synthesizeThreadEntry, type RealEvent } from "./realEventSynthesis";

/**
 * M3 E4 — wires PacketThread to real data: a real snapshot fetch
 * (oldest-first, matching how a thread reads) followed by a real live
 * `/stream/events` subscription for anything that happens afterward.
 * Named C2 in m2-atlas-roadmap.md ("packet thread wired to real
 * data"), rescheduled to M3 because A6/A7 (this exact stream/reconnect
 * contract, built in E1/E2) didn't exist yet.
 *
 * Every existing PacketThread caller is unaffected: this hook is opt-in
 * via a real `packetId`, the fixture-driven default path is untouched.
 */

import { readApiBaseUrl } from "../readApiBaseUrl";

export interface UseRealPacketThreadResult {
  entries: ThreadEntry[];
  resyncRequired: boolean;
  /**
   * The packet's own real, authoritative current state (e.g.
   * "Running"), read directly from `/snapshot/packets` — not inferred
   * from the event feed above. A real gap found while wiring this: a
   * state change caused by starting/finishing an attempt's execution
   * is recorded under that Attempt's own entity_id, not the packet's,
   * so it never appears in `entries` at all; inferring "current state"
   * from the last packet-entity event alone silently missed it (a real
   * packet showed a stale "Assigned" status after work had actually
   * started). The packets table itself is the one real source of
   * truth for current state, so read it directly instead.
   */
  packetState: string | null;
}

/**
 * `packetId` of `undefined` (the default fixture-driven rendering path)
 * performs no fetch and opens no stream connection at all — every
 * existing PacketThread caller stays exactly as it was.
 */
export function useRealPacketThread(packetId: string | undefined): UseRealPacketThreadResult {
  const [entries, setEntries] = useState<ThreadEntry[]>([]);
  const [resyncRequired, setResyncRequired] = useState(false);
  const [packetState, setPacketState] = useState<string | null>(null);

  useEffect(() => {
    if (!packetId) return;

    let cancelled = false;
    let eventSource: EventSource | null = null;

    async function loadPacketState() {
      try {
        const response = await fetch(`${readApiBaseUrl()}/snapshot/packets?limit=500`);
        if (!response.ok) return;
        const data = (await response.json()) as { packets?: Array<{ packet_id: string; state: string }> };
        const packet = (data.packets ?? []).find((p) => p.packet_id === packetId);
        if (!cancelled && packet) setPacketState(packet.state);
      } catch {
        // Best-effort only — the header falls back to inferring from
        // entries when this fails.
      }
    }

    async function loadSnapshotThenStream() {
      let lastEventId = 0;
      try {
        const response = await fetch(`${readApiBaseUrl()}/snapshot/events?limit=500`);
        if (response.ok) {
          const data = (await response.json()) as { events?: RealEvent[] };
          const relevant = (data.events ?? [])
            .filter((event) => event.entity_id === packetId)
            // The real snapshot orders newest-first for pagination;
            // a thread reads oldest-first.
            .slice()
            .reverse();
          if (!cancelled) {
            setEntries(relevant.map(synthesizeThreadEntry));
          }
          const allIds = (data.events ?? []).map((event) => event.event_id);
          if (allIds.length > 0) {
            lastEventId = Math.max(...allIds);
          }
        }
      } catch {
        // A real, honest empty state — no fabricated fallback content.
        if (!cancelled) setEntries([]);
      }

      void loadPacketState();
      if (cancelled) return;

      eventSource = new EventSource(`${readApiBaseUrl()}/stream/events?after=${lastEventId}`);
      eventSource.onmessage = (message: MessageEvent<string>) => {
        if (cancelled) return;
        const event = JSON.parse(message.data) as RealEvent;
        // Any live event might have changed this packet's real current
        // state (including one recorded under a different entity, like
        // an Attempt) — re-read the authoritative source rather than
        // only reacting to events whose own entity_id matches.
        void loadPacketState();
        if (event.entity_id !== packetId) return;
        setEntries((previous) => [...previous, synthesizeThreadEntry(event)]);
      };
      eventSource.addEventListener("resync", () => {
        if (!cancelled) setResyncRequired(true);
      });
    }

    void loadSnapshotThenStream();

    return () => {
      cancelled = true;
      eventSource?.close();
    };
  }, [packetId]);

  return { entries, resyncRequired, packetState };
}
