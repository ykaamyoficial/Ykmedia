import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { DialogProvider } from "@/shared/dialogs/DialogProvider";
import { dialog } from "@/shared/dialogs/dialog-service";

describe("DialogProvider", () => {
  it("renders and closes dialogs", async () => {
    render(
      <DialogProvider>
        <button type="button" onClick={() => dialog.info("Atencao", "Mensagem")}>
          Abrir
        </button>
      </DialogProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Abrir" }));

    expect(screen.getByRole("dialog", { name: "Atencao" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(screen.queryByRole("dialog", { name: "Atencao" })).not.toBeInTheDocument();
  });
});
