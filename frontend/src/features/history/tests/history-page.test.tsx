import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HistoryPage } from "@/features/history";
import { createAppQueryClient } from "@/shared/query";

function renderHistory() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return render(
    <QueryClientProvider client={queryClient}>
      <HistoryPage />
    </QueryClientProvider>,
  );
}

const historyPayload = {
  items: [
    {
      id: "hist-1",
      date: "2026-07-29T10:00:00+00:00",
      date_display: "29/07/2026 10:00",
      sender: "+55 62 99999-9999",
      sender_raw: "5562999999999@s.whatsapp.net",
      origin: "WhatsApp",
      category: "Louvores",
      final_name: "imagem.jpg",
      file_path: "Louvores/imagem.jpg",
      kind: "Imagem",
      status: "CONCLUIDO",
    },
    {
      id: "hist-2",
      date: "2026-07-29T11:00:00+00:00",
      date_display: "29/07/2026 11:00",
      sender: "+55 62 88888-8888",
      sender_raw: "5562888888888@s.whatsapp.net",
      origin: "YouTube",
      category: "Mensagens",
      final_name: "pregacao.mp4",
      file_path: "Mensagens/pregacao.mp4",
      kind: "YouTube",
      status: "CONCLUIDO",
    },
  ],
  total: 2,
};

describe("HistoryPage", () => {
  it("renders history rows with the PySide6 columns", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(historyPayload),
      }),
    );

    renderHistory();

    await waitFor(() => expect(screen.getByText("imagem.jpg")).toBeInTheDocument());
    expect(screen.getByRole("columnheader", { name: "Data" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Remetente" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Origem" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Categoria" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Nome final" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Tipo" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Status" })).toBeInTheDocument();
  });

  it("filters rows by search and category", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(historyPayload),
      }),
    );

    renderHistory();

    await waitFor(() => expect(screen.getByText("imagem.jpg")).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText("Buscar por nome, remetente ou categoria..."), {
      target: { value: "pregacao" },
    });
    expect(screen.queryByText("imagem.jpg")).not.toBeInTheDocument();
    expect(screen.getByText("pregacao.mp4")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Filtrar por categoria"), {
      target: { value: "Louvores" },
    });
    expect(screen.getByText("Nenhuma midia processada ainda.")).toBeInTheDocument();
  });

  it("shows an empty state when there are no history rows", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [], total: 0 }),
      }),
    );

    renderHistory();

    await waitFor(() => expect(screen.getByText("Nenhuma midia processada ainda.")).toBeInTheDocument());
  });

  it("shows an error state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    renderHistory();

    await waitFor(() => expect(screen.getByText("Sem conexao")).toBeInTheDocument());
  });
});
