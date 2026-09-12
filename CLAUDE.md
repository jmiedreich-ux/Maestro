# Maestro — working rules

Read and follow `AGENTS.md` before every repository task. Its repository-wide rules apply to every agent and override older workflow instructions when they conflict.

## Response style — a hard rule, not a preference

**Default: under 150 words. Plain prose. No headers, no bullet lists, no bold
labels, no tables.** Just say the thing.

This is the default for every reply. Break it only when the user asks for a
document, a plan, a comparison, or explicitly asks for detail — and when in
doubt, give the short answer and offer the long one.

Specifically:
- Answer the question asked. Do not add context the user did not ask for.
- One recommendation, not a survey of options.
- No preamble ("Great question", "Let me explain"), no summary of what you just
  did, no restating the user's question back at them.
- Do not enumerate your reasoning. Give the conclusion; give the reason only if
  it changes what the user would do.
- If something is wrong, say what and why in a sentence or two. Do not build a
  case.
- Never end with a list of what you could do next.

Writing a long structured reply because the material feels important is the
failure mode. The user has asked for short answers repeatedly across multiple
sessions — including in M0-D18 §11, where it is recorded as a standing Owner
instruction — and it has been overridden every time. Length is not thoroughness.

**Documents are the exception, and only in files.** Planning records, decision
records and reports are written to files and can be as long as they need to be.
The reply that accompanies them is still under 150 words.

## Verify before asserting

M0-D18 §11 carries a standing instruction: *"there is way to much assumptions
being made"*. Check the code before stating what exists. This has produced real
errors — including a claim that no model had ever completed a Maestro packet
when one had, and a charge that an Owner-approved record was factually wrong on
the strength of a line that had not been read.

Be careful with absolutes. "Never", "only", "no X anywhere", "zero", "cannot"
are where overstatement hides. Grep before writing one.

## Planning authority

`docs/planning/decisions/m0-d18-real-wiring-audit-authority-and-architect-loop.md`
governs all milestone planning; `m0-d19-next-milestone-round.md` is the current
plan built from it. Read both before scoping anything.

Keep D18's provenance convention in anything extending it: `[OWNER]` for the
Owner's verbatim words, `[PROPOSAL]` for inference, `[OPEN]` for unresolved,
`[FINDING]` for facts verified against code with file and line. Do not file
inference as Owner authority — a fidelity review has caught that twice.
