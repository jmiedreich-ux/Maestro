import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import DesktopShell from "./DesktopShell";
import styles from "./DesktopShell.module.css";

afterEach(cleanup);

describe("DesktopShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, not a hand-copied literal", () => {
    const { container } = render(<DesktopShell />);
    const root = container.firstChild as HTMLElement;
    // Corrected — non-blocking finding from Decision Fidelity review:
    // exhaustively checks every SHELL_VARS entry, including the
    // disclosed non-token literals — a prior draft spot-checked only 5
    // of 14 entries, which would not have caught the wrong-value
    // idle-grey defect review found by hand. G1 removed
    // `--atlas-idle-grey`/`--atlas-idle-label` (the live indicator's
    // colors are now computed per-render by `deriveConnectionState`
    // and applied via inline style, not a fixed custom property) and
    // added `--atlas-conn-body` (the connection strip's own fixed body
    // text color) — this list is updated to match.
    expect(root.style.getPropertyValue("--atlas-surface")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-border-divider")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-nav-ground")).toBe(colors.navGround);
    expect(root.style.getPropertyValue("--atlas-nav-text-inactive")).toBe(colors.navTextInactive);
    expect(root.style.getPropertyValue("--atlas-nav-text-active")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-nav-active-bg")).toBe(colors.navActiveBg);
    expect(root.style.getPropertyValue("--atlas-nav-hover-bg")).toBe(colors.navHoverBg);
    expect(root.style.getPropertyValue("--atlas-nav-divider")).toBe("rgba(255,255,255,.08)");
    expect(root.style.getPropertyValue("--atlas-page-bg-desktop")).toBe(colors.pageBgDesktop);
    expect(root.style.getPropertyValue("--atlas-font-mono")).toBe(fontFamily.mono);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-nav-text-running")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-dot-need")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-dot-need-halo")).toBe("rgba(224,163,46,.26)");
    expect(root.style.getPropertyValue("--atlas-conn-body")).toBe(colors.inkSecondary);
  });

  it("defaults to systemState 'normal': live indicator says 'idle' with real idle-token colors, no connection strip", () => {
    render(<DesktopShell />);
    const live = screen.getByText("idle").closest('[class*="liveIndicator"]') as HTMLElement;
    expect(live.style.getPropertyValue("--atlas-conn-live-text")).toBe(colors.inkFaint);
    expect(live.style.getPropertyValue("--atlas-conn-live-dot")).toBe(colors.inkMuted);
    expect(screen.queryByText("Reconnecting")).toBeNull();
  });

  it("systemState 'disconnected': live indicator flips to 'reconnecting' and the real connection strip renders", () => {
    render(<DesktopShell systemState="disconnected" />);
    expect(screen.getByText("reconnecting")).toBeInTheDocument();
    expect(screen.getByText("Reconnecting")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Atlas lost its connection at 14:58. Agents keep working — they report to the Coordinator, not to this window. What you see below is the last state Atlas received.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("retry 3 · 0:12")).toBeInTheDocument();
  });

  it("(G2) systemState 'crashed': the real danger-toned connection strip renders on every view, not just the packet view", () => {
    render(<DesktopShell systemState="crashed" />);
    expect(screen.getByText("Terra is not running")).toBeInTheDocument();
    expect(
      screen.getByText(
        "A.2 stopped without a handoff. Its worktree and locks are held, so A.3 stays undispatchable until this is resolved.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("stopped 14:58")).toBeInTheDocument();
    // The live indicator itself stays "idle" even mid-crash — this app
    // has no real live connection to claim either way.
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("(G2) systemState 'crashed': selecting the A.2 packet row renders the real CrashCard appended to the real thread", () => {
    render(<DesktopShell systemState="crashed" />);
    fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
    expect(screen.getByText("agent stopped unexpectedly")).toBeInTheDocument();
    // The real thread content is still there too — the crash card is
    // appended, not a replacement.
    expect(screen.getByText(PACKET_A2_ENTRIES[0].text)).toBeInTheDocument();
  });

  it("(G2) systemState 'crashed' has no effect on any other view's own content", () => {
    render(<DesktopShell systemState="crashed" />);
    fireEvent.click(screen.getByRole("button", { name: /^History/ }));
    expect(screen.getByText("History view")).toBeInTheDocument();
    expect(screen.queryByText("agent stopped unexpectedly")).toBeNull();
  });

  it("renders the top bar's idle live indicator", () => {
    render(<DesktopShell />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("renders the four static nav rows plus the packet row, in order", () => {
    render(<DesktopShell />);
    const rows = screen.getAllByRole("button");
    expect(rows.map((row) => row.textContent?.replace("—", "").trim())).toEqual([
      "Performance",
      "Agents",
      "History",
      "A.2 · Runtime Package",
      "M1-B gate",
    ]);
  });

  it("defaults to Performance selected, with only one row marked current", () => {
    render(<DesktopShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Performance");
    expect(screen.getByText("Performance view")).toBeInTheDocument();
  });

  it("clicking a row makes it the sole selected row and updates the content pane", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /History/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
    expect(screen.getByText("History view")).toBeInTheDocument();
    expect(screen.queryByText("Performance view")).not.toBeInTheDocument();
  });

  it("never renders a literal 0 for the unavailable nav counts", () => {
    render(<DesktopShell />);
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(4);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<DesktopShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });

  it("renders the A.2 packet row between History and the M1-B gate row", () => {
    render(<DesktopShell />);
    // Corrected: the real NavRow always appends a trailing mono count
    // span ("—") to its own text, exactly like the pre-existing "renders
    // exactly four static nav rows" test already accounts for — this
    // test's first draft omitted that same normalization and failed
    // against the real rendered output.
    const rows = screen
      .getAllByRole("button")
      .map((r) => r.textContent?.replace("—", "").trim());
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
    // Corrected: the real accessible name is "Agents—" (the trailing
    // mono count), so the exact string "Agents" never matches — the same
    // class of fix as the test above, using a regex here instead since
    // this call needs to select one specific row, not compare a full list.
    fireEvent.click(screen.getByRole("button", { name: /^Agents/ }));
    expect(screen.getByText("Agents view")).toBeInTheDocument();
    expect(screen.queryByText(PACKET_A2_ENTRIES[0].text)).not.toBeInTheDocument();
  });

  it("(E7C) selecting the M1-B gate row renders the real GateHeader and GateCriteriaList, not the placeholder", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("M1-B gate");

    // Real GateHeader content.
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
    expect(screen.getByText("approver")).toBeInTheDocument();
    // Real GateCriteriaList content.
    expect(screen.getByText("entry criteria")).toBeInTheDocument();
    expect(screen.getByText("A.0 through A.7 accepted")).toBeInTheDocument();

    expect(screen.queryByText("M1-B gate view")).not.toBeInTheDocument();
  });

  it("(E7C) selecting a different static row after the gate row correctly unmounts GateHeader/GateCriteriaList", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Performance/ }));
    expect(screen.getByText("Performance view")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Overlay and support surfaces" })).not.toBeInTheDocument();
    expect(screen.queryByText("entry criteria")).not.toBeInTheDocument();
  });

  it("(E7C, corrected — Decision Fidelity review finding) the gate view's <main> uses the no-padding .contentGate class, and every other view keeps the padded .content class", () => {
    // The reviewer proved this by mutation-testing: reverting the gate
    // view's className from `styles.contentGate` back to `styles.content`
    // (the exact regression Design Rationale #1 exists to avoid — doubling
    // GateHeader's own 34px gutter) left all other tests passing, since
    // none of them asserted on <main>'s own className. This test compares
    // against the real imported CSS-module identifiers, not hand-typed
    // strings, so it fails under that exact mutation.
    render(<DesktopShell />);
    const main = screen.getByTestId("desktop-shell-main");
    expect(main.className).toBe(styles.content);
    expect(main.className).not.toBe(styles.contentGate);

    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    expect(main.className).toBe(styles.contentGate);
    expect(main.className).not.toBe(styles.content);

    fireEvent.click(screen.getByRole("button", { name: /^Performance/ }));
    expect(main.className).toBe(styles.content);
  });
});
