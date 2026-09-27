# Registration reads the workshop rules file

## Outcome and result
A change to how [Register and confirm a project through the CLI](../outcomes/registration.md#register-and-confirm-a-project-through-the-cli) checks planning documents. The outcome and its acceptance criteria stay as they are. Registration loads one rules file from the workshop, applies it to the exact saved revision of the project's planning documents, and reports which rules failed. It no longer carries its own hardcoded copy of what the documents must contain. A change to the rules file changes what registration checks, with no code change.

## Existing implementation assessment
Registration checks the documents with rules written into the code: the accepted source types, the required overview sections and the declaration fields (`services/maestro/maestro/service/registration_source.py`), and the reading instructions given to the registration agents (`services/maestro/maestro/service/registration.py`). Those rules still describe the old milestone declarations. The rules file, `skills/maestro-workshop/process/registration-rules.json`, exists with its first set of rules (all required sections, tables, allowed values, link rules and cross-document rules for the overview, architecture, roadmap and outcome documents), and the templates agree with it. Registration does not read it yet. The direction for the split between the workshop and the service is in [the registration process](../../../../skills/maestro-workshop/process/registration-process.md).

## What has to be true
- The workshop holds one rules file, `skills/maestro-workshop/process/registration-rules.json`, in JSON so a program can read it, listing the required documents, their required sections and the link rules. The workshop's templates and guide agree with it (done).
- The service takes the rules file from a tested release, using only versions marked passed. The CLI checks for a newer approved version when it starts, tells the Owner one exists, and says which version it used.
- Each registration keeps the rules version it started with, so the rules cannot change halfway through.
- When a document fails a rule, registration stops with a plain report of which rule failed, in which document and where. The service saves the report with the exact version it checked, and the next workshop session reads it first.
- The service records the rules version used with the registration, in a small registration record: the pinned revision, a fingerprint of each document, the rules version, the workshop's review record, and the Owner's confirmation.
- Registration launches no reviewer of its own. It checks that the workshop's review record exists, covers exactly the version being registered, that no document changed afterwards, and that coverage is complete.

## Verification
A real registration through the CLI on a real repository. Change one rule in the file and show that registration's result changes with no code change. Show a failing document reported by rule, a registration that keeps its version while a newer one is released, and the recorded version.

## Work still to do
- Make registration read the rules file: the loader, the version pinned per registration, and the CLI check for a newer approved version.
- Remove the registration agents from the code: launching the architect and reviewer, their response contract, review-round counting, and the registration-only retry and timeout settings in `services/maestro/maestro/service/registration.py`.
- Replace the old package with the small registration record in `services/maestro/maestro/service/registration_package.py`. Settle the record's exact file layout and how the workshop reads a saved rejection report.
- Replace the hardcoded source checks in `services/maestro/maestro/service/registration_source.py` with the rules file.
- Update the schemas that still describe the old process: `docs/schemas/registration-process.schema.json`, `docs/schemas/registration-records.schema.json` and `services/maestro/schemas/registration-process/1/schema.json`.
- Update the tests in `tests/maestro/service/test_registration.py` and the old paths in the CLI help text (`services/maestro/maestro/terminal/main.py`).
- Re-prove the blank rows in [the registration outcomes](../outcomes/registration.md) with a real registration.
