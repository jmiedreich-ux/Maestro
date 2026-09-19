# Maestro manual architecture — QA resource preparation

Resource preparation, version 5. The selected QA repository now exists and its service-App read access is verified. The operator-prepared binding description is saved on the Linux AI box. Maestro service installation, catalog validation and runtime plan binding remain implementation work; this preparation does not authorize running QA.

## Why this input is needed

[Project Quality Assurance bindings](../../architecture.md#project-quality-assurance-bindings) requires an operator-provided, non-secret catalog before QA plans use environments, credentials or network access. An entirely self-contained plan may use empty references and a null binding hash. That exception cannot be used for acceptance requiring actual GitHub publication, installed agents or credentialed service behavior.

The manual planning adaptation records verified operator evidence without calling it a service-owned catalog. The repository, service App, installed tools, exact local models, network endpoints and isolated roots below are now concrete. The unimplemented service cannot yet collect, validate or publish the runtime catalog and QA-plan records.

## Verified resource arrangement

| Resource | Verified binding | Remaining work |
|---|---|---|
| Host | Linux AI box; isolated roots prepared under `/home/jeremy/Development/Maestro/var/qa` for environments, worktrees, artifacts and secrets; directories are owner-only. Loopback port `8877` was available at inspection. | The isolated Maestro test service identity, installation and separate test Owner credential are delivered during implementation. |
| GitHub test project | Private `jmiedreich-ux/Maestro-qa`; default branch `main`; operator admin access verified. | Use only run-owned test projects, branches and evidence. Repository creation grants no broad cleanup authority. |
| Service repository identity | GitHub App `Maestro Coordinator`; slug `maestro-coordinator`; App ID `4746601`; installation ID `157167451`; account `jmiedreich-ux`; installation active with all-repository selection. On 2026-09-19 a fresh App token read `Maestro-qa` contents and branch refs but received HTTP 403 for the branch-protection endpoint. The App and installation declare `Contents: write`; neither currently grants `Administration: read`. | Before M3 QA, the App owner must add repository `Administration: read` to Maestro Coordinator and approve the permission update on its `jmiedreich-ux` installation. The service then proves fresh Contents-write and Administration-read access, exact App/installation identity and configured profile mapping without exposing the key or token. |
| GitHub destination-policy QA targets | Run-owned branch `maestro-m3-authorized` exists and is unprotected. Run-owned branch `maestro-m3-protected` exists but is also unprotected. On 2026-09-19 GitHub rejected both branch-protection and repository-ruleset creation for this private repository with `Upgrade to GitHub Pro or make this repository public to enable this feature`. | A protected or ruleset-bound branch in the same private QA repository remains unavailable. Do not substitute a permission-denied result. Before M3 acceptance, the Owner must choose a GitHub plan that permits private-repository protection or authorize a public QA policy target; then record the exact protected target, policy observation identities and profile binding. This is UNTESTED and blocks M3 acceptance. |
| Private key | Recovered into the local QA secret root with owner-only `600` permissions. The non-secret binding uses secret name `maestro-coordinator-private-key`. | Keep the value out of Git, chat, arguments and captured logs. Runtime availability is rechecked before use. |
| Owner request testing | A separate test credential is still required for the isolated service, including invalid and expired cases. | Approved implementation setup creates it; the normal operator credential is not reused. |
| Agent routes | Codex CLI `0.154.0`, authenticated through ChatGPT; Claude Code `2.1.270`, authenticated first-party; Qwen CLI `0.22.3`. | Registration and Architecture still collect architect/reviewer tool and exact model separately. Execution still records manager, coder and reviewer selections under existing routing rules. |
| Local model route | Ollama API `0.32.15` at `127.0.0.1:11434`. Available exact models: `qwen3.8:27b-temp03-thinking`, `qwen3.8:27b-temp03`, `qwen3.8:27b`, `qwen3.6:27b`, `codestral:22b`, and `muse-glimmer:30b`. | Each assignment selects and records one permitted exact model; availability is rechecked before launch. |
| Network | `api.github.com` over HTTPS port `443`; local Ollama over HTTP port `11434`. | Any additional cloud-agent endpoint must be observed from the selected supported route and added explicitly; no wildcard host is inferred. |
| Data and artifacts | Owner-only environment, worktree and artifact roots are prepared. | Setup generators, run manifests, retention and cleanup are delivered by the assigned implementation packets. |

## Operator-prepared binding evidence

The non-secret operator description is saved at `/home/jeremy/Development/Maestro/var/qa/operator-bindings.json`, SHA-256 `e6f6cca91b5b520d1de943e37f990f5284c0c191d73ca04dabb12c00dc3f7738`. It is operator-prepared evidence, not `qa-catalog.json`, a service-assigned identity or a runtime publication.

The service must import or collect the same facts through the implemented catalog contract, validate current availability and authorization, and produce its canonical snapshot/hash before runtime QA-plan publication and confirmation. A changed value requires the existing amendment path.

## Manual planning and remaining binding work

The architect owns routine QA design and setup requirements. Seven [milestone QA procedure specifications](qa-plans/README.md) define the real journeys, expected results, essential failures, data lineage, artifacts, cleanup and reset.

The protected GitHub repository/App binding, installed agent tools, local model inventory and isolated roots no longer block final manual-breakdown confirmation. The remaining implementation prerequisites are the Maestro service/catalog consumer, isolated test service identity and Owner credential, approved setup/check/data scripts, runtime plan records and actual test results. These are delivered by the existing packets rather than invented by QA.

## Confirmed repository decision and provisioning

The Owner selected `jmiedreich-ux/Maestro-qa` by replying **“Yes”** to **“Shall we use that repository name?”** The repository was created private on 2026-09-17 with default branch `main`.

The Owner later identified `Maestro Coordinator` as the service identity and authorized using it. Live GitHub App authentication confirmed App ID `4746601`, installation ID `157167451`, owner `jmiedreich-ux`, active all-repository selection and direct access to `Maestro-qa`. No secret value is recorded here.

## Readiness boundary

This completes the concrete manual QA resource bindings needed before presenting the seven development milestones and 42 work packets for confirmation. It does not establish an installed Maestro service, a service-validated catalog, executable runtime QA plans, passing QA or authority to start implementation.
