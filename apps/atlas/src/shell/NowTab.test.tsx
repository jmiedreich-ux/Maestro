import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NowTab } from "./NowTab";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";

afterEach(cleanup);

describe("NowTab", () => {
  it("renders the real hero card identity, headline, and subline, all from one derived state object", () => {
    const { container } = render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    // Scoped to the hero card: the reused OwnerDecisionCard below it also
    // renders "Terra" (its own real chain-of-escalation chip).
    const hero = container.querySelector('[class*="hero"]') as HTMLElement;
    expect(within(hero).getByText("Terra")).toBeInTheDocument();
    expect(within(hero).getByText("Implementor · A.2 Runtime Package")).toBeInTheDocument();
    // Hardcoded literals, not just cross-checked against the function's own
    // live return value — a wording regression inside
    // derivePacketHeaderState itself must still fail this test.
    expect(state.headline).toBe("Blocked");
    expect(state.subline).toBe("Escalated to you · worktree held");
    expect(within(hero).getByText(state.headline)).toBeInTheDocument();
    expect(within(hero).getByText(state.subline)).toBeInTheDocument();
  });

  it("renders the real 40% progress fill width, derived from the real fixture's plan steps", () => {
    const { container } = render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.progressPercent).toBe(40);
    const fill = container.querySelector('[class*="fill"]') as HTMLElement;
    expect(fill.style.width).toBe("40%");
  });

  it("renders the real boundary timestamps", () => {
    render(<NowTab />);
    expect(screen.getByText("began 13:51")).toBeInTheDocument();
    expect(screen.getByText("held at 14:52")).toBeInTheDocument();
  });

  it("renders the meta grid's Last report and Blocker, consistent with the derived state", () => {
    render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText("Last report")).toBeInTheDocument();
    expect(screen.getByText(state.lastReport)).toBeInTheDocument();
    expect(screen.getByText("Blocker")).toBeInTheDocument();
    expect(screen.getByText(state.blocker)).toBeInTheDocument();
  });

  it("renders the real owner-decision card (C4, reused verbatim) because this real trajectory is blocked", () => {
    render(<NowTab />);
    expect(
      screen.getByText(
        "Should a theme-free output get a sentinel version, or does the frozen contract change?",
      ),
    ).toBeInTheDocument();
  });

  it("renders the 'what happens next' panel with the real derived text", () => {
    render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    // Hardcoded literal, not just cross-checked against the function's own
    // live return value — a wording regression inside
    // derivePacketHeaderState itself must still fail this test.
    expect(state.nextPanelText).toBe(
      "Nothing is expected from Terra until you answer — its worktree stays held while the packet is blocked.",
    );
    expect(screen.getByText("what happens next")).toBeInTheDocument();
    expect(screen.getByText(state.nextPanelText)).toBeInTheDocument();
  });

  it("renders no Stop/Start or Open-conversation control (no real backend command exists for them yet)", () => {
    render(<NowTab />);
    expect(screen.queryByRole("button", { name: /stop/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /start/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /open conversation/i })).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<NowTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
