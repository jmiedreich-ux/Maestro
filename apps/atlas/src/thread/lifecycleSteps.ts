import type { ThreadEntry } from "./fixtures";
import { labelForState } from "./realEventSynthesis";

/**
 * Real internal states a packet passes through before any real work
 * begins (materialize -> queued -> unblocked -> dispatchable). These
 * are mechanically real but not narratively interesting on their own
 * — a user cares that the packet reached "ready to start", not that
 * it took 3 separate internal gate-checks to get there. Anything past
 * this set (Leased/Running/NeedsReplan/MergeReady/Cancelled) is a real
 * milestone worth its own message.
 */
const PRE_WORK_STATES = new Set(["Planned", "Waiting", "Ready", "Dispatchable"]);

export function isPreWorkEntry(entry: ThreadEntry): boolean {
  return entry.afterState !== undefined && PRE_WORK_STATES.has(entry.afterState);
}

/**
 * The furthest real pre-work states reached, oldest first, as plain
 * labels — deduped when consecutive real states share one label (e.g.
 * Ready/Dispatchable both read "Ready to start"). `entries` must
 * already be oldest-first.
 */
export function derivePreWorkTrail(entries: ThreadEntry[]): string[] {
  const trail: string[] = [];
  for (const entry of entries) {
    if (!isPreWorkEntry(entry)) continue;
    const label = labelForState(entry.afterState as string);
    if (trail[trail.length - 1] !== label) trail.push(label);
  }
  return trail;
}
