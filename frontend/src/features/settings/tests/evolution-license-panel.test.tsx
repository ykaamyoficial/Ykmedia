import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EvolutionLicensePanel } from "@/features/settings/components";

const noop = () => {};

const handlers = {
  onRefresh: noop,
  onStartActivation: noop,
  onCancelActivation: noop,
  onOpenRegisterUrl: noop,
};

describe("EvolutionLicensePanel", () => {
  it("offers activation when the license is pending", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "PENDENTE", message: "Licenca ainda nao ativada." }}
        activationPhase="idle"
        {...handlers}
      />,
    );

    expect(screen.getByText("Pendente")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ativar licença/i })).toBeInTheDocument();
  });

  it("hides activation when the license is already active", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "ATIVA", message: "Licenca ativa." }}
        activationPhase="idle"
        {...handlers}
      />,
    );

    expect(screen.getByText("Ativa")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ativar licença/i })).not.toBeInTheDocument();
  });

  it("hides activation on versions that do not require a license", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "NAO_EXIGIDA", message: "Versao antiga." }}
        activationPhase="idle"
        {...handlers}
      />,
    );

    expect(screen.getByText("Não exigida")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ativar licença/i })).not.toBeInTheDocument();
  });

  it("guides the user while waiting for the registration", () => {
    const onOpenRegisterUrl = vi.fn();
    render(
      <EvolutionLicensePanel
        license={{ status: "PENDENTE", message: "Licenca ainda nao ativada." }}
        activationPhase="waiting"
        registerUrl="https://license.test/register?token=abc"
        {...handlers}
        onOpenRegisterUrl={onOpenRegisterUrl}
      />,
    );

    // Quem instala numa igreja precisa saber que basta voltar para a tela.
    expect(screen.getByText(/detectada sozinha/i)).toBeInTheDocument();
    expect(screen.getByText(/Aguardando a conclusão/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /abrir cadastro/i }));
    expect(onOpenRegisterUrl).toHaveBeenCalledWith("https://license.test/register?token=abc");
  });

  it("confirms the activation without a manual refresh", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "PENDENTE", message: "Licenca ainda nao ativada." }}
        activationPhase="activated"
        {...handlers}
      />,
    );

    expect(screen.getByText("Ativa")).toBeInTheDocument();
    expect(screen.getByText(/Licença ativada/i)).toBeInTheDocument();
  });

  it("shows an activation error", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "PENDENTE", message: "Licenca ainda nao ativada." }}
        activationPhase="error"
        activationError="O cadastro expirou."
        {...handlers}
      />,
    );

    expect(screen.getByText("O cadastro expirou.")).toBeInTheDocument();
  });
});
