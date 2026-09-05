/**
 * Same real `A.2` scenario C1/C4 already established (the reference
 * file's own `crashed` system-state toggle is scoped to
 * `cur.id === 'A.2'`) — not a new, invented scenario. Five pieces of
 * the reference file's own copy (the headline, the lede, one fact, one
 * option's body, and the footer) make a claim this program cannot
 * verify or that directly contradicts the real backend state machine,
 * and are corrected here to state only what
 * `services/maestro/maestro/operational_state.py`'s real
 * `finish_attempt_execution` outcome mapping actually does — see this
 * slice's packet contract, Scope section, for the full comparison,
 * numbered as Corrections 1 through 5.
 */
export interface CrashFact {
  k: string;
  v: string;
}

export interface CrashOption {
  title: string;
  cost: string;
  body: string;
}

export interface CrashExample {
  packetId: string;
  age: string;
  headline: string;
  lede: string;
  facts: CrashFact[];
  options: CrashOption[];
  footerNote: string;
}

export const CRASH_EXAMPLE: CrashExample = {
  packetId: "A.2",
  age: "14:58",
  headline: "Terra's attempt failed mid-step. A.2 is routed to NeedsReplan.",
  lede: "The process exited during step 3 of 5 without a handoff. A Failed execution outcome routes the packet to NeedsReplan and releases its lease, per Maestro's real execution-outcome mapping.",
  facts: [
    { k: "Last boundary", v: "14:52" },
    { k: "Step reached", v: "3 of 5" },
    { k: "Outcome", v: "Failed" },
    { k: "Corrections spent", v: "0 of 1" },
  ],
  options: [
    {
      title: "Resume Terra from the last boundary",
      cost: "no correction",
      body: "A fresh Terra process rereads the worktree and the thread, then continues at step 3. Context is rebuilt, not remembered.",
    },
    {
      title: "Re-dispatch A.2 to another implementor",
      cost: "discards ~1h of work",
      body: "Sol takes the packet from base 9d3e1a2. The existing worktree is archived, not merged.",
    },
    {
      title: "Hold A.2 and inspect the worktree",
      cost: "A.3 stays blocked",
      body: "Nothing is dispatched. A.3 stays blocked until this is resolved — read what Terra wrote before deciding.",
    },
  ],
  footerNote: "This is A.2's only recorded attempt. NeedsReplan has no automatic resume in Maestro today — the three choices above describe what a future guarded command would do; none of them dispatch anything yet.",
};
