# M2 Wave B — Atlas App Scaffold — Candidate 01

**Slice ID:** `MB-SLICE-M2-B1-ATLAS-SCAFFOLD-01`
**Status:** `Pending Targeted Verification` — targeted planning correction applied after Decision Fidelity `REQUEST_CHANGES` found check_06's `--port 0` claim doesn't actually select an ephemeral port in the pinned Vite version (empirically verified by the reviewer), plus two cheap non-blocking fixes (a devDependency miscount, a maintainer-flagged bad patch pin)
**Base:** `620bc1e` (`origin/master`)

## Scope, deliberately minimal

Wave B1 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the first
frontend slice. Creates `apps/atlas/`, a React + TypeScript + Vite
application with no screens — build, type-check, lint, and test tooling
only, rendering a single placeholder string to prove the pipeline works
end to end. Design tokens (B2), the desktop shell (B3), and the mobile
shell (B4) are separate, later slices; this one contains no visual
design, no routing, no data fetching against A1-A5's read API, and no
reference to the Owner's design handoff beyond the already-decided
technology choice (React/TypeScript — the same stack the repo's own
Alpha-era Decision Fidelity review already named: `docs/planning/maestro-alpha-decision-fidelity-review.md`
records "Owner-selected React/TypeScript Atlas" and `apps/atlas/` as its
path).

This is the first slice in the M2 program that is not a Python backend
change. Nothing under `apps/` exists yet; every file in this contract is
new. No `services/maestro` file is touched, and no repository-wide
tooling (there is no CI configuration anywhere in this repository today —
none is added by this slice either) is introduced.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-B1-ATLAS-SCAFFOLD-01` |
| `phase` | `PendingTargetedVerification` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:620bc1e","git:full-planning-review-head:9f84bdd5c6222ae513abc175c1ac1682d38990ef","review:decision-fidelity:request-changes:1-blocking-finding"]` |

## Dependency-version policy (read this before implementing)

Every dependency below is pinned to an exact version — the latest patch
release, as of this contract's authoring, of a **well-established major
version line** (React 19, TypeScript 5.x, Vite 7, ESLint 9 flat config,
Vitest 3, Testing Library 16) — deliberately **not** whatever the npm
registry's unqualified `latest` dist-tag resolves to today (which, at
authoring time, pointed at brand-new, unproven major versions: TypeScript
7, Vite 8, ESLint 10 — majors this contract has no basis to assume the
rest of the pinned ecosystem, e.g. `typescript-eslint`, already supports).
If, at implementation time, an exact pinned version is no longer
resolvable (removed/deprecated) or `npm install` reports a real peer-
dependency conflict, the implementor may substitute the nearest later
patch/minor **within the same major version line named above**, and must
report the substitution and its reason — exactly the class of
implementation-time judgment call already established for this program
(e.g. A2's qmark-vs-numbered-SQL-parameter substitution). Jumping to a
different major version line (e.g. TypeScript 7, Vite 8) is **not**
authorized by this contract and would need its own review.

**One pin below is deliberately not the newest 6.x patch** (a non-blocking
Decision Fidelity finding): `@testing-library/jest-dom` is pinned to
`6.9.1`, not `6.10.0` — `6.10.0`'s own package prints an `npm install`-time
deprecation warning identifying itself as "an incorrect minor release
with breaking changes," and directs installers to `6.9.1` or `7.0.0`.
`6.9.1` is the last release before that regression, still within the
pinned major/minor line.

## Exact file contents

`apps/atlas/package.json` (new):

```json
{
  "name": "atlas",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "19.2.8",
    "react-dom": "19.2.8"
  },
  "devDependencies": {
    "@eslint/js": "9.39.5",
    "@testing-library/jest-dom": "6.9.1",
    "@testing-library/react": "16.3.3",
    "@types/react": "19.2.18",
    "@types/react-dom": "19.2.7",
    "@vitejs/plugin-react": "4.7.0",
    "eslint": "9.39.5",
    "jsdom": "25.0.1",
    "typescript": "5.9.3",
    "typescript-eslint": "8.69.0",
    "vite": "7.3.6",
    "vitest": "3.2.7"
  }
}
```

`apps/atlas/tsconfig.json` (new):

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src", "vite.config.ts"]
}
```

`apps/atlas/vite.config.ts` (new):

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: false,
  },
});
```

