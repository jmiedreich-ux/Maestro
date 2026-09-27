# Registration process

Registration is where Maestro takes in a project's planning documents and confirms exactly what will be built. The workshop does the thinking before it. Registration only checks, records and asks for the Owner's confirmation.

## Who does what

- **The workshop** interprets the plan, asks the Owner about anything missing or contradictory, and gets the independent review. It saves a review record with the exact document versions the review covered. See [the workshop](../SKILL.md).
- **The service** checks the documents against the rules file, checks the review record, pins the exact version, keeps the registration record, and publishes it. It holds the repository credentials.
- **The Owner** confirms the scope, from the CLI.

Registration does not approve the architecture, start development, or break the work into features. It launches no agents of its own.

## Steps

1. **Start.** The Owner names the repository and the path to the project overview, chooses the whole plan or a defined portion, and chooses where the record is published. Only one registration can be active for a project. Registering again is allowed only when the project has no work in progress.
2. **Pin.** The service resolves the chosen version to one exact revision, checks repository access and the destination branch rules, and saves what it found. Everything after this reads that exact revision, never a moving branch.
3. **Check.** The service applies [the rules file](registration-rules.json) to the documents at the pinned revision. It also checks the workshop's review record: it exists, it covers exactly this revision, no document changed afterwards, and its coverage is complete. The service does not review the plan itself; the workshop's independent review is the independent check.
4. **Report.** If every check passes, the Owner moves to confirmation. If a rule fails, registration stops with a plain report of which rule failed, in which document and where. The service saves the report with the exact version it checked. The next workshop session reads that report first and helps fix it, and the changed parts are reviewed again before registering a second time.
5. **Confirm.** The Owner sees the project, the exact revision, the rules version used, the scope, and the differences from the active registration if there is one. Confirmation is a separate, explicit action, and cancelling is always available. A changed or ineligible candidate is rejected with an explanation.
6. **Record.** The service writes the registration record, publishes it to the project's repository, verifies what was written, and only then shows the project as Registered. The previous registration stays active until the new one is confirmed.

## The registration record

The service keeps a small record, not a copy of the plan:

- the pinned revision
- a fingerprint of each document
- the rules version used
- the workshop's review record
- the Owner's confirmation and when it was given

If someone edits a document after confirmation, the fingerprints show it. The exact file layout of the record is settled when this is built.

## The rules file

The rules are in [registration-rules.json](registration-rules.json). The CLI checks for a newer approved version when it starts, tells the Owner one exists, and says which version it used. Only versions marked passed are used, never arbitrary changes on master. Each registration keeps the rules version it started with, so the rules cannot change halfway through.

## Portions

A registration can cover a defined portion of the plan. The chosen boundary, its exclusions and any outside dependencies are recorded and shown for confirmation. An essential dependency cannot simply be left out: it must already work, or the missing work must be included. The service never widens a boundary by inference.

## Interruptions

Every step is saved, so an interrupted registration resumes from its last verified step. If publishing is interrupted, the service checks what actually reached the repository before writing again, never overwrites different content, and never asks the Owner to confirm twice. An unclear result is treated as unconfirmed, and the previous registration stays active.
