import { render, screen, cleanup, within, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, motion } from "../tokens";
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

  it("renders exactly 5 row buttons, each with an outcome tag, and no detail panel until opened", () => {
    render(<PerfRecordsList />);
    expect(screen.getAllByRole("button")).toHaveLength(5);
    expect(screen.getAllByText("passed")).toHaveLength(2);
    expect(screen.getByText("complete")).toBeInTheDocument();
    expect(screen.getByText("blocked")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
    for (const record of PERF_RECORDS) {
      expect(screen.queryByText(record.note)).toBeNull();
    }
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

  it("clicking a row's button opens its own real detail panel, with all 3 real groups and every real row label", () => {
    render(<PerfRecordsList />);
    const record = PERF_RECORDS[0];
    const button = screen.getByText(record.action).closest("button") as HTMLElement;
    fireEvent.click(button);

    expect(screen.getByText(record.note)).toBeInTheDocument();
    expect(record.groups).toHaveLength(3);
    for (const group of record.groups) {
      // `group.name` renders inside its own `.detailGroupName` div, a
      // direct child of the `.detailGroup` wrapper that also holds the
      // rows — so `parentElement`, not `closest("div")` (which would
      // just return the name div itself, since it is one).
      const groupNode = screen.getByText(group.name).parentElement as HTMLElement;
      const groupScope = within(groupNode);
      for (const row of group.rows) {
        expect(groupScope.getByText(row.label)).toBeInTheDocument();
      }
    }
  });

  it("clicking an open row's button again closes its detail panel", () => {
    render(<PerfRecordsList />);
    const record = PERF_RECORDS[0];
    const button = screen.getByText(record.action).closest("button") as HTMLElement;
    fireEvent.click(button);
    expect(screen.getByText(record.note)).toBeInTheDocument();
    fireEvent.click(button);
    expect(screen.queryByText(record.note)).toBeNull();
  });

  it("is a real accordion: opening a second row closes whichever record was open first", () => {
    render(<PerfRecordsList />);
    const first = PERF_RECORDS[0];
    const second = PERF_RECORDS[1];
    const firstButton = screen.getByText(first.action).closest("button") as HTMLElement;
    const secondButton = screen.getByText(second.action).closest("button") as HTMLElement;

    fireEvent.click(firstButton);
    expect(screen.getByText(first.note)).toBeInTheDocument();

    fireEvent.click(secondButton);
    expect(screen.queryByText(first.note)).toBeNull();
    expect(screen.getByText(second.note)).toBeInTheDocument();
  });

  it("applies the open-card border token's class only to the currently open record's card", () => {
    render(<PerfRecordsList />);
    const first = PERF_RECORDS[0];
    const button = screen.getByText(first.action).closest("button") as HTMLElement;
    const card = button.closest("div") as HTMLElement;
    expect(card.className).not.toContain("cardOpen");
    fireEvent.click(button);
    expect(card.className).toContain("cardOpen");
  });

  it("colors each detail row's value by its real kind, matching the reference file's exact mapping", () => {
    render(<PerfRecordsList />);
    const record = PERF_RECORDS[0];
    const button = screen.getByText(record.action).closest("button") as HTMLElement;
    fireEvent.click(button);

    const okRow = screen.getByText("Packet minimum").closest("div") as HTMLElement;
    expect(within(okRow).getByText("90,000 · satisfied").className).toContain("detailValueOk");

    const estRow = screen.getByText("Projected growth").closest("div") as HTMLElement;
    expect(within(estRow).getByText("12k–31k est.").className).toContain("detailValueEst");

    const naRow = screen.getByText("Cost").closest("div") as HTMLElement;
    expect(within(naRow).getByText("not_billed").className).toContain("detailValueNa");

    const plainRow = screen.getByText("Elapsed").closest("div") as HTMLElement;
    expect(within(plainRow).getByText("0.9s").className).toContain("detailValueDefault");
  });

  it("uses the real motion.rise token for the detail panel's reveal animation, not invented values", () => {
    expect(motion.rise.translateYPx).toBe(4);
    expect(motion.rise.durationS.min).toBe(0.18);
    expect(motion.rise.easing).toBe("ease-out");
  });
});
