import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatTab } from "./ChatTab";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";

afterEach(cleanup);

describe("ChatTab", () => {
  it("renders the real eyebrow/title identity pair, the same single state source PacketHeader (C7) already reads from", () => {
    render(<ChatTab onBack={() => {}} />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText(state.eyebrow)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: state.title })).toBeInTheDocument();
    expect(screen.getByText(state.stateLine)).toBeInTheDocument();
  });

  it("renders all six real fixture messages, in order, with their exact body text", () => {
    render(<ChatTab onBack={() => {}} />);
    const bubbles = screen.getAllByText(/./, { selector: "[class*='bubble']" });
    expect(bubbles.map((b) => b.textContent)).toEqual(PACKET_A2_ENTRIES.map((e) => e.text));
  });

  it("shows every entry's own name/role/time row unconditionally, unlike C1's desktop grouping (the reference file's mobile view has no such grouping)", () => {
    render(<ChatTab onBack={() => {}} />);
    expect(screen.getAllByText("Coordinator")).toHaveLength(3);
    expect(screen.getAllByText("Terra")).toHaveLength(3);
    expect(screen.getAllByText("Implementor")).toHaveLength(3);
  });

  it("calls onBack when the '‹ Now' button is pressed", () => {
    const onBack = vi.fn();
    render(<ChatTab onBack={onBack} />);
    fireEvent.click(screen.getByRole("button", { name: "‹ Now" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders no message composer or send control (no real backend command exists for sending a chat message)", () => {
    render(<ChatTab onBack={() => {}} />);
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByRole("button", { name: /send/i })).toBeNull();
    expect(screen.queryByPlaceholderText(/message/i)).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ChatTab onBack={() => {}} />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
