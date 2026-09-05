# M2 Wave C — Wire Packet Thread Into Desktop Shell — Candidate 01

**Slice ID:** `MB-SLICE-M2-C1B-SHELL-WIRING-01`
**Status:** `Pending Decision Fidelity Review`
**Base:** `a219e57` (`origin/master`)

## Scope, deliberately minimal

A roadmap gap named explicitly by both B3's and C1's own frozen contracts
but never itself given a roadmap letter: wiring C1's standalone
`PacketThread` into B3's `DesktopShell`. B3's contract said *"C1 adds the
packet-list rows into the same nav between History and the divider,
exactly where the README places them"*; C1's contract said *"Wiring it
in requires adding packet-list nav rows to `DesktopShell`'s nav... this
program's next slice after this one, not part of it."* This is that
slice.

**Exactly one packet nav row is added: `A.2`.** Not the full `A.0`–`A.7`
list the README's nav paragraph describes. The reference file's real
`ENTRIES` object has thread data for only two packets, `A.1` and `A.2`;
C1 built `PacketThread` against `A.2` (the reference app's own default
selection). Adding nav rows for `A.0`, `A.1`, `A.3`–`A.7` now would
create clickable rows with no real thread content behind them — either
dead ends or invented placeholder content, both against this program's
standing rule against inventing data. A later slice can add `A.1`'s row
once something renders its thread, and further slices add the rest once
real (non-fixture) data exists via A2's `/snapshot/packets` endpoint —
this is exactly the kind of proportionate, fixture-completeness-driven
scope boundary this program has used since B2.

Source quote (`Atlas Explorations.dc.html`'s `renderVals`, the exact
computation this slice reproduces for the one packet it adds):

```js
packets: PACKETS.map(p => {
  const active = p.id === s.sel;
  return {
    onSelect: () => this.setState({ sel: p.id, tab: 'thread', view: 'packet' }),
    label: p.id + ' · ' + p.short,
    bg: active ? 'rgba(255,255,255,.13)' : 'transparent',
    color: active || p.state === 'run' ? '#FFFFFF' : '#B7ADC1',
    weight: active ? 600 : 400,
    dot: this.dot(p.id === 'A.2' && blocked ? 'need' : p.state, 9),
    isRunning: p.state === 'run' && !active,
  };
}),
```
```js
// PACKETS (the one row this slice uses):
{ id: 'A.2', short: 'Runtime Package', title: 'Add output-specific Runtime Package creation', state: 'run' }
```
```js
// blocked, from the same renderVals (the default-fixture scenario: the
// current packet is A.2, s.running is true, and nothing has been
// decided yet — exactly this slice's static, no-interaction scenario):
const blocked = cur.id === 'A.2' && s.running && !s.decided;
```
```js
// dot(state, size) — the 'need' branch this row's dot resolves to,
// because blocked is true and this row's id is 'A.2':
if (state === 'need') return b + 'background:#E0A32E;box-shadow:0 0 0 3px rgba(224,163,46,.26)';
```

So, for this slice's one static row: `label = "A.2 · Runtime Package"`;
text color is `#FFFFFF` (`colors.navTextActive`) always, because
`p.state === 'run'` is true regardless of selection; `weight` is `600`
when selected, `400` otherwise; the dot is the amber `need` variant
(`#E0A32E` with a `0 0 0 3px rgba(224,163,46,.26)` halo), not the plain
purple `run` dot, because this fixture's own thread ends in an
escalation (`escalate: true` on its last message, already built by C1) —
the dot is reporting a real fact already present in the merged fixture
data, not new interactive decision content. Selecting the row sets a new
`"packet"` shell view and renders `PacketThread` in the content pane;
`DesktopShell` does not otherwise know or care what `PacketThread`
renders.

**One pre-existing, unrelated discrepancy noted but explicitly NOT fixed
by this slice:** while sourcing the packet-row font-size (`14px`, from
the quote above) directly against the reference file, the same file's
`Performance`/`Agents`/`History` nav buttons (line 61) are *also*
`font-size:14px` — but the already-merged B3 `DesktopShell.module.css`
hardcodes `13.5px` for all four of its existing static rows. This is a
real, minor (0.5px) pre-existing inaccuracy in an already-shipped slice.
Fixing it is out of this slice's scope (it would mean editing
already-frozen, unrelated CSS for a cosmetic reason with no relation to
wiring the thread in) and is recorded here as a known, deferred,
non-blocking follow-up rather than silently ignored or silently fixed in
passing.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-C1B-SHELL-WIRING-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:a219e57"]` |

