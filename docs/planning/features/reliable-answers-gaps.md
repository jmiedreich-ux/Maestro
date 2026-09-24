# Close the gaps in answering project questions

## Outcome and result
Closes the gaps found when the installed terminal answered real service-held questions, for [Reliable project questions and answers](../../outcomes/cli.md#reliable-project-questions-and-answers): the Owner answers the intended question once and sees a durable receipt and any correction needed.

## Existing implementation assessment
The service (`service/questions.py`: publish, answer, saved-before-acknowledged, repeated-request recognition, follow-up linking, delivery records) and the terminal (`terminal/questions.py`: open, choose, submit, reconcile, retry, status) were already built and unit-tested. Reused as they stand. Driving them on a real pty against a real service copy, with a proxy that drops one acknowledgment, found three gaps:

- The status line after a question (for example the "Delivery not confirmed" explanation) was cut off at the terminal width instead of wrapped.
- A stale, replaced or cancelled question showed only "the question version is stale" and did not offer the replacement.
- The error banner from a failed answer stayed after switching to another project.

## Implementation notes
Code in `terminal/rendering.py`, `terminal/questions.py` and `terminal/workspace.py`; tests in `tests/maestro/terminal/test_terminal_help_runtime.py`. Evidence script `var/qa/ws-live/q1.py`, results `q1-evidence.json`. Results are in the outcome's Result column.
