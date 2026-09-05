# M2 Wave F — Mobile Chat Tab — Candidate 01

**Slice ID:** `MB-SLICE-M2-F2-CHAT-TAB-01`
**Status:** `Decision Fidelity review returned PASS WITH 3 non-blocking notes (a mischaracterized attribution of an internal tab-id naming fact to the wrong prior slice's disclosure; an "exactly one CSS rule" overclaim for one shared token var; an unacknowledged-but-correctly-inherited plan/cadence sub-panel exclusion) — all three fixed at zero cost before freeze, no planning correction needed`
**Base:** `633167c` (full: `633167c8c1a5b34caf6231e2024b00f13af67836`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 34, *"F2 — Chat tab: reuses C1–C6 in the mobile bubble
layout."* This slice is frontend-only, no backend file touched.

This slice reuses C1's real fixture and header logic — not C3-C6.
Before writing any code, I checked the reference file's own mobile
`isThread` view (`Atlas Mobile.dc.html:140-197`) directly: it renders
only the same entries feed C1's desktop `PacketThread` already renders
(as bubbles instead of cards), plus the same identity/state header
C7's `PacketHeader`/`derivePacketHeaderState` already establish, plus
a message composer. It does **not** render `DecisionCard`,
`OwnerDecisionCard`, `FidelityRecord`, or `CrashCard` content inline —
those are separate desktop surfaces (C3-C6), reached differently, and
nothing in the real mobile markup embeds them here. "Reuses C1-C6" is
read as "reuses this program's already-established real logic from
that range of slices" (here: C1's fixture/text-color rule, C7's header
state), not as "embeds all four other components' own JSX," which the
reference file itself does not do.

## Evidence

