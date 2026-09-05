import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PerfRecordsList } from "./PerfRecordsList";
import { PERF_RECORDS } from "./perfRecords";

afterEach(cleanup);

describe("PerfRecordsList", () => {
  it("renders all 5 real records with their action, packet/who, model, tokens, cost, and elapsed", () => {
    render(<PerfRecordsList />);
    // `action` is the one field unique per record (three records share
    // the real "A.2 · Terra" packet/who pair), so each record's row is
    // found via its own action text, then every other field is checked
    // scoped to that same row — not a bare, ambiguous getByText.
    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const row = action.closest("button") as HTMLElement;
      expect(row).not.toBeNull();
      const rowScope = within(row);
      expect(rowScope.getByText(`${record.packet} · ${record.who}`)).toBeInTheDocument();
      expect(rowScope.getByText(record.model)).toBeInTheDocument();
      expect(rowScope.getByText(record.tokens)).toBeInTheDocument();
      expect(rowScope.getByText(record.cost)).toBeInTheDocument();
      expect(rowScope.getByText(record.elapsed)).toBeInTheDocument();
    }
  });

  it("renders exactly 5 inert row buttons, each with an outcome tag", () => {
    render(<PerfRecordsList />);
    expect(screen.getAllByRole("button")).toHaveLength(5);
    expect(screen.getAllByText("passed")).toHaveLength(2);
    expect(screen.getByText("complete")).toBeInTheDocument();
    expect(screen.getByText("blocked")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
  });

  it("colors the blocked outcome tag with the warning chip, and passed/approved with the success wash, matching the reference file's real per-outcome mapping", () => {
    render(<PerfRecordsList />);
    const blocked = screen.getByText("blocked");
    const approved = screen.getByText("approved");
    const complete = screen.getByText("complete");
    expect(blocked.className).toContain("outcomeBlocked");
    expect(approved.className).toContain("outcomeGood");
    expect(complete.className).toContain("outcomeNeutral");
  });

  it("colors billed costs ink, estimated costs amber, and non-billed costs muted, matching the reference file's real per-record costKind mapping", () => {
    render(<PerfRecordsList />);
    const billed = screen.getByText("$0.41 billed");
    const estimated = screen.getByText("$0.52 estimated");
    const notBilled = screen.getByText("not billed");
    expect(billed.className).toContain("costBilled");
    expect(estimated.className).toContain("costEst");
    expect(notBilled.className).toContain("costNone");
  });

  it("sets the card border/surface and tag CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.warningChip).toBe("#FDF1DC");
    expect(colors.successWash).toBe("#E4F6EE");
    const { container } = render(<PerfRecordsList />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-perf-card-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-perf-tag-blocked-bg")).toBe(colors.warningChip);
    expect(root.style.getPropertyValue("--atlas-perf-tag-good-bg")).toBe(colors.successWash);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PerfRecordsList />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
