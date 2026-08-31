# Non-Material Completion Delegation — 2026-08-31

## Trigger

Alpha-03 produced committed implementation candidate
`e3929c46882dbd0512bac377bdef1440d4e17cff`. Its full independent review
returned `REQUEST_CHANGES`. The one M0-D05 targeted correction produced
`f21e4a2ff25cead8b972b4433da33f0e9910efc5`.

Targeted follow-up review passed all required commands but returned
`REQUEST_CHANGES` because a conflicting `[]` value remained accepted for the
required non-empty `authority.architecture_paths` array. The same schema class
also governs `authority.plan_paths`. Malformed input could therefore reach
claim and SQLite mutation instead of failing before mutation.

Reported passing evidence was:

- 11 Alpha-01 tests;
- 7 Alpha-02 tests;
- 56 Alpha-03 tests;
- the required CLI result at `AwaitingReview` with complete evidence; and
- `git diff --check`.

No implementation PR or merge was created. No external access, real-project
action, Alpha-04 implementation, or additional correction occurred.

## Owner clarification

The Owner clarified that a coding completion which preserves the already
approved software direction does not require a new Owner approval merely
because the current packet exhausted its correction allowance.

The correction cap remains a hard stop for the active packet. It prevents
unbounded retry and forces a fresh architectural classification. After that
stop, Architecture may issue one narrow superseding completion packet without
returning to the Owner when all of the following are true:

1. the required behavior and quality boundary are already explicit and
   approved;
2. the completion does not change product direction, architecture, public
   contract, security/data boundary, external access, dependency, model route,
   release authority, or accepted risk;
3. implementation paths and proof remain a strict subset of the existing
   approved packet;
4. the exact failed candidate, remaining finding, and prior evidence are
   recorded;
5. the superseding packet receives fresh full Decision Fidelity Review; and
6. the final cumulative implementation result receives fresh full independent
   implementation review.

The superseding packet receives the normal one targeted-correction allowance.
If it also exhausts that allowance, requires broader work, or reveals a new
material decision, work stops for Owner direction.

This delegation does not authorize Architecture to implement, independently
approve, dispatch, merge, accept, or change operational state. The Coordinator
may dispatch only after the superseding packet is approved and merged under
the established gates. Existing Owner acceptance and merge policy remains
unchanged.

## Review closure and 90/10 operating boundary

The Owner further clarified that reviewers have historically continued finding
something else to criticize and that Maestro must know when the approved work
is good enough. The Owner does not want to supervise routine implementation and
review decisions. The intended operating split is approximately 90% delegated
to Architecture/Maestro and 10% reserved for genuine Owner judgment.

Passing the packet's named sufficient proof is enough unless a reviewer
demonstrates a concrete violation of an accepted decision, packet criterion,
or bounded quality contract. Preferences, hypothetical hardening, alternative
designs, refactors, and stronger proof standards are non-blocking observations.
A blocking finding must cite the exact governing criterion, show reproducible
evidence of failure, explain the material consequence, and identify the
smallest in-scope correction.

Architecture owns routine classification of whether a review observation is
inside the approved contract. This does not let Architecture approve its own
implementation or dismiss a demonstrated contract violation. It prevents a
reviewer from silently enlarging the work. Only a material direction, risk,
security/data/external-authority, irreversible, spending-policy, or repeatedly
failed architecture question returns to the Owner.

## Desired unattended day

The Owner's target experience is to set the day's outcomes and boundaries in
the morning, leave for their own job, and return to development that is
complete, merge-ready, actively progressing, or blocked only on a genuinely
material decision. Maestro should continue other independent approved work
when one item is blocked rather than idling the whole day.

When Owner input is genuinely required, Slack is the desired contact channel.
The question must include the facts, options, Architecture recommendation,
impact, response deadline, and safe action if no answer arrives. The affected
work stops without assuming approval; unrelated eligible work continues.
Slack delivery and replies must be durable, rate-limited, tied to a decision
ID, restricted to an approved Owner identity/destination, and contain no
secrets or raw agent traces. This direction does not configure or contact
Slack now.
