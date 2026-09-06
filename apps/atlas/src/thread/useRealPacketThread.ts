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
}

/**
 * `packetId` of `undefined` (the default fixture-driven rendering path)
 * performs no fetch and opens no stream connection at all — every
 * existing PacketThread caller stays exactly as it was.
 */
export function useRealPacketThread(packetId: string | undefined): UseRealPacketThreadResult {
  const [entries, setEntries] = useState<ThreadEntry[]>([]);
  const [resyncRequired, setResyncRequired] = useState(false);

  useEffect(() => {
    if (!packetId) return;

    let cancelled = false;
    let eventSource: EventSource | null = null;

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

      if (cancelled) return;

      eventSource = new EventSource(`${readApiBaseUrl()}/stream/events?after=${lastEventId}`);
      eventSource.onmessage = (message: MessageEvent<string>) => {
        if (cancelled) return;
        const event = JSON.parse(message.data) as RealEvent;
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

  return { entries, resyncRequired };
}
