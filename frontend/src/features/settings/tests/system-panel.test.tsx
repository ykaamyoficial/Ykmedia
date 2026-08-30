import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SystemSettingsPanel } from "@/features/settings/components";
import { appTimeouts } from "@/shared/constants/app";

const noop = () => {};

describe("SystemSettingsPanel", () => {
  it("explains the wait instead of looking stuck", () => {
    render(<SystemSettingsPanel preparing onPrepare={noop} onDiagnostics={noop} />);

    expect(screen.getByText(/Preparando o sistema/i)).toBeInTheDocument();
    expect(screen.getByText(/pode levar vários minutos/i)).toBeInTheDocument();
    expect(screen.getByText(/continua de onde parou/i)).toBeInTheDocument();
  });

  it("shows which step failed and why", () => {
    // Antes o painel exibia so a mensagem final: o usuario via "Nao foi
    // possivel preparar o sistema" sem saber qual etapa quebrou.
    render(
      <SystemSettingsPanel
        setup={{
          status: "ERROR",
          message: "Alguns itens ainda precisam de atencao.",
          steps: [
            { key: "config", label: "Configuracao", status: "OK", message: "Pronto." },
            {
              key: "environment",
              label: "Ambiente",
              status: "ERROR",
              message: "O download dos componentes demorou demais e foi interrompido.",
            },
          ],
        }}
        onPrepare={noop}
        onDiagnostics={noop}
      />,
    );

    expect(screen.getByText("Ambiente")).toBeInTheDocument();
    expect(screen.getByText(/download dos componentes demorou demais/i)).toBeInTheDocument();
  });

  it("allows minutes for the preparation, not the default 5 seconds", () => {
    // O limite padrao abortava a requisicao enquanto o backend ainda baixava
    // as imagens, e a tela acusava falha sem que nada tivesse falhado.
    expect(appTimeouts.systemPrepareMs).toBeGreaterThan(10 * 60 * 1000);
  });
});

describe("SystemSettingsPanel — relatar o problema", () => {
  it("lets the user copy the real error to send to support", async () => {
    // Sem isto o usuario so consegue fotografar a tela, e a mensagem longa
    // aparece cortada.
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(
      <SystemSettingsPanel
        setup={{
          status: "ERROR",
          message: "Alguns itens ainda precisam de atencao.",
          steps: [
            { key: "config", label: "Configuracao", status: "OK", message: "Pronto." },
            {
              key: "environment",
              label: "Ambiente",
              status: "ERROR",
              message: "ykmedia_evolution Exited (1)",
            },
          ],
        }}
        onPrepare={noop}
        onDiagnostics={noop}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /copiar detalhes/i }));

    expect(writeText).toHaveBeenCalledTimes(1);
    const copied = writeText.mock.calls[0][0] as string;
    expect(copied).toContain("Ambiente");
    expect(copied).toContain("ykmedia_evolution Exited (1)");
  });

  it("hides the copy button when everything worked", () => {
    render(
      <SystemSettingsPanel
        setup={{
          status: "OK",
          message: "Sistema pronto.",
          steps: [{ key: "config", label: "Configuracao", status: "OK", message: "Pronto." }],
        }}
        onPrepare={noop}
        onDiagnostics={noop}
      />,
    );

    expect(screen.queryByRole("button", { name: /copiar detalhes/i })).not.toBeInTheDocument();
  });
});
