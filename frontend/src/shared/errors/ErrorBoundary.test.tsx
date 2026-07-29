import { render, screen } from "@testing-library/react";
import { type ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import { ErrorBoundary } from "@/shared/errors";

describe("ErrorBoundary", () => {
  it("renders a friendly fallback when children fail", () => {
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);

    function BrokenComponent(): ReactElement {
      throw new Error("broken");
    }

    render(
      <ErrorBoundary>
        <BrokenComponent />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Algo saiu do esperado")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tentar novamente" })).toBeInTheDocument();

    errorSpy.mockRestore();
  });
});
