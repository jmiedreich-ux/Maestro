import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { colors } from "../tokens";
import { OwnerDecisionCard } from "./OwnerDecisionCard";
import { OWNER_DECISION_EXAMPLE } from "./ownerFixtures";

afterEach(cleanup);

const REAL_CONTEXT = {
  packetId: "packet-foundry-cg-m4-19",
  expectedVersion: 4,
  reviewId: "review-request-changes",
  actor: { actor_type: "Owner", actor_id: "owner-1", correlation_id: "correlation-1" },
};

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

  describe("(M3 E5) real prop — wired to the real D2/D3 commands", () => {
    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("renders both options disabled, with no click handler, when real is omitted", () => {
      render(<OwnerDecisionCard />);
      const button = screen.getByRole("button", { name: /Allow a sentinel version/ });
      expect(button).toBeDisabled();
    });

    it("posts the real resolve-decision command when the sentinel option is clicked", async () => {
      const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ packet: { state: "Ready" } }) });
      vi.stubGlobal("fetch", fetchMock);

      render(<OwnerDecisionCard real={REAL_CONTEXT} />);
      fireEvent.click(screen.getByRole("button", { name: /Allow a sentinel version/ }));

      await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
      const [url, options] = fetchMock.mock.calls[0];
      expect(url).toBe("http://localhost:8765/command/resolve-decision");
      const body = JSON.parse(options.body as string);
      expect(body.target_state).toBe("Ready");
      expect(body.packet_id).toBe(REAL_CONTEXT.packetId);
    });

    it("posts the real dispatch-correction command when the amend option is clicked", async () => {
      const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ packet: { state: "Leased" } }) });
      vi.stubGlobal("fetch", fetchMock);

      render(<OwnerDecisionCard real={REAL_CONTEXT} />);
      fireEvent.click(screen.getByRole("button", { name: /Amend the A.1 contract/ }));

      await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
      const [url, options] = fetchMock.mock.calls[0];
      expect(url).toBe("http://localhost:8765/command/dispatch-correction");
      const body = JSON.parse(options.body as string);
      expect(body.review_id).toBe(REAL_CONTEXT.reviewId);
    });

    it("shows the real server error and clears the pending state when a real command fails", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ error: "stale_state" }) })
      );

      render(<OwnerDecisionCard real={REAL_CONTEXT} />);
      fireEvent.click(screen.getByRole("button", { name: /Allow a sentinel version/ }));

      await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("stale_state"));
      expect(screen.getByRole("button", { name: /Allow a sentinel version/ })).not.toBeDisabled();
    });

    it("disables both options while a real command is pending", async () => {
      let resolveFetch: (value: unknown) => void = () => {};
      vi.stubGlobal(
        "fetch",
        vi.fn().mockReturnValue(new Promise((resolve) => { resolveFetch = resolve; }))
      );

      render(<OwnerDecisionCard real={REAL_CONTEXT} />);
      fireEvent.click(screen.getByRole("button", { name: /Allow a sentinel version/ }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Amend the A.1 contract/ })).toBeDisabled();
      });

      resolveFetch({ ok: true, json: async () => ({ packet: { state: "Ready" } }) });
    });
  });
});
