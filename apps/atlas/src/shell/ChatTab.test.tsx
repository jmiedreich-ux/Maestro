import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatTab } from "./ChatTab";
import styles from "./ChatTab.module.css";
import type { RealEvent } from "../thread/realEventSynthesis";

const PACKET_ID = "packet-test-chat";

function realEvent(overrides: Partial<RealEvent>): RealEvent {
  return {
    event_id: 1,
    entity_type: "Packet",
    entity_id: PACKET_ID,
    event_type: "state_transition",
    before_json: { state: "Ready" },
    after_json: { state: "Leased" },
    reason: { kind: "reason", reason_code: "WORK_STARTED", detail_reference: null },
    actor_type: "MaestroDeveloper",
    actor_id: "developer-1",
    created_at: "2026-09-06T13:49:00.000000Z",
    ...overrides,
  };
}

const TWO_EVENTS: RealEvent[] = [
  realEvent({ event_id: 1, actor_type: "IntegrationAgent", created_at: "2026-09-06T13:49:00.000000Z" }),
  realEvent({ event_id: 2, actor_type: "MaestroDeveloper", created_at: "2026-09-06T13:51:00.000000Z" }),
];

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: TWO_EVENTS.slice().reverse() }) }),
  );
  vi.stubGlobal(
    "EventSource",
    class {
      onmessage: unknown = null;
      addEventListener() {}
      close() {}
    },
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ChatTab", () => {
  it("renders the real packet id as eyebrow, and a real, humanized current state as title/status once events load", async () => {
    render(<ChatTab onBack={() => {}} packetId={PACKET_ID} />);
    expect(screen.getByText("test-chat")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Assigned" })).toBeInTheDocument();
    });
    expect(screen.getAllByText("work started").length).toBeGreaterThan(0);
    expect(screen.getByText("2 real events recorded")).toBeInTheDocument();
  });

  it("renders the real backend events as honest mechanical descriptions, newest first", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          events: [
            realEvent({ event_id: 2, before_json: { state: "Leased" }, after_json: { state: "Running" } }),
            realEvent({ event_id: 1, before_json: { state: "Ready" }, after_json: { state: "Leased" } }),
          ],
        }),
      }),
    );
    const { container } = render(<ChatTab onBack={() => {}} packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(container.getElementsByClassName(styles.row).length).toBeGreaterThan(0);
    });
    const rows = Array.from(container.getElementsByClassName(styles.row));
    // The snapshot itself is newest-first (event_id 2 listed before 1);
    // useRealPacketThread reverses it to oldest-first for its own
    // shared entries shape, and ChatTab reverses it back — the most
    // recent real event (event_id 2) is visible first, no scrolling.
    expect(rows.map((r) => r.textContent)).toEqual([
      expect.stringContaining("Assigned → In progresswork started"),
      expect.stringContaining("Ready to start → Assignedwork started"),
    ]);
  });

  it("renders every real event as its own timeline row, including pre-work transitions (queued/waiting/ready/dispatchable) — no collapsing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          events: [
            realEvent({ event_id: 4, before_json: { state: "Ready" }, after_json: { state: "Leased" } }),
            realEvent({ event_id: 3, before_json: { state: "Waiting" }, after_json: { state: "Dispatchable" } }),
            realEvent({ event_id: 2, before_json: { state: "Waiting" }, after_json: { state: "Ready" } }),
            realEvent({ event_id: 1, before_json: {}, after_json: { state: "Planned" } }),
          ],
        }),
      }),
    );
    const { container } = render(<ChatTab onBack={() => {}} packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(container.getElementsByClassName(styles.entryTitle).length).toBe(4);
    });
    const titles = Array.from(container.getElementsByClassName(styles.entryTitle)).map((el) => el.textContent);
    const details = Array.from(container.getElementsByClassName(styles.entryDetail)).map((el) => el.textContent);
    expect(titles).toEqual(["Ready to start → Assigned", "Waiting → Ready to start", "Waiting → Ready to start", "State transition"]);
    expect(details).toEqual(["work started", "work started", "work started", "work started"]);
  });

  it("shows every entry's own name/role/time row unconditionally, unlike C1's desktop grouping (the reference file's mobile view has no such grouping)", async () => {
    render(<ChatTab onBack={() => {}} packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(screen.getAllByText("Maestro Developer").length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText("Integration Agent")).toHaveLength(1);
    expect(screen.getAllByText("Maestro Developer")).toHaveLength(1);
  });

  it("calls onBack when the '‹ Now' button is pressed", () => {
    const onBack = vi.fn();
    render(<ChatTab onBack={onBack} packetId={PACKET_ID} />);
    fireEvent.click(screen.getByRole("button", { name: "‹ Now" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders no message composer or send control (no real backend command exists for sending a chat message)", () => {
    render(<ChatTab onBack={() => {}} packetId={PACKET_ID} />);
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByRole("button", { name: /send/i })).toBeNull();
    expect(screen.queryByPlaceholderText(/message/i)).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ChatTab onBack={() => {}} packetId={PACKET_ID} />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