`Atlas Mobile.dc.html:140-197` is the real mobile "Chat" tab (the
reference file's own internal name is `isThread`/`tab:'thread'`; B4's
already-merged `MobileShell.tsx` names the same real tab `"chat"` —
**corrected per an independent Decision Fidelity review's non-blocking
note**: B4's own actually-disclosed README-vs-reference discrepancy fix
was about tab bar *order*, not this internal id naming; citing it as
that specific fix was a mischaracterization, fixed here to state only
the real, checked fact — the two names refer to the same real tab,
without over-attributing which prior slice's disclosure covers it).
It has three real parts:

1. **Header** (`:141-144`): a "‹ Now" back link, `<h1>A.2 · Runtime
   Package</h1>` (a literal string, not derived from any real state
   field), and a state line with a colored dot.
2. **Entries feed** (`:146-192`): the exact same real `PACKET_A2_ENTRIES`
   C1's `PacketThread` already renders (`apps/atlas/src/thread/fixtures.ts:32-82`),
   as chat bubbles instead of desktop cards — name/role/time row (`:149`),
   then a bubble (`:150`) colored by a real per-entry `mine`/`nameColor`/
   `bubbleColor` rule (`renderVals()`, not itself line-numbered in this
   packet since it lives in the file's script block, but the exact real
   values it produces are cited below).
3. **Composer** (`:193-197`): a role-select button, a message textarea,
   and a send button — none of which has any real backend counterpart.

## Design rationale

1. **Reuses `PACKET_A2_ENTRIES` and `textColorFor` from C1's
   `PacketThread.tsx` verbatim**, exporting `textColorFor` (previously
   module-private) as the one additive change to that already-merged
   file — the exact real rule for bubble text color
   (`e.k === 'by' ? '#6C6376' : '#221C29'`, i.e.
   `colors.inkSecondary`/`colors.ink`), unchanged.
2. **Does NOT reuse `computeShowAvatar`'s same-author grouping.** The
   reference file's own mobile `entries` derivation has no such field
   — every entry's name/role/time row renders unconditionally in the
   real markup (`:149`, inside a plain `sc-for`, no conditional). This
   slice matches that literal, real structure rather than importing a
   desktop-only enhancement the mockup's own mobile view never
   exhibits.
3. **Implements the reference file's real, full `nameColor`/`mine`
   rule**, not a reduction to the two role kinds (`wk`/`co`)
   `PACKET_A2_ENTRIES` actually contains: `e.k === 'ow' ? '#4A28CC' :
   e.k === 'ar' ? '#3F1FC0' : (e.k === 'wk' || e.k === 'ow') ?
   '#4A28CC' : '#221C29'`. `#4A28CC`/`#3F1FC0` are real tokens,
   `colors.accentHover`/`colors.accentDeepest`
   (`colors.ts:27`/`:28`) — implemented in full so a future real
   `ow`/`ar` entry renders correctly without revisiting this function.
4. **The header does NOT transcribe the reference file's own literal
   text, `"A.2 · Runtime Package"`** (`:143`) — that string is neither
   of this program's two already-established real identity fields
   (`state.eyebrow`, `"m1-a · a.2"`; `state.title`, the full real
   work-item name, both from the already-merged, unmodified
   `derivePacketHeaderState`). Inventing a third, distinct abbreviated
   label would violate this program's own fixture-content discipline.
   This header instead reuses the exact same eyebrow/title pair C7's
   `PacketHeader.tsx` already established as this packet's one real
   identity — the README's own single-state-source rule, applied to a
   second real surface, matching F1's own precedent of reusing
   `derivePacketHeaderState` rather than re-deriving a surface-specific
   variant.
5. **No message composer or send control is rendered.** The reference
   file's own composer (`:193-197`) has no real backend counterpart
   anywhere in M1/M2 — no command exists for sending a chat message to
   an agent. Rendering an inert-but-visible composer would misrepresent
   a capability this build does not have — the same reasoning F1's
   `NowTab` already applied to its own excluded Stop/Start/
   Open-conversation controls.
6. **`onBack` is a prop, not internal state.** `MobileShell` already
   owns the real `selected` tab state (`useState<MobileShellTab>`);
   `ChatTab` accepts a callback rather than re-deriving its own
   navigation state, matching React's own single-owner-of-state
   convention and requiring only one new line in `MobileShell.tsx`
   (`onBack={() => setSelected("now")}`) rather than any new shared
   state mechanism.

## Guards

1. This slice modifies exactly 3 existing files
   (`apps/atlas/src/thread/PacketThread.tsx` — one function,
   `textColorFor`, changed from module-private to exported, zero
   behavior change; `apps/atlas/src/shell/MobileShell.tsx`;
   `apps/atlas/src/shell/MobileShell.test.tsx`) and adds exactly 3 new
   files (`apps/atlas/src/shell/ChatTab.tsx`,
   `ChatTab.module.css`, `ChatTab.test.tsx`) — no backend file, no
   other frontend file, touched.
2. `PacketThread.tsx`'s only change is exporting `textColorFor`
   (adding the `export` keyword to its existing declaration) — its own
   7 existing tests in `PacketThread.test.tsx` are unmodified and still
   pass unchanged, proving this is genuinely additive.
3. `MobileShell.test.tsx`'s two new tests (tapping Chat renders real
   content; the back button returns to Now) are additive; all 5
   pre-existing tests in that file are unmodified.
4. No `DecisionCard`, `OwnerDecisionCard`, `FidelityRecord`, or
   `CrashCard` content is rendered anywhere in `ChatTab.tsx` — see
   "Scope, deliberately minimal" above for why "reuses C1-C6" does not
   mean embedding all four. Two `PACKET_A2_ENTRIES` entries also carry
   real, unused `plan`/`cadence` fields (Terra's 13:51 and 14:30
   entries) that the reference file's own markup renders as inline
   sub-panels within the same bubbles — this slice inherits, not
   introduces, their exclusion: `fixtures.ts:19-20`'s own already-merged
   comment discloses them as "not yet rendered by any slice," and C1's
   own merged `PacketThread.tsx` likewise never renders them.
5. No message composer, textarea, or send button anywhere in
   `ChatTab.tsx` — a dedicated test
   (`test_04_renders_no_message_composer...` in the file below)
   confirms no `textbox` role, no "send"-named button, and no
   "message"-placeholder element render.
6. Every color in `ChatTab.tsx`/`ChatTab.module.css` is routed through
   a real token or a disclosed literal — verified by grepping the
   final CSS module for bare hex literals (none found) and confirming
   every declared `--atlas-*` custom property is consumed by at least
   one real CSS rule, with none orphaned (one, `--atlas-font-mono`, is
   legitimately consumed by two rules, `.eyebrow` and `.time`, sharing
   the same real font token — corrected per an independent Decision
   Fidelity review's non-blocking note: this item originally
   overclaimed "exactly one" for every var), matching the token-routing
   discipline an independent review already enforced on F1.
