# One Packet, Every Phase
Worked example using the real CG-M1-03.5 layout packet and its actual failure.

---

## Phase 1 — Author the packet (Codex, once)

What exists at this point: the milestone doc's acceptance criteria, in human language.

> **CG-M1-03.5 — gallery layout**
> Files you may change: `apps/lab/src/GalleryLayout.tsx`, `apps/lab/src/gallery.css`
> Do not change any other file.
> Use the motion duration tokens from `tokens.css`. Do not write literal duration values.
> `apps/lab/src/GalleryApp.tsx` already exists and already renders the providers. Do not modify it.
> Run `npm run build` and `npm exec tsc -- --noEmit`. Both must pass.
> Commit with message `CG-M1-03.5 gallery layout`.

Output of this phase: **the packet text.** Nothing runs yet.

---

## Phase 2 — Compile the packet (Codex, once)

Same source, three machine-readable artifacts derived from it.

**Allowed paths:**
```
ALLOWED_PATHS=("apps/lab/src/GalleryLayout.tsx" "apps/lab/src/gallery.css")
```

**Permission config** — OpenCode denies writes outside those two paths, so scope creep can't happen rather than being caught after.

**Checks:**
```bash
check_invariants() {
  # from the invariants list, plus this packet's own rules
  grep -nE '[0-9]+(ms|s)\b' apps/lab/src/gallery.css && fail "literal duration; use tokens.css"
  grep -q 'var(--motion-' apps/lab/src/gallery.css || fail "no motion token referenced"
}
```

Output of this phase: **allowed paths, permission config, checker.** Still nothing runs.

---

## Phase 3 — Dispatch (wrapper)

- `git worktree add` a fresh tree at the base commit
- `ollama ps` — refuse to start if context is under 65536
- Preflight ping — 5-second "reply OK"; abort if the model doesn't respond with a tool-capable reply
- `opencode run -m qwen3.6:27b "<packet text>"`
- Timer starts

Output: **a finished run, or a timeout kill.**

---

## Phase 4 — Grade (wrapper)

| Check | Command | Result |
| --- | --- | --- |
| Scope | `git diff --name-only <base>` vs ALLOWED_PATHS | pass |
| Build | `npm run build` | pass |
| Types | `npm exec tsc -- --noEmit` | pass |
| Commit | `git rev-parse HEAD` ≠ base | pass |
| Invariants | `check_invariants` | **FAIL — literal duration in gallery.css** |

Output: **a verdict, and if failed, the one failing line.**

---

## Phase 5 — Rework (wrapper, one round only)

Sends back exactly the failed check, nothing else:

> The previous attempt failed this check — fix only this, don't touch anything else:
> `invariants: FAILED — literal duration in gallery.css; use tokens from tokens.css`

Re-grade. Pass → Phase 6. Fail again → escalate to Codex.

Output: **accepted, or escalated.**

---

## Phase 6 — Record (wrapper appends the row)

The existing columns, plus the three new ones:

| Field | Value |
| --- | --- |
| Packet | CG-M1-03.5 |
| Model | `qwen3.6:27b` @ 65536 |
| Elapsed | 166.4 s |
| Rework — self-corrected | 0 |
| Rework — coordinator-issued | 1 |
| **What the packet said** | "Use the motion duration tokens from `tokens.css`. Do not write literal duration values." |
| **What the model did** | Wrote literal `200ms` / `0ms` values in `gallery.css` |
| **Rule-catchable?** | Yes — grep |
| Outcome | accepted |

Output: **a row that says what to change**, not just what happened.

---

## Phase 7 — Update the invariants list (Codex, after the milestone)

Reading Phase 6: packet *did* state the rule, model missed it anyway, and it's grep-catchable. So it goes permanent.

`docs/features/control-gallery/invariants.md`:

```
| Rule | First seen | Enforced by |
| --- | --- | --- |
| No duplicate `#root`; index.html already has one | CG-M1-03.1 | grep |
| Preserve pre-existing motion classes | CG-M1-03.4 | grep + source review |
| Motion durations use tokens.css, never literals | CG-M1-03.5 | grep |
| `<legend>` contents must be valid | CG-M1-03.6 | lint |
| Focus assertions must match Foundry's ring (3px solid, 4px offset) | CG-M1-04 | judgment — Codex only |
```

Output: **the list Phase 2 reads next time.** Every future packet gets these checks for free, without anyone remembering to write them.

---

## The loop

Phase 7 feeds Phase 2. Each milestone's failures become the next milestone's automatic checks, so the same mistake can only cost you once. The bottom row of the invariants list — the judgment ones — is the only part that stays with Codex permanently.
