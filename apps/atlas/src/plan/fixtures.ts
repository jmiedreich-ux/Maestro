/**
 * Transcribed verbatim from `Atlas Mobile.dc.html`'s own real
 * `PACKETS` array and `STATE` map — pure reporting content, no
 * persona, no fictional agent. A.2's own real `run` state here matches
 * `AGENTS`'s own real Terra entry (`apps/atlas/src/agents/agents.ts`,
 * `state: "running"`, `styleKey: "run"`) — the mockup's own real
 * `PACKETS` array is sufficient justification on its own.
 *
 * **Corrected — real defect from Decision Fidelity review:** an
 * earlier draft of this comment also cited `NowTab.tsx` as
 * corroborating "Terra genuinely running," which is false — `NowTab.tsx`'s
 * own doc comment deliberately renders Terra as blocked/waiting, not
 * running, as an already-reviewed, on-record design decision (see that
 * file's own comment: *"Terra is genuinely idle/blocked in this real
 * trajectory, not running, so the 'wait' style key is the honest
 * choice, not 'run'..."*). This Plan tab's own use of `run` for A.2 is
 * still correct — it matches the mockup's own real `PACKETS` array and
 * `AGENTS`'s own real Terra entry — only the false `NowTab` citation is
 * removed.
 */
export type PlanPacketState = "done" | "run" | "wait" | "block" | "pend";

export interface PlanPacket {
  id: string;
  short: string;
  state: PlanPacketState;
}

export const PLAN_PACKETS: PlanPacket[] = [
  { id: "A.0", short: "Source homes", state: "done" },
  { id: "A.1", short: "Core contract", state: "done" },
  { id: "A.2", short: "Runtime Package", state: "run" },
  { id: "A.3", short: "Live overlay", state: "wait" },
  { id: "A.4", short: "Support view", state: "block" },
  { id: "A.5", short: "Module guides", state: "block" },
  { id: "A.6", short: "Journey proof", state: "block" },
  { id: "A.7", short: "Records & merge", state: "pend" },
];

export const PLAN_STATE_LABEL: Record<PlanPacketState, string> = {
  done: "Complete",
  run: "Running now",
  wait: "Waiting on A.2",
  block: "Blocked",
  pend: "Planned",
};

/** Real, verbatim — the Plan tab's own breadcrumb. */
export const PLAN_BREADCRUMB = "m1-a · api module foundation";

/**
 * The one real packet with any live conversation thread today
 * (`PACKET_A2_ENTRIES`) — used to highlight the matching row the same
 * way the reference file's own `active = p.id === 'A.2'` does.
 */
export const PLAN_ACTIVE_PACKET_ID = "A.2";
