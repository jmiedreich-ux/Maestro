# Registration reads the workshop rules file

## Outcome and result
A change to how [Register and confirm a project through the CLI](../outcomes/registration.md#register-and-confirm-a-project-through-the-cli) checks planning documents. The outcome and its acceptance criteria stay as they are. Registration loads one rules file from the workshop, applies it to the exact saved revision of the project's planning documents, and reports which rules failed. It no longer carries its own hardcoded copy of what the documents must contain. A change to the rules file changes what registration checks, with no code change.

## Existing implementation assessment
Registration checks the documents with rules written into the code: the accepted source types, the required overview sections and the declaration fields (`services/maestro/maestro/service/registration_source.py`), and the reading instructions given to the registration agents (`services/maestro/maestro/service/registration.py`). Those rules still describe the old milestone declarations. The rules file, `skills/maestro-workshop/process/registration-rules.json`, does not exist yet. The direction for the split between the workshop and the service is in [the registration split](../../../../skills/maestro-workshop/process/registration-split.md).

## What has to be true
- The workshop holds one rules file, `skills/maestro-workshop/process/registration-rules.json`, in JSON so a program can read it, listing the required documents, their required sections and the link rules. The workshop's templates and guide agree with it.
- The service takes the rules file from a tested release, using only versions marked passed. The CLI checks for a newer approved version when it starts, tells the Owner one exists, and says which version it used.
- Each registration keeps the rules version it started with, so the rules cannot change halfway through.
- When a document fails a rule, the Owner sees which rule and where, in plain words, and can return to the workshop.
- The service records the rules version used with the registration.

## Verification
A real registration through the CLI on a real repository. Change one rule in the file and show that registration's result changes with no code change. Show a failing document reported by rule, a registration that keeps its version while a newer one is released, and the recorded version.
