# Remove the four work-disposition choices

## Outcome and result
Re-registration happens only when no work is happening in the project. When the architect determines that re-registration is needed, the service blocks the affected packets, tells the Owner, and the Owner stops or pauses Execution with the existing pause and stop actions. There is no separate Owner decision. The behavior is described in [work when re-registration is needed](../architecture.md#work-when-re-registration-is-needed).

## Existing implementation assessment
The service and terminal still implement the old four choices (continue unaffected work, finish safe work, stop affected or all work, finish current work and prioritize replanning) as the Owner decision target `execution_work_disposition`. The architect's determination still carries a recommended disposition.

## Work still to do
- Remove the `execution_work_disposition` decision target, the four choices and the recommended-disposition field from the service (`services/maestro/maestro/service/execution.py`, `execution_support.py`, `architecture.py`), the terminal (`services/maestro/maestro/terminal/execution.py`) and the `execution@1` schema.
- Make a re-registration determination block the affected packets and their dependants and raise an attention item for the Owner, with no pending decision.
- Update the tests: `tests/maestro/service/test_execution_determination.py`, `test_execution_gaps.py` and `tests/maestro/terminal/test_terminal_execution_gaps.py`.
- Re-prove the blank Result in [the Execution outcomes](../outcomes/execution.md) for "Findings reach a process limit or need replanning" with a real run.
