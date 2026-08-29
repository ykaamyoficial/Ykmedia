import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { normalizeMediaKind } from "@/shared/media/media-kind";
import { mediaStatusLabel, mediaStatusTone } from "@/shared/media/media-status";
import { MediaActions } from "@/shared/media/MediaActions";
import { MediaName } from "@/shared/media/MediaName";
import { MediaStatusBadge } from "@/shared/media/MediaStatusBadge";
import { MediaThumbnail } from "@/shared/media/MediaThumbnail";
import { MediaTypeIcon } from "@/shared/media/MediaTypeIcon";

describe("media-kind", () => {
  it("normalizes the backend Portuguese label and the extension-derived kind to the same value", () => {
    expect(normalizeMediaKind("Imagem")).toBe("image");
    expect(normalizeMediaKind("image")).toBe("image");
    expect(normalizeMediaKind("Arquivo")).toBe("file");
    expect(normalizeMediaKind(null)).toBe("file");
    expect(normalizeMediaKind("unknown-kind")).toBe("file");
  });
});

describe("media-status", () => {
  it("translates the real backend status to the standardized visual label", () => {
    expect(mediaStatusLabel("PENDENTE")).toBe("Aguardando");
    expect(mediaStatusLabel("PROCESSANDO")).toBe("Processando");
    expect(mediaStatusLabel("CONCLUIDO")).toBe("Salvo");
    expect(mediaStatusLabel("ERRO")).toBe("Erro");
    expect(mediaStatusTone("ERRO")).toBe("danger");
  });

  it("keeps an unknown status visible instead of hiding it", () => {
    expect(mediaStatusLabel("QUALQUER_COISA")).toBe("QUALQUER_COISA");
    expect(mediaStatusLabel(undefined)).toBe("-");
  });
});

describe("MediaTypeIcon", () => {
  it("renders a different icon per media kind", () => {
    const { container: imageBox } = render(<MediaTypeIcon kind="image" />);
    const { container: audioBox } = render(<MediaTypeIcon kind="Audio" />);

    expect(imageBox.querySelector(".lucide-image")).toBeInTheDocument();
    expect(audioBox.querySelector(".lucide-music")).toBeInTheDocument();
  });

  it("falls back to the generic file icon for an unknown kind", () => {
    const { container } = render(<MediaTypeIcon kind="totalmente-desconhecido" />);
    expect(container.querySelector(".lucide-file")).toBeInTheDocument();
  });
});

describe("MediaThumbnail", () => {
  it("renders the icon fallback when there is no thumbnail URL", () => {
    const { container } = render(<MediaThumbnail kind="video" alt="video.mp4" />);
    expect(container.querySelector(".lucide-video")).toBeInTheDocument();
  });

  it("falls back to the type icon when the thumbnail fails to load", () => {
    const { container } = render(
      <MediaThumbnail kind="image" thumbnailUrl="https://example.com/broken.jpg" alt="foto.jpg" />,
    );

    expect(container.querySelector("img")).toBeInTheDocument();
    fireEvent.error(screen.getByAltText("foto.jpg"));
    expect(container.querySelector("img")).not.toBeInTheDocument();
    expect(container.querySelector(".lucide-image")).toBeInTheDocument();
  });
});

describe("MediaName", () => {
  it("truncates a long name while keeping the extension visible", () => {
    const longName = "relatorio-completo-da-reuniao-de-producao-de-sonoplastia-2026.pdf";
    render(<MediaName name={longName} className="max-w-40" />);

    expect(screen.getByText(".pdf")).toBeInTheDocument();
    expect(screen.getByRole("tooltip", { hidden: true })).toHaveTextContent(longName);
  });

  it("exposes the original name in the tooltip when the file was renamed", () => {
    render(<MediaName name="final.mp3" originalName="audio (1).mp3" />);
    expect(screen.getByRole("tooltip", { hidden: true })).toHaveTextContent("final.mp3 (original: audio (1).mp3)");
  });
});

describe("MediaActions", () => {
  it("exposes accessible, tooltip-backed open actions and opens the file via the native fallback", () => {
    const open = vi.fn();
    vi.stubGlobal("open", open);

    render(<MediaActions path={"C:\\media\\louvor.mp3"} canOpen fileName="louvor.mp3" />);

    const openButton = screen.getByLabelText("Abrir arquivo louvor.mp3");
    const revealButton = screen.getByLabelText("Mostrar louvor.mp3 na pasta");
    expect(openButton).toBeEnabled();
    expect(revealButton).toBeEnabled();

    fireEvent.click(openButton);
    expect(open).toHaveBeenCalledWith("file:///C:/media/louvor.mp3", "_blank", "noopener,noreferrer");

    vi.unstubAllGlobals();
  });

  it("disables the open action when the file cannot be opened yet", () => {
    render(<MediaActions path={"C:\\media\\job.mp3"} canOpen={false} fileName="job.mp3" />);

    expect(screen.getByLabelText("Abrir arquivo job.mp3")).toBeDisabled();
    expect(screen.getByLabelText("Mostrar job.mp3 na pasta")).toBeEnabled();
  });

  it("disables both actions when there is no known path", () => {
    render(<MediaActions path={undefined} canOpen fileName="job.mp3" />);

    expect(screen.getByLabelText("Abrir arquivo job.mp3")).toBeDisabled();
    expect(screen.getByLabelText("Mostrar job.mp3 na pasta")).toBeDisabled();
  });
});

describe("MediaStatusBadge", () => {
  it("renders the standardized label for a real backend status", () => {
    render(<MediaStatusBadge status="PROCESSANDO" />);
    expect(screen.getByText("Processando")).toBeInTheDocument();
  });
});
