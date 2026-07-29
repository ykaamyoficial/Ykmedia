import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ToastProvider } from "@/shared/toast/ToastProvider";
import { toast } from "@/shared/toast/toast-service";

describe("ToastProvider", () => {
  it("renders and dismisses toast messages", async () => {
    render(
      <ToastProvider>
        <button type="button" onClick={() => toast.success("Salvo", "Operacao concluida")}>
          Mostrar
        </button>
      </ToastProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Mostrar" }));

    expect(screen.getByText("Salvo")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /salvo/i }));
    expect(screen.queryByText("Salvo")).not.toBeInTheDocument();
  });
});
