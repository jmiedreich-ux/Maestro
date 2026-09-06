import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";

afterEach(cleanup);

function setWindowWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { writable: true, configurable: true, value: width });
  fireEvent(window, new Event("resize"));
}

describe("App", () => {
  it("renders the desktop shell at desktop widths", () => {
    setWindowWidth(1440);
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Atlas views" })).toBeInTheDocument();
  });

  it("renders the mobile shell at mobile widths, below the real 880px breakpoint", () => {
    setWindowWidth(390);
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Atlas tabs" })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Atlas views" })).toBeNull();
  });

  it("switches shells on resize across the real 880px breakpoint", () => {
    setWindowWidth(1440);
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Atlas views" })).toBeInTheDocument();

    setWindowWidth(390);
    expect(screen.getByRole("navigation", { name: "Atlas tabs" })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Atlas views" })).toBeNull();

    setWindowWidth(1440);
    expect(screen.getByRole("navigation", { name: "Atlas views" })).toBeInTheDocument();
  });
});
