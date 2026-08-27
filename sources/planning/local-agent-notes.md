# Local-Model Coding Agent — Working Notes
Foundry / Control Gallery. Nothing here is in the repo yet — only Codex's actual test results are committed.

## Delegation flow
Codex starts the milestone, splits it into packets, assigns each to a local model or itself, and delegates. A packet either passes the wrapper's checks and gets accepted, fails once and gets one rework message, or fails twice and escalates to Codex.

## Enforcement wrapper
Runs the local model on a packet, then grades it mechanically instead of Codex checking by hand:
- Scope — `git diff --name-only` against the packet's allowed paths only
- Build — `npm run build` (add `npm exec tsc -- --noEmit` — the 03.4 gap: an unintegrated file's type error didn't show up in the build)
- Commit — confirms a commit actually exists, doesn't trust the model's own report
- Invariants — packet-specific checks (e.g. no duplicate `#root`, required providers rendered not just imported)

One rework round: on failure, send the model exactly the failed check. Pass → accepted. Fail again → escalate to Codex.
Example implementation: `enforcement-wrapper.sh`, concrete to CG-M1-03.1.

## Micro-helpers (not yet built)
- **Preflight ping** — 5-second "reply OK" test before spending a real attempt; catches a dead run like Devstral's before it burns a packet
- **Permission lock** — OpenCode agent permissions deny writes outside allowed paths, instead of catching scope creep after
- **Runaway timeout** — kill and escalate past ~150s with no commit
- **Auto-append to performance-reports.md** — wrapper writes its result row directly into the ledger
- **Fingerprint every commit** — stamp `ollama ps` output (model, context, quant) into the commit message or report row
- **Fake-completion detector** — run with `--format json`, check the event stream for an actual `git commit` tool event before believing "committed"
- **Packet linter** — checks the prompt itself: does it name what already exists, use explicit "do not create" wording, spell out exact filenames? The `#root` and import-vs-render failures were both wording triggers
- **Bake-off runner** — one command runs the same packet across N models in fresh worktrees, emits the comparison table
- **Auto-worktree per attempt** — `git worktree add` from the base commit per run, so attempts never contaminate each other
- **Context hard gate** — wrapper refuses to start if `ollama ps` shows context under 65536 (it's already reverted once)
- **Unattended lock** — detached tmux, stdin closed, so a timed run can't be interrupted by typing into it
- **Session export archive** — `opencode export` the session JSON next to each report row, so a failure can be reread without rerunning it

## Deep / llama.cpp-level ideas
Means running llama.cpp directly instead of through Ollama.
- **Grammar-constrained tool calls** — GBNF grammar masks invalid tokens at sampling time, so a malformed or fake tool call becomes impossible rather than caught after
- **Custom sampler for scope enforcement** — C++ sampler chain addition that masks any token spelling a path outside `ALLOWED_PATHS` while a tool call is being generated; out-of-scope edits can't be generated at all
- **KV-cache prefix snapshot** — snapshot the KV state once after the shared system prompt/AGENTS.md/packet prefix, restore it per run; skips re-reading the prefix on every rework round or bake-off model
- Limit: these enforce format and scope, not judgment — the duplicate `#root` was a semantic choice, not a syntax error, and stays with the wrapper

## Systems-level ideas
- **Best-of-N** — run the same packet in parallel worktrees, take the first pass; fixes variance (stochastic misses), not bias (a wording-driven mistake repeats regardless of N)
- **Wrapper as data collector** — every run is a labeled example (packet, diff, pass/fail per check); enough of them is a fine-tuning set on this repo's actual conventions (QLoRA via Unsloth fits the card)
- **Flip roles** — Codex writes `check_invariants` from the acceptance criteria once; the local model implements against it as many times as needed
- **Packet compiler** — one tool turns `m1.md` packets into: the local prompt (prohibitions stated concretely), the `ALLOWED_PATHS` array, the OpenCode permission config, and the checker stub. Routes each rule to the cheapest layer that can enforce it — lexical to the sampler mask, structural to grep/build, semantic to a judge
- **Second model as judge** — a different model family judges what can't be grepped (grammar-forced yes/no + reason); Glimmer was built for this
- **Model behavior debugger** — session export + KV snapshots at each tool-call boundary lets you replay a failed run, fork at the exact decision point, swap the prompt, and see if the decision changes

## Where things stand
- Qwen 3.6 27B is the working local model: passed CG-M1-03.1 twice (including the unmodified original prompt), then completed 6 real production packets — all accepted, none by hand, 11.7 minutes total. 2 of 6 passed first try; the other 4 needed one correction each.
- Every correction so far was rule-catchable, not a judgment call: uncommitted state, literal values instead of tokens, invalid markup, missing custom focus style — exactly what the packet linter and stronger invariant checks are for.
- Browser tests needed two rounds plus coordinator strengthening — the packet closest to integration-shaped, and the weakest result. Consistent with the CG-M1-03.4 finding: it holds a stated boundary well, doesn't yet reason about what "done" means beyond the literal ask.
- Next: Muse Glimmer 30B on the same six packets, same gates — watching specifically for whether it self-corrects a failed tool call without a coordinator-issued rework message.
