import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { colors, fontFamily } from "../tokens";
import MobileShell from "./MobileShell";

// ChatTab (F2) now always fetches real backend data — every test that
// can reach it needs a real (mocked) fetch/EventSource, matching the
// same pattern DesktopShell.test.tsx's own real-wiring tests already
// established.
class FakeEventSource {
  onmessage: unknown = null;
  addEventListener() {}
  close() {}
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: [] }) }));
  vi.stubGlobal("EventSource", FakeEventSource);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

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

  it("(F4A) tapping Plan renders the real PlanTab rather than the placeholder", () => {
    render(<MobileShell />);
    // Scoped to the tab bar: PlanTab's own packet rows and gate row are
    // also real buttons, which would otherwise collide with an unscoped
    // current-button query.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Plan" }));
    const current = within(nav).getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Plan");
    expect(screen.getByRole("heading", { name: "Plan" })).toBeInTheDocument();
    expect(screen.queryByText("Plan tab")).not.toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("(F3) tapping Activity renders the real ActivityTab (F3) rather than the placeholder", () => {
    render(<MobileShell />);
    // Scoped to the tab bar: ActivityTab's own segmented control also
    // sets aria-current on its selected segment button, which would
    // otherwise collide with an unscoped current-button query.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Activity" }));
    const current = within(nav).getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Activity");
    expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
    expect(screen.queryByText("Activity tab")).not.toBeInTheDocument();
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
