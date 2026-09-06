import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";
import { AGENTS, AGENTS_STATS } from "../agents/agents";
import { WEEKLY_WINDOW } from "../performance/weeklyWindow";
import { SPLIT, SPLIT_BASES } from "../performance/perfBreakdown";

afterEach(cleanup);

describe("ActivityTab", () => {
  it("renders the real page title and defaults to the History segment selected", () => {
    render(<ActivityTab />);
    expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
  });

  it("renders exactly three segments, in the reference file's own order", () => {
    render(<ActivityTab />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual(["History", "Agents", "Cost"]);
  });

  it("renders all 4 real HISTORY_STATS", () => {
    const { container } = render(<ActivityTab />);
    // Two real stats ("Corrections spent" and "Decisions recorded")
    // share the same real value ("1"), so each stat's label+value pair
    // is checked as one concatenated text run (each label is unique,
    // even though two values collide) rather than querying the value
    // alone document-wide.
    for (const stat of HISTORY_STATS) {
      const label = screen.getByText(stat.label);
      expect(label.textContent).toBe(`${stat.label}${stat.value}`);
    }
    expect(container.textContent).toContain(HISTORY_STATS[0].label);
  });

  it("renders all 10 real HISTORY_ENTRIES, in order, with their exact titles", () => {
    render(<ActivityTab />);
    const titles = screen.getAllByText(/./, { selector: "[class*='entryTitle']" });
    expect(titles.map((t) => t.textContent)).toEqual(HISTORY_ENTRIES.map((e) => e.title));
  });

  it("renders the real trailing empty-timeline note, reusing E6's own established constant", () => {
    render(<ActivityTab />);
    expect(screen.getByText(HISTORY_EMPTY_NOTE)).toBeInTheDocument();
  });

  it("renders no 'Open ... thread' button, unlike desktop History (the real mobile markup has no such control here)", () => {
    render(<ActivityTab />);
    expect(screen.queryByRole("button", { name: /open .* thread/i })).toBeNull();
  });

  it("tapping Cost switches the segmented control's own selection and renders the real weekly-window card", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));
    const current = screen.getAllByRole("button", { current: true });
    // Scoped to the outer segmented control only: the split card's own
    // segmented control (Cost/Tokens/Time) also uses `aria-current`-free
    // plain buttons here, but its own selected button carries no
    // `current` role attribute, so this stays unambiguous.
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Cost");

    expect(screen.getByText("openai weekly window")).toBeInTheDocument();
    // Real fixture fields, not the mobile mockup's own shorter,
    // compressed single line — see this file's own doc comment.
    expect(screen.getByText(WEEKLY_WINDOW.meta)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.caption)).toBeInTheDocument();
    expect(screen.getByText(`${WEEKLY_WINDOW.unattributedPercent} unattributed`)).toBeInTheDocument();
    expect(screen.getByText(`${WEEKLY_WINDOW.observedChangePercent}`)).toBeInTheDocument();
  });

  it("renders the real 'm1-a split' card defaulting to the Cost basis, with all real role and work parts", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    expect(screen.getByText("m1-a split")).toBeInTheDocument();
    expect(screen.getByText("by role")).toBeInTheDocument();
    expect(screen.getByText("by kind of work")).toBeInTheDocument();

    const data = SPLIT.cost;
    expect(screen.getByText(`share of ${data.note}`)).toBeInTheDocument();
    expect(screen.getByText(data.caveat)).toBeInTheDocument();
    for (const part of [...data.role, ...data.work]) {
      const label = screen.getByText(part.label);
      const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
      expect(within(item).getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(within(item).getByText(part.abs)).toBeInTheDocument();
    }
  });

  it("tapping Tokens or Time in the split card's own segmented control switches to that basis's real data", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const basis of SPLIT_BASES) {
      if (basis.key === "cost") continue;
      fireEvent.click(screen.getByRole("button", { name: basis.label }));
      const data = SPLIT[basis.key];
      expect(screen.getByText(`share of ${data.note}`)).toBeInTheDocument();
      expect(screen.getByText(data.caveat)).toBeInTheDocument();
      // The previous basis's own caveat must not linger.
      for (const other of SPLIT_BASES) {
        if (other.key === basis.key) continue;
        expect(screen.queryByText(SPLIT[other.key].caveat)).toBeNull();
      }
      // Every real role/work part for this basis, not just the note/caveat
      // strings — proves the switch re-derives the whole group, not just
      // the two summary lines.
      for (const part of [...data.role, ...data.work]) {
        const label = screen.getByText(part.label);
        const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
        expect(within(item).getByText(`${part.pct}%`)).toBeInTheDocument();
        expect(within(item).getByText(part.abs)).toBeInTheDocument();
      }
    }
  });

  it("tapping Agents switches the segmented control's own selection and renders the real AGENTS_STATS", () => {
    const { container } = render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Agents");

    // Every real AGENTS_STATS label is unique, so a bare label lookup
    // is unambiguous here (unlike HISTORY_STATS' shared "1" value).
    for (const stat of AGENTS_STATS) {
      const label = screen.getByText(stat.label);
      expect(label.textContent).toBe(`${stat.label}${stat.value}`);
    }
    expect(container.textContent).toContain(AGENTS_STATS[0].label);
  });

  it("renders all 4 real AGENTS cards with their exact name, state, and line", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      // "Coordinator" is both this real agent's name and its own role —
      // scope each assertion to that one card, found via its unique
      // real `line` text, to avoid an ambiguous document-wide query.
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      expect(within(card).getByText(agent.name)).toBeInTheDocument();
      expect(within(card).getByText(agent.state)).toBeInTheDocument();
      expect(within(card).getByText(agent.packet)).toBeInTheDocument();
      expect(within(card).getByText(agent.locks)).toBeInTheDocument();
    }
  });

  it("renders each real agent's exact progress-bar width, progress label, and due label with the correct urgent styling", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      const fill = card.querySelector('[class*="agentBarFill"]') as HTMLElement;
      expect(fill.style.width).toBe(agent.pct);

      const due = within(card).getByText(agent.due);
      expect(within(card).getByText(agent.progress)).toBeInTheDocument();
      // Only Coordinator's real fixture entry has `urgent: true` — every
      // other real agent must render the non-urgent due class instead.
      expect(due.className).toContain(agent.urgent ? "agentDueUrgent" : "agentDue");
      if (!agent.urgent) {
        expect(due.className).not.toContain("agentDueUrgent");
      }
    }
  });

  it("renders a hollow state dot only for Sol (the real fixture's only 'wait' styleKey), filled for the other 3", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      const dot = card.querySelector('[class*="agentStateDot"]') as HTMLElement;
      const isWait = agent.styleKey === "wait";
      expect(dot.className.includes("agentStateDotHollow")).toBe(isWait);
      if (isWait) {
        expect(dot.style.background).toBe("transparent");
      } else {
        expect(dot.style.background).not.toBe("");
        expect(dot.style.background).not.toBe("transparent");
      }
    }
  });

  it("renders no 'Open thread' button on the mobile Agents cards (the real mobile markup has no such control here)", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    expect(screen.queryByRole("button", { name: /open thread/i })).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ActivityTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