7. This slice does not implement F3 (Activity tab) or F4 (Plan tab) —
   separate, future roadmap items.

## `apps/atlas/src/thread/PacketThread.tsx` (modified — one function exported, no other change)

```typescript
export function textColorFor(entry: ThreadEntry): string {
  return entry.k === "by" ? colors.inkSecondary : colors.ink;
}
```

Every other line in this file is byte-for-byte unchanged from the
merged C1 version — only the `export` keyword was added to this one
function's existing declaration.

## `apps/atlas/src/shell/ChatTab.tsx` (new)

```typescript
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { derivePacketHeaderState } from "../thread/headerState";
import { textColorFor } from "../thread/PacketThread";
import { PACKET_A2_ENTRIES, ROLE_LABEL, type EntryRoleKey } from "../thread/fixtures";
import styles from "./ChatTab.module.css";

/**
 * Mobile chat-bubble colors from `Atlas Mobile.dc.html`'s real
 * `isThread` markup (lines 140-192 of the reference file), checked
 * directly against `colors.ts`. Real token matches: `colors.pageBgMobile`
 * (the feed's own background, `#F7F5FA`, line 146), `colors.accentHover`
 * (the "mine" name/bubble accent color, `#4A28CC`, matching the
 * reference file's real `renderVals()` logic — "mine" there means
 * `e.k === 'wk' || e.k === 'ow'`, i.e. Terra's own entries render with
 * this accent; no real entry in `PACKET_A2_ENTRIES` has `k === 'ow'`),
 * `colors.surface` (non-"mine" bubble background, the reference file's
 * own `#fff`), `colors.accentDeepest` (the `ar`-role name color,
 * `#3F1FC0` — unreachable by `PACKET_A2_ENTRIES` today, implemented in
 * full anyway per `nameColorFor`'s own doc comment below), and
 * `colors.borderDivider[0]` (the header's own bottom border,
 * `#EEEAF2` — the same real value C7's `PacketHeader.tsx` already
 * uses for an identical header border). One value has no equivalent
 * token and stays a disclosed literal, checked against every color
 * family: the "mine" bubble's own tinted background (`#EFEAFE`).
 * `colors.inkFaint` matches the role label's own real color (`#A79BB4`,
 * line 149) — self-caught before dispatch: the entry `<time>` element
 * on that same line uses a genuinely *different* real color, `#B9AFC4`,
 * which coincidentally matches a real border token,
 * `colors.borderDashed[2]`, reused here for text — an earlier draft
 * wrongly applied `inkFaint` to both.
 *
 * The header itself deliberately does NOT transcribe the reference
 * file's own literal one-line text, `"A.2 · Runtime Package"`
 * (`Atlas Mobile.dc.html:143`) — that string is neither of this
 * program's two already-established real identity fields
 * (`state.eyebrow`, `"m1-a · a.2"`; `state.title`, the full real
 * work-item name) and inventing a third, distinct abbreviated label
 * would violate this program's own fixture-content discipline. This
 * header instead reuses the exact same eyebrow/title pair C7's
 * `PacketHeader.tsx` already established as this packet's one real
 * identity — the README's own single-state-source rule, applied to a
 * second real surface.
 *
 * Unlike C1's desktop `PacketThread`, this view does NOT reuse
 * `computeShowAvatar`'s same-author grouping: the reference file's own
 * mobile `entries` derivation (`renderVals()`) has no such field at
 * all — every entry's name/role/time row renders unconditionally in
 * the real markup (line 149, inside a plain `sc-for`, no `sc-if`) —
 * so this component matches that literal, real structure rather than
 * importing a desktop-only enhancement the mockup's own mobile view
 * never exhibits.
 */
