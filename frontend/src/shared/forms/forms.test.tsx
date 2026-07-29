import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { YkForm } from "@/shared/forms/YkForm";
import { YkInput, YkSelect } from "@/shared/forms/form-controls";

describe("forms", () => {
  it("submits values through the official form wrapper", async () => {
    const onSubmit = vi.fn();

    render(
      <YkForm defaultValues={{ name: "" }} onSubmit={onSubmit}>
        <YkInput aria-label="Nome" {...{ name: "name" }} />
        <button type="submit">Salvar</button>
      </YkForm>,
    );

    await userEvent.type(screen.getByLabelText("Nome"), "YkMedia");
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));

    expect(onSubmit).toHaveBeenCalled();
  });

  it("renders official select controls", () => {
    render(
      <YkSelect aria-label="Categoria">
        <option>Louvores</option>
      </YkSelect>,
    );

    expect(screen.getByLabelText("Categoria")).toBeInTheDocument();
  });
});
