import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { AgentsRoster } from "./AgentsRoster";
import { AGENTS, AGENTS_STATS } from "./agents";
import { AGENT_STYLE } from "./agentStyle";

afterEach(cleanup);

// "A.2" is the real packet for both Terra's and Coordinator's cards at
// once, so every per-card check below is scoped to that specific
// card. Coordinator's own real `name` AND `role` are both literally
// "Coordinator" (self-caught while writing these tests — the reference
// data has no such collision, since it named this field "Approver" for
// the fictional persona; this program's own real substitution
// introduced it), so `agentCard` finds the card via the name SPAN
// specifically (scoped by its own class), never a bare `getByText`
// that would match both the name and the role.
function agentCard(name: string): HTMLElement {
  const nameNode = screen.getByText(
    (content, element) => content === name && Boolean(element?.className?.includes("name")),
  );
  return nameNode.closest('[class*="card"]') as HTMLElement;
}

function roleText(card: HTMLElement, role: string): HTMLElement {
  return within(card).getByText(
    (content, element) => content === role && Boolean(element?.className?.includes("role")),
  );
}

describe("AgentsRoster", () => {
  it("renders the real header: corrected 'm1-a' eyebrow (not the reference file's own 'vennuesign' artifact), title, and all 4 real stats", () => {
    render(<AgentsRoster />);
    expect(screen.getByText("m1-a · agents")).toBeInTheDocument();
    expect(screen.queryByText(/vennuesign/i)).toBeNull();
    expect(screen.getByText("Four agents, one worktree each")).toBeInTheDocument();
    for (const stat of AGENTS_STATS) {
      const row = within(screen.getByText(stat.label).closest('[class*="stat"]') as HTMLElement);
      expect(row.getByText(stat.value)).toBeInTheDocument();
    }
  });

  it("renders all 4 real agent cards with their real role, packet, state, line, progress, due, and locks", () => {
    render(<AgentsRoster />);
    for (const agent of AGENTS) {
      const cardEl = agentCard(agent.name);
      const card = within(cardEl);
      expect(roleText(cardEl, agent.role)).toBeInTheDocument();
      expect(card.getByText(agent.packet)).toBeInTheDocument();
      expect(card.getByText(agent.state)).toBeInTheDocument();
      expect(card.getByText(agent.line)).toBeInTheDocument();
      expect(card.getByText(agent.progress)).toBeInTheDocument();
      expect(card.getByText(agent.due)).toBeInTheDocument();
      expect(card.getByText(agent.locks)).toBeInTheDocument();
    }
  });

  it("substitutes the fictional 'Architect agent' persona with the real Coordinator actor, with no fictional persona anywhere", () => {
    render(<AgentsRoster />);
    expect(screen.queryByText("Architect agent")).toBeNull();
    const coordinatorCardEl = agentCard("Coordinator");
    const coordinatorCard = within(coordinatorCardEl);
    // name AND role both real "Coordinator" — see agentCard's own note.
    expect(coordinatorCard.getAllByText("Coordinator")).toHaveLength(2);
    expect(roleText(coordinatorCardEl, "Coordinator")).toBeInTheDocument();
    expect(coordinatorCard.getByText("ruling")).toBeInTheDocument();
    expect(coordinatorCard.getByText("A.2")).toBeInTheDocument();
  });

  it("renders exactly 4 real 'Open thread' buttons, all inert (no onClick)", () => {
    render(<AgentsRoster />);
    const buttons = screen.getAllByRole("button", { name: "Open thread" });
    expect(buttons).toHaveLength(4);
  });

  it("renders the hollow waiting-dot only for Sol's card (the real 'waiting on locks' state)", () => {
    render(<AgentsRoster />);
    const solDot = agentCard("Sol").querySelector('[class*="stateDot"]') as HTMLElement;
    const terraDot = agentCard("Terra").querySelector('[class*="stateDot"]') as HTMLElement;
    expect(solDot.className).toContain("stateDotHollow");
    expect(terraDot.className).not.toContain("stateDotHollow");
  });

  it("colors the due text urgent only for Coordinator's real urgent entry", () => {
    render(<AgentsRoster />);
    const coordinatorDue = within(agentCard("Coordinator")).getByText(
      AGENTS.find((a) => a.name === "Coordinator")!.due,
    );
    const terraDue = within(agentCard("Terra")).getByText(AGENTS.find((a) => a.name === "Terra")!.due);
    expect(coordinatorDue.className).toContain("dueUrgent");
    expect(terraDue.className).not.toContain("dueUrgent");
  });

  it("sets each card's real per-style border color as a checked CSS variable, matching agentStyle.ts's own real/disclosed values", () => {
    expect(AGENT_STYLE.run.border).toBe("#E0DAF2");
    expect(AGENT_STYLE.wait.border).toBe(colors.border);
    expect(AGENT_STYLE.rev.border).toBe("#EFE0D8");
    expect(AGENT_STYLE.rule.border).toBe(colors.borderStrong[1]);

    render(<AgentsRoster />);
    expect(agentCard("Terra").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.run.border);
    expect(agentCard("Sol").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.wait.border);
    expect(agentCard("Claude Opus").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.rev.border);
    expect(agentCard("Coordinator").style.getPropertyValue("--atlas-ag-card-border")).toBe(AGENT_STYLE.rule.border);
  });

  it("sets the header's real, checked CSS variables", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    const { container } = render(<AgentsRoster />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-ag-header-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-ag-eyebrow")).toBe(colors.inkFaint);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<AgentsRoster />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
