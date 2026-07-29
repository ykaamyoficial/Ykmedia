import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DownloadsPage } from "@/features/downloads";
import { createAppQueryClient } from "@/shared/query";

function renderDownloads() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return render(
    <QueryClientProvider client={queryClient}>
      <DownloadsPage />
    </QueryClientProvider>,
  );
}

const jobsPayload = {
  items: [
    {
      id: "job-123456",
      short_id: "job-1234",
      sender: "+55 62 99999-9999",
      sender_raw: "5562999999999@s.whatsapp.net",
      origin: "WhatsApp",
      file: "foto.jpg",
      kind: "Imagem",
      status: "PENDENTE",
      created_at: "29/07/2026 10:00",
    },
    {
      id: "job-222222",
      short_id: "job-2222",
      sender: "+55 62 88888-8888",
      sender_raw: "5562888888888@s.whatsapp.net",
      origin: "YouTube",
      file: "louvor.mp4",
      kind: "Video",
      status: "CONCLUIDO",
      created_at: "29/07/2026 10:10",
    },
  ],
  total: 2,
};

describe("DownloadsPage", () => {
  it("renders queue jobs with the PySide6 columns", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(jobsPayload),
      }),
    );

    renderDownloads();

    await waitFor(() => expect(screen.getByText("foto.jpg")).toBeInTheDocument());
    expect(screen.getByText("Remetente")).toBeInTheDocument();
    expect(screen.getByText("Origem")).toBeInTheDocument();
    expect(screen.getByText("Arquivo")).toBeInTheDocument();
    expect(screen.getByText("Tipo")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Status" })).toBeInTheDocument();
    expect(screen.getByText("Recebido em")).toBeInTheDocument();
    expect(screen.getByText("ID")).toBeInTheDocument();
  });

  it("filters jobs by search and status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(jobsPayload),
      }),
    );

    renderDownloads();

    await waitFor(() => expect(screen.getByText("foto.jpg")).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText("Buscar por remetente, arquivo ou tipo..."), {
      target: { value: "louvor" },
    });
    expect(screen.queryByText("foto.jpg")).not.toBeInTheDocument();
    expect(screen.getByText("louvor.mp4")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Filtrar por status"), {
      target: { value: "PENDENTE" },
    });
    expect(screen.getByText("Fila vazia.")).toBeInTheDocument();
  });

  it("shows an empty state when there are no jobs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [], total: 0 }),
      }),
    );

    renderDownloads();

    await waitFor(() => expect(screen.getByText("Fila vazia.")).toBeInTheDocument());
    expect(
      screen.getByText("Quando uma midia ou link entrar para processamento, o job aparecera aqui."),
    ).toBeInTheDocument();
  });

  it("shows an error state and can request a retry", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(jobsPayload),
      });
    vi.stubGlobal("fetch", fetcher);

    renderDownloads();

    await waitFor(() => expect(screen.getByText("Erro ao carregar")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /tentar novamente/i }));
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  });

  it("calls the clear completed endpoint", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(jobsPayload),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ removed: 1 }),
      })
      .mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ items: [jobsPayload.items[0]], total: 1 }),
      });
    vi.stubGlobal("fetch", fetcher);

    renderDownloads();

    await waitFor(() => expect(screen.getByText("foto.jpg")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /limpar concluidos/i }));

    await waitFor(() =>
      expect(fetcher).toHaveBeenCalledWith(
        "http://127.0.0.1:8010/downloads/jobs/completed",
        expect.objectContaining({ method: "DELETE" }),
      ),
    );
  });
});