## Exact file contents

`apps/atlas/src/shell/DesktopShell.module.css` (modified — additive
only; every existing rule is untouched, verified below):

```css
/* Appended, after the existing .navDivider rule; nothing above this
   point in the real file changes. */

.packetRow {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 40px;
  padding: 8px 10px;
  border-radius: 8px;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font: 400 14px var(--atlas-font-body);
  color: var(--atlas-nav-text-running);
}

.packetRow:hover {
  background: var(--atlas-nav-hover-bg);
}

.packetRowActive {
  background: var(--atlas-nav-active-bg);
  font-weight: 600;
}

.packetLabel {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.packetDot {
  flex: none;
  display: inline-block;
  box-sizing: border-box;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--atlas-dot-need);
  box-shadow: 0 0 0 3px var(--atlas-dot-need-halo);
}
```

`apps/atlas/src/shell/DesktopShell.tsx` (modified — the exact diff is
described precisely below, not a full re-paste, since most of the file
is unchanged):

1. Add `"packet"` to the `DesktopShellView` union type:
   ```ts
   export type DesktopShellView = "performance" | "agents" | "history" | "gate" | "packet";
   ```
2. Add imports: `import PacketThread from "../thread/PacketThread";`
3. Add two new entries to `SHELL_VARS` (both real token properties, no
   new disclosed literal for the color; the halo is a disclosed literal
   since no rgba-with-alpha token exists):
   ```ts
   "--atlas-nav-text-running": colors.navTextActive,
   "--atlas-dot-need": colors.warning,
   // Not a token: the reference file's own halo alpha value for this
   // exact dot state (Atlas Explorations.dc.html's dot() function,
   // 'need' branch) — colors.warning's RGB (224,163,46) at .26 alpha,
   // no equivalent token exists for a translucent halo.
   "--atlas-dot-need-halo": "rgba(224,163,46,.26)",
   ```
4. Add a constant, next to `VIEW_LABEL`:
   ```ts
   const PACKET_A2_LABEL = "A.2 · Runtime Package";
   ```
