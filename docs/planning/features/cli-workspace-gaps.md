# Close the gaps in the connected CLI workspace

## Outcome and result
Closes the gaps found when the installed terminal was driven against real service-held projects, for [Connected multi-project CLI workspace](../../outcomes/cli.md#connected-multi-project-cli-workspace): the Owner sees current activity and attention for several projects and can navigate them read-only from the keyboard.

## Existing implementation assessment
The terminal (`services/maestro/maestro/terminal`) already had the connection client, project overview and ordering, conversation with earlier-message loading, attention list, findings list, reconnect schedule, credential checks and the minimum-size message, all proved on a disposable copy of the installed service. Reused as it stands. The gaps that needed code:

- `/help` listed three commands and no syntax; it was also erased by the next redraw.
- A lone Escape key waited for two more keys; a resize did not redraw; exit could wait up to 15 s for the event stream.
- Attention for another project had no notice in the conversation.
- Findings could not be opened inline, and details never restored the reading position.
- Activity details did not show runtime readings, and the service did not return the `runtime` object.
- Switching projects kept the previous project's question on screen; a failed command stayed in the input; a missing credential file reported only an exception name.

## Implementation notes
Code in `terminal/main.py`, `workspace.py`, `rendering.py`, `connection.py` and the activity projection in `service/projections.py` (empty `runtime` arrays: no agent run records exist yet, so nothing is invented). Tests in `tests/maestro/terminal/test_terminal_help_runtime.py`. Codex reviewed the diff once; its five findings (resize handler could deadlock, a notice could take focus, Escape followed by a key, runtime status cut off at 80 columns, reading position after closing a finding) were fixed in one correction. Evidence and scripts are in `var/qa/ws-live` (`p1.py`, `p2.py`, `p3.py`). Results are in the outcome's Result column.
