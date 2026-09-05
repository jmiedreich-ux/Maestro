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
