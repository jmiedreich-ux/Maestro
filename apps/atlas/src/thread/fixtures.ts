export type EntryRoleKey = "co" | "wk" | "rv" | "ok" | "by" | "ow" | "ar";

export interface ThreadPlanStep {
  text: string;
  status: "done" | "now" | "open";
}

export interface ThreadPlan {
  name: string;
  summary: string;
  steps: ThreadPlanStep[];
}

export interface ThreadEntry {
  k: EntryRoleKey;
  who: string;
  text: string;
  time: string;
  // Present in the real reference data; not yet rendered by any slice.
  plan?: ThreadPlan;
  cadence?: boolean;
  escalate?: boolean;
  closure?: string;
}

/**
 * Transcribed verbatim from Atlas Explorations.dc.html's real
 * `ENTRIES['A.2']` array — the reference app's own default-selected
 * packet's thread. Do not edit a value here without re-checking that
 * file; this is fixture content, not this program's own prose.
 */
export const PACKET_A2_ENTRIES: ThreadEntry[] = [
  {
    k: "co",
    who: "Coordinator",
    text: "Terra, base is 9d3e1a2. You can write one Runtime file and one Runtime test. One correction allowed, and you have 60 minutes before I expect a response.",
    time: "13:49",
  },
  {
    k: "wk",
    who: "Terra",
    text: "Base verified, worktree clean. 200k of context available, no pressure.",
    time: "13:51",
    plan: {
      name: "Terra's task list",
      summary: "2 complete · 1 active · 2 open",
      steps: [
        { text: "Read the frozen-presentation contract from A.1", status: "done" },
        { text: "Derive the per-output Runtime shape without importing UI", status: "done" },
        { text: "Implement RuntimePackageBuilder and its fixture", status: "now" },
        { text: "Focused tests against local fixture data", status: "open" },
        { text: "Hand off for validate-only integration", status: "open" },
      ],
    },
  },
  {
    k: "co",
    who: "Coordinator",
    text: "Status check, once: plan, current step, blocker, and an ETA or unknown.",
    time: "14:19",
  },
  {
    k: "wk",
    who: "Terra",
    text: "Step 3 of 5, building the Runtime Package. Writing RuntimePackageBuilder now. No blocker. ETA unknown.",
    time: "14:30",
    cadence: true,
  },
  {
    k: "wk",
    who: "Terra",
    text: "Blocked. Outputs with no theme still need a theme version, and the A.1 contract rejects an empty one. I read the contract twice and tried a derived hash — both violate the frozen-presentation rule, so this is not mine to decide.",
    time: "14:52",
  },
  {
    k: "co",
    who: "Coordinator",
    text: "Terra raised this to me first. I can rule on scope, corrections and dispatch — I cannot widen a frozen contract, so this one goes to the owner. Terra holds its worktree meanwhile.",
    time: "14:56",
    escalate: true,
  },
];

/** `AV_NAME` from the reference file — explicit initials by real name. */
export const INITIALS_BY_NAME: Record<string, string> = {
  You: "OW",
  "Architect agent": "AR",
  Sol: "SO",
  Terra: "TE",
  "Claude Opus": "CL",
  Coordinator: "CO",
  Boundary: "15",
};

/** `ROLE_OF` from the reference file — the role label shown next to the name. */
export const ROLE_LABEL: Record<EntryRoleKey, string> = {
  co: "",
  wk: "Implementor",
  rv: "Reviewer",
  ok: "",
  by: "",
  ow: "Owner",
  ar: "Architect · agent",
};
