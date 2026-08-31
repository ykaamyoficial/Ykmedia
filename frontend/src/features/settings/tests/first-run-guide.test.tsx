import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FirstRunGuide } from "@/features/settings/components";

const noop = () => {};

describe("FirstRunGuide", () => {
  it("points at preparation when nothing is ready yet", () => {
    // Numa maquina nova existe uma ordem obrigatoria; a tela de Configuracoes
    // nao a mostrava, e o usuario tinha de adivinhar por onde comecar.
    render(
      <FirstRunGuide
        environmentReady={false}
        licenseActive={false}
        whatsappConnected={false}
        onPrepare={noop}
      />,
    );

    expect(screen.getByTestId("current-stage")).toHaveTextContent("Preparar o sistema");
  });

  it("moves to the license once the environment is up", () => {
    render(
      <FirstRunGuide
        environmentReady
        licenseActive={false}
        whatsappConnected={false}
        onPrepare={noop}
      />,
    );

    expect(screen.getByTestId("current-stage")).toHaveTextContent("Ativar a licenca");
  });

  it("moves to WhatsApp once the license is active", () => {
    render(
      <FirstRunGuide environmentReady licenseActive whatsappConnected={false} onPrepare={noop} />,
    );

    expect(screen.getByTestId("current-stage")).toHaveTextContent("Conectar o WhatsApp");
  });

  it("disappears when everything is done", () => {
    const { container } = render(
      <FirstRunGuide environmentReady licenseActive whatsappConnected onPrepare={noop} />,
    );

    // Cumprido o seu papel, o guia sai da frente em vez de virar ruido fixo.
    expect(container).toBeEmptyDOMElement();
  });

  it("marks the finished stages so progress is visible", () => {
    render(
      <FirstRunGuide
        environmentReady
        licenseActive={false}
        whatsappConnected={false}
        onPrepare={noop}
      />,
    );

    expect(screen.getByTestId("stage-environment")).toHaveTextContent("Concluído");
  });
});