`apps/atlas/eslint.config.js` (new):

```js
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      // Explicit and defensive, not a fix for an active false positive:
      // typescript-eslint's own recommended config already disables
      // no-undef for .ts/.tsx files (TypeScript's checker already
      // catches undefined identifiers with full type information), so
      // this line currently changes nothing observable. It stays as a
      // literal statement of intent in case a future config change ever
      // reintroduces the rule for these files.
      "no-undef": "off",
    },
  },
);
```

`apps/atlas/index.html` (new):

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Atlas</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`apps/atlas/src/vite-env.d.ts` (new):

```ts
/// <reference types="vite/client" />
```

`apps/atlas/src/App.tsx` (new):

```tsx
export function App() {
  return <div>Atlas</div>;
}

export default App;
```

`apps/atlas/src/main.tsx` (new):

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

const container = document.getElementById("root");
if (container === null) {
  throw new Error("Root element #root was not found");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

`apps/atlas/src/App.test.tsx` (new):

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the Atlas placeholder", () => {
    render(<App />);
    expect(screen.getByText("Atlas")).toBeInTheDocument();
  });
});
```

`apps/atlas/src/test/setup.ts` (new):

```ts
import "@testing-library/jest-dom/vitest";
```

`apps/atlas/.gitignore` (new):

```
node_modules/
dist/
*.local
```

`apps/atlas/package-lock.json` (new, generated by `npm install` — not
hand-authored; its exact content is whatever `npm install` resolves
against the pinned versions above, or their authorized substitutes).

## Guards and boundary

1. Every file above lives under `apps/atlas/`; no file outside that
   directory is created, modified, or deleted by this slice.
2. `node_modules/` and `dist/` are never committed (enforced by the
   `.gitignore` above and by a hygiene check before any readiness claim).
3. `package-lock.json` **is** committed — it is the reproducibility
   record for the exact dependency tree `npm install` resolved.
4. No dependency outside the two `dependencies` and twelve
   `devDependencies` named above (or their authorized same-major-line
   substitutes) is added without a new review.
5. No routing, no data fetching, no design tokens, no reference to
   `docs/planning/m2-atlas-roadmap.md`'s later waves' content — this
   slice's only rendered output is the literal string `Atlas`.

## Boundary, proof, and M0-D12

Writable paths are exactly the eleven files listed above, all newly
created under `apps/atlas/`. No `services/maestro` or `tests/` path is
touched by this slice.

The 7 named checks, run from `apps/atlas/` after `npm install`:

1. `check_01_install_succeeds_and_lockfile_committed` — `npm install`
   from a clean checkout (no pre-existing `node_modules/`) exits `0`;
   `package-lock.json` exists and `git status` shows it as a tracked,
   committed file (not merely present on disk).
2. `check_02_typecheck_passes` — `npm run typecheck` exits `0` with no
   type errors.
3. `check_03_lint_passes` — `npm run lint` exits `0` with zero errors and
   zero warnings.
4. `check_04_build_succeeds` — `npm run build` exits `0` and produces
   `apps/atlas/dist/index.html`.
5. `check_05_test_suite_passes` — `npm test` exits `0`; the one named
   test, `App > renders the Atlas placeholder`, passes.
6. `check_06_dev_server_serves_root` — **corrected, blocking finding from
   Decision Fidelity review:** Vite (verified against the pinned 7.3.6)
   treats `--port 0` as falsy and silently falls back to its fixed
   default port `5173`, not an OS-assigned ephemeral port — `--port 0
   --strictPort` is therefore neither ephemeral nor safe against a
   colliding process already on `5173` (`--strictPort` turns that
   collision into a hard failure instead of the intended isolation). The
   correct mechanism: before invoking Vite, select a genuinely free port
   by binding a throwaway socket to port `0` and reading back the
   OS-assigned port (e.g.
   `python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()"`
   or the Node/shell equivalent), close that socket, then invoke
   `npm run dev -- --port <that-port> --strictPort` with the real number.
   A small close-then-reuse race is possible but is standard, accepted
   practice for test port allocation (the same pattern this program's own
   Python `ReadApiServer` tests already use via `port=0` at the socket
   level in A1). The rest of the check is unchanged: the server starts
   within a bounded timeout (10s); a `GET /` against
   `http://127.0.0.1:<that-port>/` returns `200` with `Content-Type:
   text/html` and a body containing `<div id="root">`; the process is
   then terminated cleanly (`SIGTERM`, confirm exit).
