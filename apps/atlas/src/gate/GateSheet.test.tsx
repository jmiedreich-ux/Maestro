import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { GateSheet } from "./GateSheet";
import { GATE_CRITERIA } from "./fixtures";

afterEach(cleanup);

describe("GateSheet", () => {
  it("renders as a real dialog, labelled by its own real title", () => {
    render(<GateSheet onClose={() => {}} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    const heading = screen.getByRole("heading", { name: "Overlay and support surfaces" });
    expect(dialog).toHaveAttribute("aria-labelledby", heading.id);
  });

  it("renders the real breadcrumb and a real, derived state line", () => {
    const yesCount = GATE_CRITERIA.filter((c) => c.met === "yes").length;
    const partCount = GATE_CRITERIA.filter((c) => c.met === "part").length;
    render(<GateSheet onClose={() => {}} />);
    expect(screen.getByText("m1-b · milestone gate")).toBeInTheDocument();
    expect(
      screen.getByText(`Closed · ${yesCount} of ${GATE_CRITERIA.length} criteria met, ${partCount} partly`),
    ).toBeInTheDocument();
  });

  it("renders every real GATE_CRITERIA row with its exact title, detail, and evidence", () => {
    render(<GateSheet onClose={() => {}} />);
    for (const criterion of GATE_CRITERIA) {
      expect(screen.getByText(criterion.title)).toBeInTheDocument();
      expect(screen.getByText(criterion.detail)).toBeInTheDocument();
      expect(screen.getByText(criterion.evidence)).toBeInTheDocument();
    }
  });

  it("colors each real row's mark/title/evidence by its exact real 'met' state", () => {
    render(<GateSheet onClose={() => {}} />);
    for (const criterion of GATE_CRITERIA) {
      const title = screen.getByText(criterion.title);
      expect(title.className).toContain(criterion.met === "no" ? "rowTitleUnmet" : "rowTitleDefault");

      const row = title.closest('[class*="criterionRow"]') as HTMLElement;
      const mark = row.querySelector('[class*="mark"]') as HTMLElement;
      expect(mark.className).toContain(
        criterion.met === "yes" ? "markYes" : criterion.met === "part" ? "markPart" : "markNo",
      );

      const evidence = screen.getByText(criterion.evidence);
      expect(evidence.className).toContain(
        criterion.met === "yes" ? "evidenceYes" : criterion.met === "part" ? "evidencePart" : "evidenceNo",
      );
    }
  });

  it("renders the real, derived 'blocked by N criteria' disabled Open-gate button", () => {
    const noCount = GATE_CRITERIA.filter((c) => c.met === "no").length;
    render(<GateSheet onClose={() => {}} />);
    const openButton = screen.getByRole("button", { name: `Open gate · blocked by ${noCount} criteria` });
    expect(openButton).toBeDisabled();
  });

  it("renders the corrected, real-mechanism note — no fictional autonomous-opening claim", () => {
    render(<GateSheet onClose={() => {}} />);
    expect(
      screen.getByText(
        "No automated gate-opening exists in Maestro today — opening the gate remains a manual, owner-reviewed action. This becomes an automatic Coordinator decision once M4's own autonomous Architect loop exists.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent opens the gate on its own/)).toBeNull();
  });

  it("moves focus to its own Close button on mount", () => {
    render(<GateSheet onClose={() => {}} />);
    expect(screen.getByRole("button", { name: "Close" })).toHaveFocus();
  });

  it("calls onClose when the Close button is clicked", () => {
    const onClose = vi.fn();
    render(<GateSheet onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the backdrop is clicked, but not when the sheet itself is clicked", () => {
    const onClose = vi.fn();
    const { container } = render(<GateSheet onClose={onClose} />);
    const dialog = screen.getByRole("dialog");
    fireEvent.click(dialog);
    expect(onClose).not.toHaveBeenCalled();

    const backdrop = container.firstElementChild as HTMLElement;
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose on Escape", () => {
    const onClose = vi.fn();
    render(<GateSheet onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not call onClose on a non-Escape key", () => {
    const onClose = vi.fn();
    render(<GateSheet onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Enter" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("removes its own document keydown listener on unmount", () => {
    const onClose = vi.fn();
    const { unmount } = render(<GateSheet onClose={onClose} />);
    unmount();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("renders no image, icon font, or <svg> element", () => {
    render(<GateSheet onClose={() => {}} />);
    expect(document.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
