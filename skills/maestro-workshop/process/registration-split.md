# Registration: what moves to the workshop and what stays in the service

Working analysis for the Owner's decision. Nothing here is built or agreed as a requirement yet. It compares each part of registration in [the architecture](../../../docs/product/v1/architecture.md#registration) with the direction the Owner set: the workshop does the thinking, and the service only checks, records and asks for confirmation.

## The idea in plain words

Today, registration is one large process. It launches its own architect and reviewer agents, collects answers, builds a package of records, publishes it to GitHub and asks the Owner to confirm.

Under the new direction, the planning work happens earlier, inside the [maestro-workshop skill](../SKILL.md), with the Owner in the room. By the time registration starts, the planning documents already exist and have been independently reviewed. Registration then does only what a program can do reliably: check the documents against a rules file, record exactly which version was checked, and ask the Owner to confirm.

## Part by part

| Part of registration today | Where it goes | Why |
|---|---|---|
| Finding the project, checking repository access, credentials and branch protection | Service | It holds the secrets and must not depend on an agent's word. |
| Pinning the exact revision that is checked, and choosing where results are published | Service | A record of exactly what was approved. |
| Only one registration at a time per project; blocking re-registration while work is running | Service | Protects work in progress. |
| Checking that required documents, sections and links exist and are well formed | Service, driven by the shared rules file | Mechanical, and it becomes the second check on the workshop's output. |
| Noticing that the source changed before confirmation | Service | Mechanical. The choice of what to do stays with the Owner. |
| Understanding the meaning of the plan, its scope and its dependencies | Workshop | Judgment, done with the Owner. |
| Testing whether the scope can really deliver the outcome (the usage walkthrough) | Workshop | Judgment. |
| Tagging what exists today by how well it is known (reported, seen in code, verified) | Workshop | Already part of the workshop's rules. |
| Asking the Owner about missing or contradictory facts | Workshop | The Owner is already there; no separate question-routing process is needed. |
| Independent review of the plan and recorded gaps | Workshop | The workshop already runs and records it. The service only checks that the record exists for the exact revision. |
| Choosing a portion of the project to register | Both | The workshop helps define the boundary; the service records the chosen boundary and the Owner confirms it. |
| Building the package of records (declarations, milestone records, naming conventions) | Mostly dropped | The planning documents are the package. The service keeps a small record: the pinned revision, the document fingerprints, the rules version used, the review record, and the Owner's confirmation. |
| Publishing the record to GitHub and recovering if it is interrupted | Service | Durability and safety, unchanged in purpose. |
| The Owner's confirmation, comparison with the previous version, and cancellation | Service and CLI | This is the Owner's gate and the permanent record. |
| Registration-specific agents: launching an architect and a reviewer, their response format, review-round counting, retry limits and time limits | Dropped from registration | The workshop does this work before registration. The shared agent tooling stays for the architecture and execution stages. |

## What this removes

- The registration architect and reviewer as separate launched agents.
- The registration agent response contract, and the registration-only retry and timeout settings.
- The declaration, milestone and naming-convention record types.

## What this adds

- One rules file, `registration-rules.json` in this folder, machine readable (JSON), listing the required documents, sections and link rules. The workshop and the service both follow it.
- A small, fixed registration record instead of a package of many files.
- A check in the service that the workshop's review record matches the exact revision being registered.

## Decisions for the Owner

1. Is the "small registration record" the right size, or should the service keep more of the old package?
2. If the service no longer launches reviewers for registration, is the workshop's independent review, checked by fingerprint, enough as the independent check at registration?
3. How should a rejected registration go back to the workshop: an error listing the failed rules, with the workshop rerun by the Owner?