const SHELL_VARS = {
  "--atlas-feed-bg": colors.pageBgMobile,
  "--atlas-header-bg": colors.surface,
  "--atlas-header-border": colors.borderDivider[0],
  "--atlas-back": colors.accent,
  "--atlas-title": colors.ink,
  "--atlas-mine-bg": "#EFEAFE",
  "--atlas-other-bg": colors.surface,
  "--atlas-ink-faint": colors.inkFaint,
  "--atlas-time-color": colors.borderDashed[2],
  "--atlas-ink-muted": colors.inkMuted,
  // Same real value C7's `PacketHeader.tsx` already uses for its own
  // state-line/dot color, for the same reason: only the real blocked
  // trajectory exists today, and `colors.warningText`/`colors.warning`
  // are its real, checked colors there.
  "--atlas-state-color": colors.warningText,
  "--atlas-state-dot": colors.warning,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

function isMine(role: EntryRoleKey): boolean {
  return role === "wk" || role === "ow";
}

/**
 * The reference file's own full `nameColor` rule (`renderVals()`):
 * `e.k === 'ow' ? '#4A28CC' : e.k === 'ar' ? '#3F1FC0' : mine ?
 * '#4A28CC' : '#221C29'` — implemented in full, not reduced to the
 * two branches (`wk`/`co`) `PACKET_A2_ENTRIES` actually exercises
 * today, so a future real entry using `ow`/`ar` renders correctly
 * without this function needing a second look. `#4A28CC` is the real
 * `colors.accentHover`; `#3F1FC0` is the real `colors.accentDeepest`.
 */
function nameColorFor(role: EntryRoleKey): string {
  if (role === "ow") return colors.accentHover;
  if (role === "ar") return colors.accentDeepest;
  return isMine(role) ? colors.accentHover : colors.ink;
}

/**
 * Mobile "Chat" tab — the reference file's own `isThread` view,
 * reusing C1's real fixture (`PACKET_A2_ENTRIES`), role labels, and
 * text-color rule (`textColorFor`, exported from `PacketThread.tsx`
 * for this reuse), restyled as chat bubbles per the reference file's
 * own mobile markup, and C7's real `derivePacketHeaderState` for the
 * header (the same single state source every other real header
 * surface already reads from). No message composer or send control is
 * rendered: the reference file's own composer
 * (`Atlas Mobile.dc.html:193-197`) has no real backend counterpart
 * anywhere in M1/M2 — no command exists for sending a chat message to
 * an agent — so rendering an inert-but-visible composer would
 * misrepresent a capability this build does not have, the same
 * reasoning F1's `NowTab` already applied to its own excluded
 * Stop/Start/Open-conversation controls.
 */
export function ChatTab({ onBack }: { onBack: () => void }) {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.header}>
        <button type="button" className={styles.back} onClick={onBack}>
          ‹ Now
        </button>
        <span className={styles.eyebrow}>{state.eyebrow}</span>
        <h1 className={styles.title}>{state.title}</h1>
        <div className={styles.stateLine}>
          <span className={styles.dot} aria-hidden="true" />
          {state.stateLine}
        </div>
      </div>
      <div className={styles.feed}>
        {PACKET_A2_ENTRIES.map((entry) => {
          const mine = isMine(entry.k);
          return (
            <div key={`${entry.who}-${entry.time}`} className={styles.row}>
              <div className={styles.nameRow}>
                <span className={styles.name} style={{ color: nameColorFor(entry.k) }}>
                  {entry.who}
                </span>
                <span className={styles.role}>{ROLE_LABEL[entry.k]}</span>
                <time className={styles.time}>{entry.time}</time>
              </div>
              <div
                className={`${styles.bubble} ${mine ? styles.mine : styles.other}`}
                style={{ color: textColorFor(entry) }}
              >
                {entry.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ChatTab;
```

## `apps/atlas/src/shell/ChatTab.module.css` (new)

```css
.tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header {
  flex: none;
  padding: 6px 18px 12px;
  background: var(--atlas-header-bg);
  border-bottom: 1px solid var(--atlas-header-border);
}

.back {
  border: 0;
  background: transparent;
  color: var(--atlas-back);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.eyebrow {
  display: block;
  margin-top: 6px;
  font: 500 11px var(--atlas-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--atlas-ink-muted);
}

.title {
  margin: 4px 0 0;
  font-family: var(--atlas-font-display);
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.025em;
  color: var(--atlas-title);
}

.stateLine {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 5px;
  font-size: 13px;
  font-weight: 600;
  color: var(--atlas-state-color);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--atlas-state-dot);
}

.feed {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px 0 16px;
  background: var(--atlas-feed-bg);
}

.row {
  padding: 9px 18px;
}

.nameRow {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 5px;
}

.name {
  font-size: 13px;
  font-weight: 700;
}

.role {
  font-size: 12px;
  color: var(--atlas-ink-faint);
}

.time {
  margin-left: auto;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-time-color);
}

.bubble {
  max-width: 87%;
  padding: 12px 14px;
  border-radius: 18px;
  font-size: 14.5px;
  line-height: 1.55;
}

.mine {
  background: var(--atlas-mine-bg);
}

.other {
  background: var(--atlas-other-bg);
}
```

## `apps/atlas/src/shell/ChatTab.test.tsx` (new)

```typescript
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatTab } from "./ChatTab";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";

afterEach(cleanup);

describe("ChatTab", () => {
  it("renders the real eyebrow/title identity pair, the same single state source PacketHeader (C7) already reads from", () => {
    render(<ChatTab onBack={() => {}} />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText(state.eyebrow)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: state.title })).toBeInTheDocument();
    expect(screen.getByText(state.stateLine)).toBeInTheDocument();
  });

  it("renders all six real fixture messages, in order, with their exact body text", () => {
    render(<ChatTab onBack={() => {}} />);
    const bubbles = screen.getAllByText(/./, { selector: "[class*='bubble']" });
    expect(bubbles.map((b) => b.textContent)).toEqual(PACKET_A2_ENTRIES.map((e) => e.text));
  });

  it("shows every entry's own name/role/time row unconditionally, unlike C1's desktop grouping (the reference file's mobile view has no such grouping)", () => {
    render(<ChatTab onBack={() => {}} />);
    expect(screen.getAllByText("Coordinator")).toHaveLength(3);
    expect(screen.getAllByText("Terra")).toHaveLength(3);
    expect(screen.getAllByText("Implementor")).toHaveLength(3);
  });

  it("calls onBack when the '‹ Now' button is pressed", () => {
    const onBack = vi.fn();
    render(<ChatTab onBack={onBack} />);
    fireEvent.click(screen.getByRole("button", { name: "‹ Now" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders no message composer or send control (no real backend command exists for sending a chat message)", () => {
    render(<ChatTab onBack={() => {}} />);
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByRole("button", { name: /send/i })).toBeNull();
    expect(screen.queryByPlaceholderText(/message/i)).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ChatTab onBack={() => {}} />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## `apps/atlas/src/shell/MobileShell.tsx` (modified — full new content)

```typescript
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { NowTab } from "./NowTab";
import { ChatTab } from "./ChatTab";
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
      <main className={styles.content}>
        {selected === "now" ? (
          <NowTab />
        ) : selected === "chat" ? (
          <ChatTab onBack={() => setSelected("now")} />
        ) : (
          `${TAB_LABEL[selected]} tab`
        )}
      </main>
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

## `apps/atlas/src/shell/MobileShell.test.tsx` (modified — full new content)

```typescript
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
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
    // Scoped to the tab bar itself: F1's real Now-tab content also
    // contains real buttons (the reused owner-decision options), so an
    // unscoped `getAllByRole("button")` now picks those up too.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    const tabs = within(nav).getAllByRole("button");
    expect(tabs.map((t) => t.textContent)).toEqual(["Now", "Chat", "Plan", "Activity"]);
  });

  it("defaults to Now selected, with only one tab marked current, rendering the real Now tab (F1) rather than the placeholder", () => {
    render(<MobileShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
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

  it("(F2) tapping Chat renders the real ChatTab (F2) rather than the placeholder", () => {
    render(<MobileShell />);
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Chat" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Chat");
    expect(screen.getByRole("button", { name: "‹ Now" })).toBeInTheDocument();
    expect(screen.queryByText("Chat tab")).not.toBeInTheDocument();
  });

  it("(F2) ChatTab's own '‹ Now' back button returns to the real Now tab", () => {
    render(<MobileShell />);
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Chat" }));
    fireEvent.click(screen.getByRole("button", { name: "‹ Now" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<MobileShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (`/tmp/maestro-m2-f2`, branch `architecture/m2-f2`, base
`633167c`) and run through the real frontend toolchain from
`apps/atlas` (`npm install`, then each script below), before this
packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean, zero errors.
- `npm run lint` (`eslint .`) — clean, zero warnings or errors.
- `npm test` (`vitest run`) — **20/20 test files, 148/148 tests
  passed** on the first full run (zero self-caught test-ambiguity
  failures this time, unlike D2/F1 — the scoping lessons from those
  slices were applied up front: every new query in `ChatTab.test.tsx`
  and the new `MobileShell.test.tsx` assertions was checked for
  collision against `OwnerDecisionCard`'s own rendered content before
  writing it).
- `npm run build` (`vite build`) — clean, `38 modules transformed`, no
  warnings.

**Self-caught before dispatch (not found by an external review):**
auditing this slice's own `ChatTab.tsx` doc comment against the real
reference file line-by-line found the entry `<time>` element
(`Atlas Mobile.dc.html:149`) uses a genuinely different real color
(`#B9AFC4`) than the role label on the same line (`#A79BB4`,
`colors.inkFaint`) — an earlier draft had applied `inkFaint` to both.
Fixed by adding `colors.borderDashed[2]` (the real, if
coincidentally-named, match for `#B9AFC4`) as its own token, with the
mistake and fix disclosed directly in the doc comment above rather
than silently corrected. A second earlier draft mistakenly rendered a
per-message avatar bubble that does not exist anywhere in the
reference file's real mobile markup (conflating it with C1's desktop
card layout, which does show avatars) — caught by re-reading the
actual markup line-by-line before writing tests, removed before any
test was written against it.

**Independent Decision Fidelity review result:** `PASS WITH MINOR
NOTES`, zero blocking findings. The review independently reproduced
every quantitative claim (byte-exact citations, the full real
`nameColor`/`mine` rule, the token-routing audit, 20/20 test files,
148/148 tests, the `PacketThread.tsx` diff scope) and found them all
accurate. Three non-blocking notes were fixed at zero cost before
freeze, no planning correction consumed — matching this program's own
established precedent (e.g. M2-B4, M2-E1) for a clean pass with minor
findings:

1. The Evidence section's attribution of the `isThread`→`"chat"`
   internal naming fact to "B4's own disclosed README-vs-reference
   discrepancy fix" was inaccurate — B4's actually-disclosed
   discrepancy was about tab bar *order*, not this internal id. Fixed
   to state only the real, checked fact without the wrong attribution.
2. Guards item 6 overclaimed every `--atlas-*` var is consumed by
   "exactly one" CSS rule — `--atlas-font-mono` is legitimately
   consumed by two (`.eyebrow` and `.time`), sharing one real font
   token. Fixed to state the accurate, still-meaningful claim (no
   orphaned declaration), not a false stronger one.
3. `PACKET_A2_ENTRIES`' own `plan`/`cadence` fields (rendered as inline
   sub-panels in the reference file's real markup) were excluded
   without acknowledgment. Fixed: Guards item 4 now names this
   explicitly as an inherited, already-disclosed exclusion (from
   `fixtures.ts` and C1's own merged `PacketThread.tsx`), not a new gap
   this slice introduced or hid.

## M0-D12 bounded quality contract

1. **Protected outcome:** the mobile Atlas app's "Chat" tab renders
   the same real packet trajectory (Terra blocked, escalated) as chat
   bubbles — real fixture text, real per-entry name/role/time,
   real state-derived header identity and state line — with zero
   backend change, zero regression to any of the 20 existing test
   files, and a working, real back-navigation to the Now tab.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** F3 (Activity tab), F4 (Plan tab); any
   message composer or send control (no real backend command exists);
   `DecisionCard`/`OwnerDecisionCard`/`FidelityRecord`/`CrashCard`
   content inline in the feed (not present in the real reference
   markup for this view); `computeShowAvatar`'s desktop-only grouping
   behavior (not present in the real reference markup for this view).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every rendered surface is exercised by a
   React Testing Library render test; no browser-based visual
   verification was performed (tooling failure, already disclosed in
   this session for M2-E4/F1, same root cause).
5. **Acceptance proof:** 20/20 test files, 148/148 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 3 modified files (one a single-function
   export), 3 new files, all within `apps/atlas/src`; zero backend
   files; no new third-party dependency.
7. **Proportionality ceiling:** one exported existing function, one new
   presentational component, one new CSS module, one two-branch wiring
   change in an already-real shell — no new fixture data invented, no
   new design tokens invented.
8. **Stop and escalation rule:** rendering any decision/fidelity/crash
   card content inline, wiring a message-send control, or reusing
   desktop-only grouping behavior the real mobile markup does not
   exhibit, is explicitly out of scope — future work's job, not this
   one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F2-CHAT-TAB-01` |
| `phase` | `MergeReady` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f2-chat-tab.md"]` |
