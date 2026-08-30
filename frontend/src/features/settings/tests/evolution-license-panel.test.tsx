import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EvolutionLicensePanel } from "@/features/settings/components";

const noop = () => {};

describe("EvolutionLicensePanel", () => {
  it("offers activation when the license is pending", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "PENDENTE", message: "Licenca ainda nao ativada." }}
        onRefresh={noop}
        onStartRegistration={noop}
        onOpenRegisterUrl={noop}
      />,
    );

    expect(screen.getByText("Pendente")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ativar licença/i })).toBeInTheDocument();
  });

  it("hides activation when the license is already active", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "ATIVA", message: "Licenca ativa." }}
        onRefresh={noop}
        onStartRegistration={noop}
        onOpenRegisterUrl={noop}
      />,
    );

    expect(screen.getByText("Ativa")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ativar licença/i })).not.toBeInTheDocument();
  });

  it("hides activation on versions that do not require a license", () => {
    render(
      <EvolutionLicensePanel
        license={{ status: "NAO_EXIGIDA", message: "Versao antiga." }}
        onRefresh={noop}
        onStartRegistration={noop}
        onOpenRegisterUrl={noop}
      />,
    );

    expect(screen.getByText("Não exigida")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ativar licença/i })).not.toBeInTheDocument();
  });

  it("opens the registration url when one is available", () => {
    const onOpenRegisterUrl = vi.fn();
    render(
      <EvolutionLicensePanel
        license={{ status: "PENDENTE", message: "Licenca ainda nao ativada." }}
        registerUrl="https://license.test/register?token=abc"
        onRefresh={noop}
        onStartRegistration={noop}
        onOpenRegisterUrl={onOpenRegisterUrl}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /abrir cadastro/i }));

    expect(onOpenRegisterUrl).toHaveBeenCalledWith("https://license.test/register?token=abc");
  });
});
