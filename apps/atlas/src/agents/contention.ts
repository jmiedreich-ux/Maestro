/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `CONTENTION` array and `contention` derivation function — pure
 * reporting content, no persona, no fictional agent. `holder` values
 * (`Terra`, `frozen`, `reserved`) are all real/neutral; there is no
 * `Architect agent` in this data at all.
 */
export type ContentionStyleKey = "run" | "wait";

export interface ContentionEntry {
  path: string;
  note: string;
  holder: string;
  styleKey: ContentionStyleKey;
}

export const CONTENTION: ContentionEntry[] = [
  {
    path: "runtime/package.ts",
    note: "Write lock held for the length of A.2.",
    holder: "Terra",
    styleKey: "run",
  },
  {
    path: "core/identity.ts",
    note: "Frozen by the A.1 contract — no packet may write it.",
    holder: "frozen",
    styleKey: "wait",
  },
  {
    path: "overlay/view.tsx",
    note: "Reserved for A.3, released when A.2 is accepted.",
    holder: "reserved",
    styleKey: "wait",
  },
];

export const CONTENTION_CAVEAT =
  "Locks are assigned at dispatch, so two agents can never be told to write the same file. A packet that needs a locked file waits rather than merges.";