7. `check_07_exact_file_boundary` — after `npm install` and running the
   checks above, `git status --porcelain` inside `apps/atlas/` shows
   nothing untracked or modified beyond what `.gitignore` already
   excludes (i.e., only the eleven authored files plus the generated
   `package-lock.json` are ever staged for commit).

Run `python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` is **not applicable** to this slice (element 5 of
M0-D12 below records this as an explicit not-applicable, since this
slice touches no Python file); the existing 339 Python-side named tests
are unaffected and not required to be re-run as part of this slice's own
acceptance proof, though they remain part of milestone-level acceptance
as always.

### M0-D12 bounded quality contract

1. **Protected outcome:** a fresh checkout of `apps/atlas/` can be
   installed, type-checked, linted, built, and tested without manual
   intervention, and the built app renders without a runtime error.
2. **Operating and threat model:** a trusted local single-user Linux box
   with outbound network access to the public npm registry at build/
   install time (a build-time dependency, not a runtime network
   requirement — the built `dist/` output is static and serves no
   network calls itself); no adversarial npm package content is assumed
   out of scope (see exclusions).
3. **Explicit exclusions:** supply-chain integrity verification of npm
   packages beyond `package-lock.json`'s own integrity hashes (no SBOM,
   no `npm audit` gate, no private registry mirror); any design token,
   screen, route, or data fetch (B2/B3/B4 and Wave C); any CI wiring
   (none exists in this repository); server-side rendering; any
   accessibility audit beyond what a single placeholder `<div>`
   trivially satisfies; supporting any Node.js version other than
   whatever is already installed in this environment (no `.nvmrc`/engines
   field is authorized by this slice).
4. **Assurance level:** practical local-development tooling correctness —
   proportionate to a zero-runtime-surface static placeholder app, not a
   production security posture.
5. **Acceptance proof:** the 7 named checks above, all passing. The
   Python-side `compileall`/`unittest` proof this program's backend
   slices have used is explicitly not applicable here (no Python file is
   touched) — recorded here as the required not-applicable disposition
   for that element, not a silent omission.
6. **Implementation boundary:** exactly the eleven writable paths above;
   the pinned dependency set (or an authorized same-major-line
   substitute per the version policy above); no other dependency, no
   other file.
7. **Proportionality ceiling:** one minimal app scaffold with zero
   screens; no state-management library, no CSS framework, no icon set,
   no router — all of that is out of scope until a later slice's actual
   rendering need justifies it.
8. **Stop and escalation rule:** if `npm install` cannot resolve a
   mutually compatible set of packages within the named major-version
   lines at all (not just a patch substitution), or if outbound network
   access to the npm registry is unavailable in the implementation
   environment, stop and report — do not silently vendor packages,
   switch package managers, or downgrade to a different major version
   line without a new review. A discovered proof/contract defect against
   a frozen slice terminally returns that slice. One planning correction
   and one implementation correction are the maximum available.
