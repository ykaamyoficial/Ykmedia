import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { DashboardPage } from "@/features/dashboard";
import { AppProvider } from "@/providers/AppProvider";
import { BackendStatusProvider } from "@/providers/BackendStatusProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { DialogProvider } from "@/shared/dialogs/DialogProvider";
import { createAppQueryClient } from "@/shared/query";
import { ToastProvider } from "@/shared/toast/ToastProvider";

function renderDashboard() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BackendStatusProvider>
          <AppProvider>
            <DialogProvider>
              <ToastProvider>
                <DashboardPage />
              </ToastProvider>
            </DialogProvider>
          </AppProvider>
        </BackendStatusProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  it("renders operational data from one overview payload", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          generated_at: "2026-07-29T10:00:00+00:00",
          system: {
            version: "0.1.0",
            uptime_seconds: 60,
            backend_online: true,
            database_connected: true,
          },
          evolution: {
            online: true,
            instance: "ykmedia",
            last_sync: "2026-07-29T10:00:00+00:00",
            error: null,
          },
          whatsapp: {
            status: "connected",
            connected: true,
            qr_pending: false,
          },
          downloads: {
            in_progress: 0,
            completed: 2,
            failures: 0,
            queue: 1,
          },
          files: {
            stored_count: 3,
            storage_used_bytes: 1024,
            categories: ["Louvores", "Mensagens"],
          },
          conversations: {
            total: 1,
            active_contacts: 1,
            latest_messages: [],
          },
          history: [
            {
              id: "hist-1",
              date: "2026-07-29T10:00:00+00:00",
              sender: "556299999999@s.whatsapp.net",
              origin: "WhatsApp",
              category: "Louvores",
              final_name: "arquivo.mp3",
              file_path: "Louvores/arquivo.mp3",
              status: "CONCLUIDO",
            },
          ],
          health: [
            {
              key: "backend",
              label: "Backend",
              status: "online",
              description: "API FastAPI respondendo.",
            },
          ],
          has_data: true,
        }),
    });
    vi.stubGlobal("fetch", fetcher);

    renderDashboard();

    await waitFor(() => expect(screen.getByText("Sistema")).toBeInTheDocument());
    expect(screen.getByText("WhatsApp")).toBeInTheDocument();
    expect(screen.getByText("Worker")).toBeInTheDocument();
    expect(screen.getByText("Na fila")).toBeInTheDocument();
    expect(screen.getByText("Atividade nas ultimas 24 horas")).toBeInTheDocument();
    expect(screen.getByText("Resumo operacional")).toBeInTheDocument();
    expect(screen.getByText("Nenhuma atividade registrada ainda.")).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8010/dashboard/overview",
      expect.any(Object),
    );
  });
});
