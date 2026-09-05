# M2 Wave B — Mobile Shell — Candidate 01

**Slice ID:** `MB-SLICE-M2-B4-MOBILE-SHELL-01`
**Status:** `Frozen — Pending Implementation`. Full Decision Fidelity review returned `APPROVE` with 2 non-blocking findings (one disclosed literal was left as a bare CSS value instead of routed through the same custom-property mechanism as the others; a quoting-convention inconsistency), both fixed here at zero cost before freeze. No blocking findings; no planning correction was needed.
**Base:** `ca8f710` (`origin/master`)

## Scope, deliberately minimal

Wave B4 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md), the last slice
in Wave B: the mobile shell. Adds a new `MobileShell` component — phone
body, four-tab bottom bar — as a standalone component with its own test
file. **This slice does not wire `MobileShell` into `App.tsx`.** Unlike
B3, where the desktop shell was and remains the app's one and only
rendered surface, the design handoff treats desktop and mobile as two
genuinely separate artifacts (two separate reference files,
`Atlas Explorations.dc.html` and `Atlas Mobile.dc.html`, never one
responsive layout that becomes the other). Deciding how a real build
serves one or the other — a route, a viewport check, a separate build
target — is a real product/architecture decision this slice has no
mandate to invent, and B3's contract never claimed one either. This
slice proves `MobileShell` renders correctly on its own, exactly as B1
proved the whole app scaffold worked before B2/B3 gave it real content.
No tab has real content yet (Now/Chat/Activity/Plan content is Wave F,
same relationship B3 has to Wave E's Performance/Agents/History/Gate
content).

**A real discrepancy between the README and the reference file, resolved
per the README's own Fidelity rule:** the README's mobile-app intro
prose lists tab order as "Now / Chat / Activity / Plan." The actual
reference file's tab bar markup (`Atlas Mobile.dc.html`, the bottom
`<nav>` element) renders them in a different order: **Now, Chat, Plan,
Activity**. The README's own Fidelity section says "prefer the reference
file over this README if they ever disagree" — so this slice uses the
reference file's actual order (Now, Chat, Plan, Activity), not the
prose's order. This is called out explicitly, not silently resolved, per
the lesson from this same wave's B3 candidates: a value that can be
checked against the reference file must be, not inferred or assumed from
prose.

Source quote (README, "## Mobile app" preamble — the exact lines this
slice implements):

> Phone body `#F7F5FA`; content scrolls; a fixed four-tab bar at the
> bottom (`grid-template-columns: repeat(4,1fr)`, `padding: 6px 8px
> 4px`, each tab `min-height: 50px`, `12px/700` label, selected tinted):
> **Now / Chat / Activity / Plan**.

Reference-file quote (`Atlas Mobile.dc.html`, the bottom tab `<nav>` —
the source of every value the README's prose leaves inexact, and the
authority for the real tab order per the Fidelity rule above):

```html
<nav style="flex:none;display:grid;grid-template-columns:repeat(4,1fr);
  padding:6px 8px 4px;background:rgba(255,255,255,.92);
  border-top:1px solid #EAE5F0;backdrop-filter:blur(12px)">
  <button onClick="{{ goNow }}" style="min-height:50px;border:0;
    border-radius:14px;background:transparent;color:{{ tabNowColor }};
    cursor:pointer;font-size:12px;font-weight:700;letter-spacing:.01em">Now</button>
  <button style="...color:{{ tabThreadColor }}...">Chat</button>
  <button style="...color:{{ tabPlanColor }}...">Plan</button>
  <button style="...color:{{ tabActColor }}...">Activity</button>
</nav>
```
(Elided attributes — `onClick` handlers on the other three buttons and
the first button's own `letter-spacing:.01em` — are the reference file's
own interactivity/micro-styling, not reproduced by this static, unwired
shell; `...` consistently marks every elision in this quote.)
```js
const col = k => s.tab === k ? '#5B34E8' : '#9A90A6';
```

Explicitly **not** built by this slice:

- Any tab's real content (Now/Chat/Activity/Plan screens — Wave F).
- The phone device-frame chrome the reference file wraps its content in
  for on-page viewing (the purple gradient bezel, the outer padding) —
  that is presentational scaffolding for displaying the mockup on a web
  page, not part of the app itself; this slice renders only the actual
  app surface (the `#F7F5FA` body and the tab bar), matching how B3
  never rendered a fake browser chrome around the desktop shell either.
- Any connection strip, empty/crashed/disconnected state — same
  exclusion B3 already established, still no data source exists.
