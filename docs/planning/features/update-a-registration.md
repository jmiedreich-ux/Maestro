# Update a registration through the service and CLI

## Outcome and result
Closes the gap for [Update a registration without losing approved history](../../outcomes/registration.md#update-a-registration-without-losing-approved-history): the Owner reruns registration for an idle registered project, sees what differs from the active version, and either confirms the exact new candidate or cancels, with the earlier version kept in both cases.

## Existing implementation assessment
Reused as built: the whole registration process (`service/registration.py`), the atomic reservation table with its `re_registration` purpose and idle check (`service/reservations.py`), package building and versioned folders (`service/registration_package.py`, which already accepted a previous-version reference), the confirmation receipt and index, and the terminal registration commands. Gap found: `registration.start` refused any project that was already registered; the idle check ignored agent runs and external writes; nothing compared a candidate with the active version; activation and receipts assumed a first registration; cancelling a re-registration would have left the project Not registered; and no service operation refused new work for a reserved project.

## Implementation notes
- `registration.start` accepts a registered project: overview path, publication branch and both agent choices are inherited unless supplied, the project shows "Registered, updating registration", and the project is reserved for re-registration.
- The re-registration idle check also names unfinished agent runs and unresolved external writes; `refuse_other_starts` makes agent run starts for a reserved project fail unless they belong to the reserving activity.
- The candidate is compared with the active package (added, changed, removed records, scope, completion requirement, profile change, reasons from decisions and findings), shown in the registration view and activity messages before confirmation.
- Confirmation replaces the active version, links the receipt to the previous receipt, and keeps earlier versions in GitHub; cancellation restores the earlier status and releases the reservation.

## Verification
Unit tests in `tests/maestro/service/test_registration.py` and `test_reservations.py`; real proof on a disposable service under `var/qa/registration-live/update-evidence.json`.
