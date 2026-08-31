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

describe("SystemSettingsPanel — mensagem em camadas", () => {
  const portFailure = {
    status: "ERROR",
    message: "Alguns itens ainda precisam de atencao.",
    steps: [
      {
        key: "environment",
        label: "Ambiente",
        status: "ERROR",
        message: "A porta 8080 esta bloqueada pelo Windows.",
        action: "Vou escolher outra porta automaticamente.",
        detail: "Container ykmedia_redis Running\nError response from daemon: ports are not available",
      },
    ],
  };

  it("shows the headline and the action, and hides the technical log", () => {
    // Ate a 0.4.1 o log cru do Docker aparecia com o mesmo peso do texto
    // humano, empurrando a frase util para o meio do bloco.
    render(<SystemSettingsPanel setup={portFailure} onPrepare={noop} onDiagnostics={noop} />);

    expect(screen.getByText(/A porta 8080 esta bloqueada pelo Windows/)).toBeInTheDocument();
    expect(screen.getByText(/Vou escolher outra porta automaticamente/)).toBeInTheDocument();
    expect(screen.queryByText(/Error response from daemon/)).not.toBeInTheDocument();
  });

  it("reveals the technical log on demand", async () => {
    render(<SystemSettingsPanel setup={portFailure} onPrepare={noop} onDiagnostics={noop} />);

    await userEvent.click(screen.getByRole("button", { name: /detalhes técnicos/i }));

    expect(screen.getByText(/Error response from daemon/)).toBeInTheDocument();
  });

  it("translates the status badges", () => {
    // O aplicativo e em portugues; a tela mostrava OK / ERROR / PENDING.
    render(
      <SystemSettingsPanel
        setup={{
          status: "ERROR",
          message: "x",
          steps: [
            { key: "a", label: "Um", status: "OK", message: "m" },
            { key: "b", label: "Dois", status: "ERROR", message: "m" },
            { key: "c", label: "Tres", status: "PENDING", message: "m" },
            { key: "d", label: "Quatro", status: "WARNING", message: "m" },
          ],
        }}
        onPrepare={noop}
        onDiagnostics={noop}
      />,
    );

    expect(screen.getByText("Pronto")).toBeInTheDocument();
    expect(screen.getByText("Falhou")).toBeInTheDocument();
    expect(screen.getByText("Aguardando")).toBeInTheDocument();
    expect(screen.getByText("Atenção")).toBeInTheDocument();
    expect(screen.queryByText("ERROR")).not.toBeInTheDocument();
  });
});

describe("SystemSettingsPanel — um problema por vez", () => {
  const cascade = {
    status: "ERROR",
    message: "Alguns itens ainda precisam de atencao.",
    steps: [
      { key: "config", label: "Configuracoes seguras", status: "OK", message: "Pronto." },
      {
        key: "environment",
        label: "Ambiente",
        status: "ERROR",
        message: "2 de 3 servicos subiram. Nao ficou de pe: ykmedia_evolution.",
        action: "Veja o log do servico que falhou.",
        detail: "ykmedia_evolution: exited",
      },
      {
        key: "license",
        label: "Licenca da Evolution",
        status: "PENDING",
        message: "Aguardando a etapa Ambiente ser resolvida primeiro.",
      },
    ],
  };

  it("promotes the blocking step above the rest", () => {
    // A tela tratava os sete itens com o mesmo peso: o usuario precisava
    // descobrir sozinho qual deles exigia acao.
    render(<SystemSettingsPanel setup={cascade} onPrepare={noop} onDiagnostics={noop} />);

    const highlight = screen.getByTestId("blocking-step");
    expect(highlight).toHaveTextContent("Ambiente");
    expect(highlight).toHaveTextContent("Nao ficou de pe: ykmedia_evolution");
    expect(highlight).toHaveTextContent("Veja o log do servico que falhou");
  });

  it("does not promote anything when every step worked", () => {
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

    expect(screen.queryByTestId("blocking-step")).not.toBeInTheDocument();
  });

  it("keeps the waiting steps visible but quiet", () => {
    render(<SystemSettingsPanel setup={cascade} onPrepare={noop} onDiagnostics={noop} />);

    // Aguardando nao e problema do usuario: e ordem de execucao.
    expect(screen.getByText("Aguardando")).toBeInTheDocument();
  });
});
