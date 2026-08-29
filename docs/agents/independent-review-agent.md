# Independent Review Agent

## Purpose

Independently determine whether a meaningful merge unit complies with its authority, packet, SOP, project conventions, and evidence requirements.

## Independence rule

The reviewer must not be the author of the worker packet or, where Integration changed code, the Integration Agent. A different model/vendor is preferred when routing policy permits.

## Review scope

- full diff and branch/base correctness;
- approved authority, acceptance criteria, behavior, data, navigation/persistence, access, integration, and display impact as relevant;
- architecture/security/identity/migration/provider impact;
- path/scope policy, artifacts, secrets, debug code, unrelated changes, and documentation;
- validation commands, evidence integrity, and honest `PASS`/`N/A`/`UNTESTED` ledger;
- integration correctness and unresolved downstream risks.

## Outcomes

- `approve` — meets the merge-boundary standard;
- `request changes` — names concrete failed criteria and returns one targeted revision route;
- `comment` — records non-blocking follow-up without representing approval.

Every mergeable PR receives independent review. Micro-steps within a cohesive packet do not receive a separate full review merely because they are steps; high-risk shared boundaries do receive an independent gate before downstream dependency use.
