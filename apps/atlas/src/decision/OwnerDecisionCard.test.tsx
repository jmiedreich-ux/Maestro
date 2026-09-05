import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { OwnerDecisionCard } from "./OwnerDecisionCard";
import { OWNER_DECISION_EXAMPLE } from "./ownerFixtures";

afterEach(cleanup);

describe("OwnerDecisionCard", () => {
  it("renders the real chain-chip actors (Terra, Coordinator, you), never the reference file's fictional Architect agent target", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText("Terra")).toBeInTheDocument();
    expect(screen.getByText("Coordinator")).toBeInTheDocument();
    expect(screen.getByText("you")).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent/)).toBeNull();
  });

  it("labels the eyebrow badge and age with the real, transcribed reference values", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText("your decision")).toBeInTheDocument();
    expect(screen.getByText(OWNER_DECISION_EXAMPLE.age)).toBeInTheDocument();
  });

  it("renders the verbatim headline question", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText(OWNER_DECISION_EXAMPLE.headline)).toBeInTheDocument();
  });

  it("attributes the escalation to the Coordinator, never to a fictional Architect agent persona", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getByText(OWNER_DECISION_EXAMPLE.why)).toBeInTheDocument();
    expect(screen.queryByText(/[Aa]rchitect agent/)).toBeNull();
  });

  it("renders exactly the 2 real options this slice keeps, and never the excluded third 'defer to the Architect agent' option", () => {
    render(<OwnerDecisionCard />);
    expect(screen.getAllByRole("button")).toHaveLength(2);
    for (const option of OWNER_DECISION_EXAMPLE.options) {
      expect(screen.getByText(option.title)).toBeInTheDocument();
      expect(screen.getByText(option.cost)).toBeInTheDocument();
      expect(screen.getByText(option.body)).toBeInTheDocument();
    }
    expect(screen.queryByText(/Send back to the Architect agent/)).toBeNull();
  });

  it("renders no footer or footer action button — that anatomy is Wave D's, not this slice's", () => {
    render(<OwnerDecisionCard />);
    expect(screen.queryByText(/Let the Architect rule/)).toBeNull();
    expect(screen.queryByText(/One of the few that needs a human/)).toBeNull();
  });

  it("sets the card border and background CSS variables to the real colors.warning* tokens", () => {
    expect(colors.warningBorder).toBe("#F1DEBE");
    expect(colors.warningWash).toBe("#FEF9F0");
    const { container } = render(<OwnerDecisionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-owner-border")).toBe(colors.warningBorder);
    expect(root.style.getPropertyValue("--atlas-owner-bg")).toBe(colors.warningWash);
    expect(root.style.getPropertyValue("--atlas-owner-dot")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-owner-chip-on")).toBe(colors.warning);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<OwnerDecisionCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
