import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ThemeProvider } from "@/providers/ThemeProvider";
import { useTheme } from "@/providers/useTheme";

function ThemeProbe() {
  const { mode, setMode } = useTheme();
  return (
    <button type="button" onClick={() => setMode("dark")}>
      Tema {mode}
    </button>
  );
}

describe("ThemeProvider", () => {
  it("provides the current theme and updates the document theme", async () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: /tema system/i }));

    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(screen.getByRole("button", { name: /tema dark/i })).toBeInTheDocument();
  });
});
