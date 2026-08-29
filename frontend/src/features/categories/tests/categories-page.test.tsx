import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CategoriesPage } from "@/features/categories";
import { createAppQueryClient } from "@/shared/query";

function renderCategories() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return render(
    <QueryClientProvider client={queryClient}>
      <CategoriesPage />
    </QueryClientProvider>,
  );
}

const categoriesPayload = {
  items: [
    { position: 1, name: "Louvores", folder: "C:\\media\\Louvores" },
    { position: 2, name: "Mensagens", folder: "C:\\media\\Mensagens" },
  ],
  total: 2,
};

describe("CategoriesPage", () => {
  it("renders category rows with the PySide6 columns", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(categoriesPayload),
      }),
    );

    renderCategories();

    await waitFor(() => expect(screen.getByText("Louvores")).toBeInTheDocument());
    expect(screen.getByRole("columnheader", { name: "Posicao" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Categoria" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Pasta correspondente" })).toBeInTheDocument();
  });

  it("adds a category using the name dialog", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(categoriesPayload) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(categoriesPayload) })
      .mockResolvedValue({ ok: true, json: () => Promise.resolve(categoriesPayload) });
    vi.stubGlobal("fetch", fetcher);

    renderCategories();

    await waitFor(() => expect(screen.getByText("Louvores")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /nova categoria/i }));
    fireEvent.change(screen.getByLabelText(/nome da categoria/i), { target: { value: "Jovens" } });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() =>
      expect(fetcher).toHaveBeenCalledWith(
        "http://127.0.0.1:8010/categories",
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify({ categories: ["Louvores", "Mensagens", "Jovens"] }),
        }),
      ),
    );
  });

  it("edits the selected category", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(categoriesPayload) })
      .mockResolvedValue({ ok: true, json: () => Promise.resolve(categoriesPayload) });
    vi.stubGlobal("fetch", fetcher);

    renderCategories();

    await waitFor(() => expect(screen.getByText("Mensagens")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Mensagens"));
    fireEvent.click(screen.getByRole("button", { name: /editar/i }));
    fireEvent.change(screen.getByLabelText(/nome da categoria/i), { target: { value: "Jovens" } });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/categories",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ categories: ["Louvores", "Jovens"] }),
      }),
    ));
  });

  it("deletes the selected category after confirmation", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(categoriesPayload) })
      .mockResolvedValue({ ok: true, json: () => Promise.resolve(categoriesPayload) });
    vi.stubGlobal("fetch", fetcher);

    renderCategories();

    await waitFor(() => expect(screen.getByText("Mensagens")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Mensagens"));
    fireEvent.click(screen.getByRole("button", { name: /excluir/i }));
    fireEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/categories",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ categories: ["Louvores"] }),
      }),
    ));
  });

  it("moves the selected category up", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(categoriesPayload) })
      .mockResolvedValue({ ok: true, json: () => Promise.resolve(categoriesPayload) });
    vi.stubGlobal("fetch", fetcher);

    renderCategories();

    await waitFor(() => expect(screen.getByText("Mensagens")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Mensagens"));
    fireEvent.click(screen.getByRole("button", { name: /mover acima/i }));

    await waitFor(() => expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/categories",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ categories: ["Mensagens", "Louvores"] }),
      }),
    ));
  });

  it("shows an empty state when there are no categories", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [], total: 0 }),
      }),
    );

    renderCategories();

    await waitFor(() => expect(screen.getByText("Nenhuma categoria cadastrada.")).toBeInTheDocument());
  });

  it("shows an error state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    renderCategories();

    await waitFor(() => expect(screen.getByText("Sem conexao")).toBeInTheDocument());
  });
});