- Any routing/wiring decision for how a real build chooses desktop vs.
  mobile — named above as a real, separate, later decision.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-B4-MOBILE-SHELL-01` |
| `phase` | `PendingImplementation` |
| `current_actor` | `none` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:ca8f710","git:full-planning-review-head:371e1968185bc3428c65be91a9c2f4918a04553c","review:decision-fidelity:approve:non-blocking-findings-fixed-pre-freeze"]` |

## Exact file contents

`apps/atlas/src/shell/MobileShell.module.css` (new — a CSS Module.
Every color/font declaration is `var(--atlas-*)`, following the exact
pattern B3 established: set once, at runtime, in `MobileShell.tsx`, from
real token values or a disclosed literal — never hand-copied into this
file):

```css
.shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--atlas-page-bg-mobile);
  overflow: hidden;
}

.content {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 24px 26px;
  color: var(--atlas-ink-muted);
  font: 400 13.5px var(--atlas-font-body);
}

.tabBar {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 6px 8px 4px;
  background: var(--atlas-tab-bar-bg);
  border-top: 1px solid var(--atlas-tab-bar-border);
  backdrop-filter: var(--atlas-tab-bar-blur);
}

.tab {
  min-height: 50px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: var(--atlas-tab-inactive);
  cursor: pointer;
  font: 700 12px var(--atlas-font-body);
}

.tabSelected {
  color: var(--atlas-tab-selected);
}
```

`apps/atlas/src/shell/MobileShell.tsx` (new):

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import styles from "./MobileShell.module.css";

export type MobileShellTab = "now" | "chat" | "plan" | "activity";

const TABS: ReadonlyArray<{ tab: MobileShellTab; label: string }> = [
  { tab: "now", label: "Now" },
  { tab: "chat", label: "Chat" },
  { tab: "plan", label: "Plan" },
  { tab: "activity", label: "Activity" },
];

/**
 * Every value here is either a direct property of the real, reviewed
 * `colors`/`fontFamily` tokens, or — where no token exists yet — a
 * literal with an inline comment naming its actual source (all five
 * non-token values here are from `Atlas Mobile.dc.html`, none
 * invented — corrected from an earlier draft that left one,
 * `backdrop-filter: blur(12px)`, as a bare CSS literal instead of
 * routing it through this same disclosed mechanism). Matches the
 * pattern `DesktopShell.tsx` (B3) already established.
 */
const SHELL_VARS = {
  "--atlas-page-bg-mobile": colors.pageBgMobile,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-font-body": fontFamily.body,
  // Not tokens: the reference file's own tab-bar chrome
  // (Atlas Mobile.dc.html's bottom <nav>) — no equivalent values exist
  // in colors.ts.
  "--atlas-tab-bar-bg": "rgba(255,255,255,.92)",
  "--atlas-tab-bar-border": "#EAE5F0",
  "--atlas-tab-bar-blur": "blur(12px)",
  // Reference file: `const col = k => s.tab === k ? '#5B34E8' : '#9A90A6'`.
  // The selected color is the real `colors.accent` token; the inactive
  // color (#9A90A6) has no equivalent token, so it stays a disclosed
  // literal.
  "--atlas-tab-selected": colors.accent,
  "--atlas-tab-inactive": "#9A90A6",
} as CSSProperties;

const TAB_LABEL: Record<MobileShellTab, string> = {
  now: "Now",
  chat: "Chat",
  plan: "Plan",
  activity: "Activity",
};

