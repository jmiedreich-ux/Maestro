# M0-D03 — Access, Service Accounts, and Secrets

**Status:** Proposed baseline for M0 acceptance  
**Decision owner:** Maestro project owner  
**Scope:** Access design only; this record authorizes no credentials, GitHub App, Azure action, webhook, or runtime implementation.

## Decision

Maestro uses separate, least-privilege service identities for each external boundary. Personal credentials are never the durable identity of the coordinator. Secrets are supplied to the component that needs them at run time and are never copied into Maestro packets, SQLite records, Atlas, evidence, prompts, commits, or logs.

## Identity boundaries

| Boundary | Identity and minimum rule |
|---|---|
| Maestro coordinator | One Linux-hosted service identity; may perform only approved coordinator actions for registered projects |
| GitHub | A GitHub App or equivalent repository-scoped service identity; permissions are granted per project and action class |
| Local worker | A scoped local execution identity/worktree with only the repository and environment access required by its packet |
| Cloud worker | A scoped invocation credential with no standing GitHub/Azure secret unless the packet explicitly requires a separately approved adapter capability |
| Murphy | Its existing Azure-side QA identity remains separate; Maestro supplies only the approved target/version and credential-reference name |
| Atlas | No external credentials and no orchestration authority; it reads redacted live state from Maestro's local service |

## GitHub policy

1. Use a repository-scoped service identity, not a personal access token embedded in Maestro.
2. Default to read access for repository metadata, contents, issues, PRs, checks, and reviews.
3. Grant branch/PR write access only to the specific approved Maestro action and only after the project adapter/policy allows it.
4. Protected-branch rules remain in GitHub. Maestro cannot bypass them.
5. V1 does not receive automatic merge authority. Owner acceptance/merge rules remain unchanged.
6. Every GitHub action stores the request purpose, scoped project, external object identifier, and redacted outcome as Maestro evidence.

## Secret-handling rules

- The database stores a **secret reference**, never a secret value.
- Secret values are injected at run time from the selected local secret provider or external service; the provider choice is an implementation decision, not a packet-level choice.
- Redaction happens before command output, event payloads, errors, screenshots, and session exports are retained.
- Worker prompts receive only the minimum non-secret context necessary to complete their packet.
- Credentials have rotation/expiry metadata and a named owner. A stale or revoked reference blocks affected work visibly.
- Backups never include unencrypted secret values; database backups contain references and redacted operational records only.

## Event and webhook policy

V1 uses polling/reconciliation as its recovery authority. If later webhooks are enabled, each event endpoint must verify sender signature, timestamp/expiry, source identity, and replay/idempotency key before recording an observed event. A webhook may accelerate observation; it may not create a new authority path.

## Azure and Murphy boundary

The Linux Maestro box currently has no local Azure CLI/session requirement. M0 and V1 do not need direct Azure access merely to represent Murphy or an Azure deployment target. Murphy remains a separately authorized, manually triggered remote QA adapter under each project's policy.

## Non-negotiable guardrails

- Atlas never displays secrets, raw credentials, prompts containing secrets, or unredacted worker traces.
- A worker cannot broaden its own repository, cloud, or environment permissions.
- A task cannot request a secret value in its instructions; it names an approved capability/reference instead.
- A missing or expired required credential produces a visible blocked state, never a silent fallback to a personal account.
- No M0 planning decision grants merge, production deployment, or autonomous-next-work authority.

## Remaining implementation choices

1. Select the local Linux secret provider and rotation mechanism.
2. Register/configure the GitHub App or repository-scoped service identity.
3. Define project-level permission templates by adapter capability.
4. Define the cloud-worker invocation provider's own credential boundary.
