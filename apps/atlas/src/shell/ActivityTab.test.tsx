import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";
import { AGENTS, AGENTS_STATS } from "../agents/agents";
import { WEEKLY_WINDOW } from "../performance/weeklyWindow";
import { SPLIT, SPLIT_BASES } from "../performance/perfBreakdown";
import { PERF_RECORDS } from "../performance/perfRecords";
import { colors } from "../tokens";

const SPLIT_COLORS = [colors.accent, colors.review, colors.success, colors.borderDashed[2]];

/**
 * jsdom (like real browsers) silently re-serializes a raw inline hex
 * color to `rgb(...)` when read back via `.style.background` — so an
 * exact-string comparison against the original hex literal must
 * convert through the same normalization first, matching the
 * discipline this program's own `connectionState.ts` (G1) already
 * established for exactly this defect class.
 */
function hexToRgb(hex: string): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

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

  it("renders each real split part's own bar-segment width (with the real 0.6% floor) and legend-dot color by real index", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const group of [SPLIT.cost.role, SPLIT.cost.work]) {
      group.forEach((part, index) => {
        const label = screen.getByText(part.label);
        const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
        const dot = item.querySelector('[class*="splitLegendDot"]') as HTMLElement;
        expect(dot.style.background).toBe(hexToRgb(SPLIT_COLORS[index]));

        // Every real 0%-share part still renders a thin, visible sliver
        // (Math.max(pct, 0.6)), never a fully collapsed 0% bar segment.
        const group2 = item.closest('[class*="splitGroup"]') as HTMLElement;
        const bar = group2.querySelector('[class*="splitBar"]') as HTMLElement;
        const segment = bar.children[index] as HTMLElement;
        const expectedWidth = `${Math.max(part.pct, 0.6)}%`;
        expect(segment.style.width).toBe(expectedWidth);
        expect(segment.style.background).toBe(hexToRgb(SPLIT_COLORS[index]));
      });
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

  it("(F3D) renders the real 'Per action' header with a derived, not hand-typed, record count", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    expect(screen.getByText("Per action")).toBeInTheDocument();
    expect(screen.getByText(`${PERF_RECORDS.length} records`)).toBeInTheDocument();
  });

  it("(F3D) renders every real PERF_RECORDS card, closed by default, with its exact action/outcome/meta/stat-line text", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const card = action.closest('[class*="recordCard"]') as HTMLElement;
      expect(within(card).getByText(record.outcome)).toBeInTheDocument();
      expect(
        within(card).getByText(`${record.packet} · ${record.who} · ${record.model}`),
      ).toBeInTheDocument();
      expect(within(card).getByText(record.tokens)).toBeInTheDocument();
      expect(within(card).getByText(record.cost)).toBeInTheDocument();
      expect(within(card).getByText(record.elapsed)).toBeInTheDocument();
      // Closed by default: no detail group name or note text is present.
      for (const group of record.groups) {
        expect(within(card).queryByText(group.name)).toBeNull();
      }
      expect(within(card).queryByText(record.note)).toBeNull();
    }
  });

  it("(F3D) each real record's own outcome tag and cost carry the exact real token color class, transcribed from PerfRecordsList's own mapping", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    // These colors are applied via a CSS-module class (matching
    // PerfRecordsList.tsx's own established convention for this exact
    // outcome/cost mapping), not an inline style — so, matching that
    // file's own test convention, this asserts class membership, not
    // `.style`, which jsdom never populates for CSS-module rules.
    const outcomeClassName: Record<string, string> = {
      blocked: "recordsOutcomeBlocked",
      approved: "recordsOutcomeGood",
      passed: "recordsOutcomeGood",
      complete: "recordsOutcomeNeutral",
    };
    const costClassName: Record<string, string> = {
      billed: "recordCostBilled",
      est: "recordCostEst",
      none: "recordCostNone",
    };

    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const card = action.closest('[class*="recordCard"]') as HTMLElement;
      const outcome = within(card).getByText(record.outcome);
      expect(outcome.className).toContain(outcomeClassName[record.outcome]);

      const cost = within(card).getByText(record.cost);
      expect(cost.className).toContain(costClassName[record.costKind]);
    }
  });

  it("(F3D) clicking a record's own button opens its real detail groups/rows/note, and closes whichever other record was open (single accordion state)", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    const first = PERF_RECORDS[0];
    const second = PERF_RECORDS[1];

    fireEvent.click(screen.getByText(first.action));
    const firstCard = screen.getByText(first.action).closest('[class*="recordCard"]') as HTMLElement;
    expect(first.groups).toHaveLength(3);
    for (const group of first.groups) {
      // Some real records repeat a value string across two rows within
      // the same open card (e.g. p1's "unavailable" appears twice, and
      // p1's own elapsed "0.9s" repeats between the closed button row
      // and its own detail row) — so, matching PerfRecordsList.test.tsx's
      // own established pattern, this scopes to each group's own name
      // node's `parentElement` and only asserts row *labels* here
      // (always unique per group), not row values.
      const groupNode = screen.getByText(group.name).parentElement as HTMLElement;
      const groupScope = within(groupNode);
      for (const row of group.rows) {
        expect(groupScope.getByText(row.label)).toBeInTheDocument();
      }
    }
    expect(within(firstCard).getByText(first.note)).toBeInTheDocument();

    // Opening the second record closes the first — a single shared
    // `openId`, not one independent boolean per record.
    fireEvent.click(screen.getByText(second.action));
    const secondCard = screen.getByText(second.action).closest('[class*="recordCard"]') as HTMLElement;
    expect(within(secondCard).getByText(second.note)).toBeInTheDocument();
    expect(within(firstCard).queryByText(first.note)).toBeNull();

    // Clicking the open record again closes it.
    fireEvent.click(screen.getByText(second.action));
    expect(within(secondCard).queryByText(second.note)).toBeNull();
  });

  it("(F3D) each real detail row's own value carries the exact real token color class for its PerfDetailKind, transcribed from PerfRecordsList's own mapping", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    const detailValueClassName: Record<string, string> = {
      "": "recordDetailValueDefault",
      est: "recordDetailValueEst",
      ok: "recordDetailValueOk",
      warn: "recordDetailValueWarn",
      na: "recordDetailValueNa",
    };

    // Every kind must appear at least once across the real fixture, or
    // this test would pass vacuously without ever exercising a branch.
    const seenKinds = new Set<string>();

    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const card = action.closest('[class*="recordCard"]') as HTMLElement;
      fireEvent.click(action);
      for (const group of record.groups) {
        for (const row of group.rows) {
          seenKinds.add(row.kind);
          // Scoped to this record's own card first (its row label, e.g.
          // "Cost", would otherwise collide with the outer segmented
          // control's own "Cost" tab and the split card's own "Cost"
          // basis button — the exact latent test-scoping trap the F3C
          // Decision Fidelity review pre-disclosed for this slice), then
          // to the row's own label -> parentElement, matching
          // PerfRecordsList.test.tsx's own established pattern (some
          // real records also repeat a value string across two rows).
          const rowNode = within(card).getByText(row.label).parentElement as HTMLElement;
          const value = within(rowNode).getByText(row.value);
          expect(value.className).toContain(detailValueClassName[row.kind]);
        }
      }
      fireEvent.click(action);
    }

    expect(seenKinds.size).toBeGreaterThan(1);
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
