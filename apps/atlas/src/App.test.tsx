import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the desktop shell", () => {
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Atlas views" })).toBeInTheDocument();
  });
});
