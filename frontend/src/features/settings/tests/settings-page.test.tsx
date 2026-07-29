import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SettingsPage } from "@/features/settings";
import { createAppQueryClient } from "@/shared/query";

const settingsPayload = {
  downloads_root: "C:/YkMedia/Midias",
  ffmpeg_path: "C:/ffmpeg/bin/ffmpeg.exe",
  sqlite_database: "data/ykmedia.sqlite3",
  whatsapp_instance: "ykmedia",
  evolution_state: "open",
  evolution_message: "Estado atualizado.",
};

function renderSettings() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false, gcTime: 0 } });
  return render(
    <QueryClientProvider client={queryClient}>
      <SettingsPage />
    </QueryClientProvider>,
  );
}

function mockFetch() {
  return vi.fn((url: string, init?: RequestInit) => {
    if (url.endsWith("/settings") && init?.method === "PUT") {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(settingsPayload) });
    }
    if (url.endsWith("/settings/evolution/connect")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ instance_name: "ykmedia", state: "connecting", message: "QR Code solicitado.", qrcode_base64: "base64" }),
      });
    }
    if (url.endsWith("/settings/evolution/disconnect")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ instance_name: "ykmedia", state: "close", message: "Sessao desconectada." }),
      });
    }
    if (url.endsWith("/settings/diagnostics")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          status: "OK",
          message: "Todos os componentes estao prontos.",
          items: [{ key: "backend", name: "Backend YkMedia", status: "OK", message: "Backend online." }],
        }),
      });
    }
    if (url.endsWith("/settings/prepare")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: "OK", message: "Sistema pronto.", steps: [] }) });
    }
    if (url.endsWith("/settings/evolution")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ instance_name: "ykmedia", state: "open", message: "Estado atualizado." }),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve(settingsPayload) });
  });
}

describe("SettingsPage", () => {
  it("renders the PySide6 settings sections", async () => {
    vi.stubGlobal("fetch", mockFetch());

    renderSettings();

    expect(await screen.findByRole("button", { name: "Pastas" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "WhatsApp" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Avancado" })).toBeInTheDocument();
  });

  it("edits and saves folder settings", async () => {
    const fetcher = mockFetch();
    vi.stubGlobal("fetch", fetcher);

    renderSettings();

    fireEvent.click(await screen.findByRole("button", { name: "Pastas" }));
    fireEvent.change(screen.getByLabelText("Pasta das midias"), { target: { value: "D:/Midias" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      const saveCall = fetcher.mock.calls.find(
        ([url, init]) => url === "http://127.0.0.1:8010/settings" && init?.method === "PUT",
      );
      expect(saveCall).toBeDefined();
      const body = saveCall?.[1]?.body;
      expect(typeof body).toBe("string");
      expect(body).toContain("D:/Midias");
    });
  });

  it("shows WhatsApp QR Code after connect", async () => {
    vi.stubGlobal("fetch", mockFetch());

    renderSettings();

    fireEvent.click(await screen.findByRole("button", { name: "WhatsApp" }));
    fireEvent.click(screen.getByRole("button", { name: /Conectar WhatsApp/i }));

    await waitFor(() => expect(screen.getByAltText("QR Code do WhatsApp")).toBeInTheDocument());
  });

  it("runs diagnostics and renders the result table", async () => {
    vi.stubGlobal("fetch", mockFetch());

    renderSettings();

    fireEvent.click(await screen.findByRole("button", { name: /Executar Diagnostico/i }));

    await waitFor(() => expect(screen.getByText("Backend YkMedia")).toBeInTheDocument());
  });
});