export function MobileShell() {
  const [selected, setSelected] = useState<MobileShellTab>("now");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <main className={styles.content}>{TAB_LABEL[selected]} tab</main>
      <nav className={styles.tabBar} aria-label="Atlas tabs">
        {TABS.map((t) => (
          <button
            key={t.tab}
            type="button"
            className={`${styles.tab} ${selected === t.tab ? styles.tabSelected : ""}`}
            aria-current={selected === t.tab ? "true" : undefined}
            onClick={() => setSelected(t.tab)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

export default MobileShell;
```

`apps/atlas/src/shell/MobileShell.test.tsx` (new — includes the local
`afterEach(cleanup)` and `fireEvent.click()` pattern B3's implementation
established as necessary in this Vitest/jsdom/React-19 stack, applied
here from the start rather than discovered again during implementation):

```tsx
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import MobileShell from "./MobileShell";

afterEach(cleanup);

describe("MobileShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, plus the disclosed reference-file literals", () => {
    const { container } = render(<MobileShell />);
    const root = container.firstChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-page-bg-mobile")).toBe(colors.pageBgMobile);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-tab-bar-bg")).toBe("rgba(255,255,255,.92)");
    expect(root.style.getPropertyValue("--atlas-tab-bar-border")).toBe("#EAE5F0");
    expect(root.style.getPropertyValue("--atlas-tab-bar-blur")).toBe("blur(12px)");
    expect(root.style.getPropertyValue("--atlas-tab-selected")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-tab-inactive")).toBe("#9A90A6");
  });

  it("renders exactly four tabs, in the reference file's actual order (not the README prose order)", () => {
    render(<MobileShell />);
    const tabs = screen.getAllByRole("button");
    expect(tabs.map((t) => t.textContent)).toEqual(["Now", "Chat", "Plan", "Activity"]);
  });

  it("defaults to Now selected, with only one tab marked current", () => {
    render(<MobileShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByText("Now tab")).toBeInTheDocument();
  });

  it("tapping a tab makes it the sole selected tab and updates the content pane", () => {
    render(<MobileShell />);
    fireEvent.click(screen.getByRole("button", { name: "Activity" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Activity");
    expect(screen.getByText("Activity tab")).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<MobileShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `App.tsx` or any other existing
   component — it is a standalone, currently-unreferenced module, exactly
   like `src/tokens/` was before B3 (and unlike B3 itself, which was
   wired in immediately).
2. `MobileShell.module.css` contains no literal hex color, font-family
   string, or other design-token-shaped value (including the
   `backdrop-filter` blur radius) — every declaration is `var(--atlas-*)`,
   each one set exactly once in `MobileShell.tsx`'s `SHELL_VARS` from a
   real `colors`/`fontFamily` property or a literal with an inline
   comment naming its real, non-token source (the five
   reference-file-only values named above). Numeric layout values with
   no design-token equivalent in this codebase (`min-height`,
   `border-radius`, grid/padding shorthands) stay literal, matching the
   precedent B3's `DesktopShell.module.css` already established.
3. No file under `apps/atlas/src/tokens/` is modified — `colors.ts`,
   `typography.ts`, `motion.ts`, `shape.ts`, and `index.ts` are read
   (imported) but byte-identical to their current, merged state. Unlike
   B3, this slice does not need to touch `tokens.test.ts` either — no
   test in that file asserts anything about a second consumer, only
   about "no consumer outside `tokens/`" in general, which B3 already
   retired.
4. No routing library, no persisted selection, no wiring into `App.tsx` —
   `selected` is local `useState`, and this component is reachable only
   by importing it directly (e.g. from a future dedicated slice's own
   entry point), exactly as scoped above.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/shell/MobileShell.module.css` (new)
- `apps/atlas/src/shell/MobileShell.tsx` (new)
- `apps/atlas/src/shell/MobileShell.test.tsx` (new)

No other path — in particular, `App.tsx`, `App.test.tsx`,
`DesktopShell.*`, and every file under `apps/atlas/src/tokens/` are
untouched.

The 5 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test (B1's App test, B2's 4
remaining token tests, B3's 7 shell tests) continuing to pass unmodified
— 17 total after this slice. `npm run build` must still succeed; since
`MobileShell` is imported by nothing yet, it is not expected to appear
in the `dist/` bundle (mirroring B2's own build-unaffected proof) —
confirmed by the same string-search-the-bundle method B2's review used.

### M0-D12 bounded quality contract

1. **Protected outcome:** `MobileShell` renders the exact phone-body and
   four-tab-bar chrome the reference file specifies, in the reference
   file's real tab order, using only real B2 token values plus
   explicitly disclosed reference-file-only literals, with zero
   fabricated data, and with zero effect on the currently-shipped
   desktop app.
2. **Operating and threat model:** a trusted local dev box; a user
   tapping any tab in any order.
3. **Explicit exclusions:** any tab's real content; the reference file's
   device-frame presentation chrome; any wiring/routing decision for how
   a real build serves this surface; any connection/empty/crashed state;
   any change to `App.tsx`, `DesktopShell.*`, or any token file.
4. **Assurance level:** practical component-rendering correctness,
   proportionate to static shell chrome with no data dependency and no
   consumer yet — identical assurance posture to B2 and B3.
5. **Acceptance proof:** the 5 named tests, the existing 12 `apps/atlas`
   tests continuing to pass (17 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the three writable paths above;
   no new npm dependency; every CSS custom property set from a real
   token property or a disclosed reference-file literal, verified
   against the actual `.dc.html` source, not assumed from the README's
   prose.
7. **Proportionality ceiling:** one shell component, one CSS Module, no
   router, no wiring, no tab content, no animation (the reference file's
   `rise`/`sheet` keyframes are unused by this static shell, same as B3).
8. **Stop and escalation rule:** deciding how a real build serves
   `MobileShell` alongside `DesktopShell` (a route, a viewport check, a
   separate entry point) is a new, separately reviewed slice — not
   something this one decides implicitly by choosing not to wire it in.
   A discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