5. In the `nav`, insert one new row between the `NAV_ROWS.map(...)` block
   and the `<div className={styles.navDivider} />` (i.e. between History
   and the Gate divider, exactly as B3's own contract anticipated):
   ```tsx
   <button
     type="button"
     className={`${styles.packetRow} ${selected === "packet" ? styles.packetRowActive : ""}`}
     aria-current={selected === "packet" ? "true" : undefined}
     onClick={() => setSelected("packet")}
   >
     <span className={styles.packetDot} aria-hidden="true" />
     <span className={styles.packetLabel}>{PACKET_A2_LABEL}</span>
   </button>
   ```
6. Change the content pane from unconditionally rendering
   `{VIEW_LABEL[selected]} view` to:
   ```tsx
   <main className={styles.content}>
     {selected === "packet" ? <PacketThread /> : `${VIEW_LABEL[selected]} view`}
   </main>
   ```
   (`VIEW_LABEL` itself is untouched — it has no `"packet"` key and
   needs none, since the packet branch never reads it.)

Every other line of `DesktopShell.tsx` — the `NavRow` component, the top
bar, the four static `NAV_ROWS`, the existing `SHELL_VARS` entries, the
gate row — is byte-identical to the current merged file.

`apps/atlas/src/shell/DesktopShell.test.tsx` (modified — additive only;
every existing test is untouched):

```tsx
// Added imports, alongside the existing ones:
import { PACKET_A2_ENTRIES } from "../thread/fixtures";

// Added tests, appended inside the existing describe("DesktopShell", ...) block:

it("renders the A.2 packet row between History and the M1-B gate row", () => {
  render(<DesktopShell />);
  const rows = screen.getAllByRole("button").map((r) => r.textContent);
  expect(rows).toEqual(["Performance", "Agents", "History", "A.2 · Runtime Package", "M1-B gate"]);
});

it("selecting the A.2 row shows the real packet thread, not a placeholder", () => {
  render(<DesktopShell />);
  fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
  const current = screen.getAllByRole("button", { current: true });
  expect(current).toHaveLength(1);
  expect(current[0]).toHaveTextContent("A.2");
  // PacketThread's own first fixture message, proving the real
  // component rendered, not a "packet view" placeholder string.
  expect(screen.getByText(PACKET_A2_ENTRIES[0].text)).toBeInTheDocument();
  expect(screen.queryByText("packet view")).not.toBeInTheDocument();
});

it("selecting a static row after the packet row correctly unmounts the thread", () => {
  render(<DesktopShell />);
  fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
  fireEvent.click(screen.getByRole("button", { name: "Agents" }));
  expect(screen.getByText("Agents view")).toBeInTheDocument();
  expect(screen.queryByText(PACKET_A2_ENTRIES[0].text)).not.toBeInTheDocument();
});
```

## Guards and boundary

1. This slice does not add any nav row other than `A.2` — no
   placeholder, no invented packet.
2. `PacketThread.tsx`, `PacketThread.module.css`, `fixtures.ts` are read
   (imported) but not modified — C1's fixture-transcription work is
   reused exactly as merged, not re-verified or re-derived.
3. Every existing rule in `DesktopShell.module.css` and every existing
   line of `DesktopShell.tsx`/`DesktopShell.test.tsx` not named above as
   changed is byte-identical to the currently merged files — this slice
   is purely additive to both.
4. No file under `apps/atlas/src/tokens/` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/shell/DesktopShell.module.css` (modified, additive)
- `apps/atlas/src/shell/DesktopShell.tsx` (modified, additive)
- `apps/atlas/src/shell/DesktopShell.test.tsx` (modified, additive)

No other path — in particular, nothing under `apps/atlas/src/thread/`
or `apps/atlas/src/tokens/` changes.

The 3 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the 3 new tests above
plus every existing `apps/atlas` test continuing to pass unmodified — 27
total after this slice (24 existing + 3 new). `npm run build` must still
succeed; unlike every prior Wave B/C slice, `PacketThread`'s fixture
content (e.g. `"Terra"`) is now expected to appear in the `dist/` bundle,
since this slice makes it the shell's first real consumer — the build
check for this slice is therefore the opposite of B2/B4/C1's: confirm
the string IS present, not absent.

### M0-D12 bounded quality contract

1. **Protected outcome:** clicking the one real packet nav row shows the
   real `PacketThread` component with its real fixture content; clicking
   away correctly unmounts it; every other nav row's existing behavior
   (from B3) is completely unaffected.
2. **Operating and threat model:** a trusted local dev box; a user
   clicking any nav row (including the new one) in any order.
3. **Explicit exclusions:** any nav row for a packet other than `A.2`;
   any change to `PacketThread`'s own content or logic; any change to
   the pre-existing, unrelated `13.5px` vs `14px` static-row font-size
   discrepancy noted above; any decision-card interactivity (the dot
   reports a real recorded fact, not a new control).
4. **Assurance level:** practical component-integration correctness,
   proportionate to wiring two already-reviewed components together with
   no new data or logic of its own.
5. **Acceptance proof:** the 3 named tests, the existing 24 `apps/atlas`
   tests continuing to pass (27 total), `npm run typecheck`, `npm run
   lint`, and `npm run build` (with `PacketThread` content now present in
   the bundle), all passing.
6. **Implementation boundary:** exactly the three writable paths above,
   all additive; no new npm dependency; the two new `SHELL_VARS` entries
   are a real token property and one disclosed literal, per the pattern
   every prior shell slice already established.
7. **Proportionality ceiling:** one new nav row, one new CSS rule set,
   one new content-pane branch; no generalized multi-packet nav-list
   component (that is real future work once more thread fixtures exist).
8. **Stop and escalation rule:** adding a second packet's nav row (e.g.
   `A.1`, once something renders its thread) is a new, separately
   reviewed slice, not an extension of this one after freeze. Fixing the
   noted `13.5px`/`14px` B3 discrepancy is also separate, future,
   optional work, not something this slice's freeze blocks on. A
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
