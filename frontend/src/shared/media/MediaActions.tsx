import { YkButton } from "@/components/system/YkButton";
import { YkTooltip } from "@/components/system/YkTooltip";
import { YkIcons } from "@/shared/icons";
import { openNativePath, revealNativePath } from "@/shared/services";

type MediaActionsProps = {
  path?: string | null;
  canOpen: boolean;
  fileName: string;
  size?: "sm" | "md";
};

// Linguagem unica de acoes de arquivo salvo: Abrir + Mostrar na pasta, sempre via comando nativo.
export function MediaActions({ path, canOpen, fileName, size = "sm" }: MediaActionsProps) {
  const buttonSize = size === "sm" ? "h-8 w-8" : "h-9 w-9";

  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <YkTooltip label={canOpen ? "Abrir arquivo" : "Arquivo indisponivel"}>
        <YkButton
          type="button"
          variant="secondary"
          size="sm"
          className={`${buttonSize} px-0`}
          disabled={!canOpen || !path}
          onClick={() => void openNativePath(path ?? undefined)}
          aria-label={`Abrir arquivo ${fileName}`}
        >
          <YkIcons.Eye className="h-4 w-4" aria-hidden="true" />
        </YkButton>
      </YkTooltip>
      <YkTooltip label={path ? "Mostrar na pasta" : "Pasta indisponivel"}>
        <YkButton
          type="button"
          variant="secondary"
          size="sm"
          className={`${buttonSize} px-0`}
          disabled={!path}
          onClick={() => void revealNativePath(path ?? undefined)}
          aria-label={`Mostrar ${fileName} na pasta`}
        >
          <YkIcons.FolderOpen className="h-4 w-4" aria-hidden="true" />
        </YkButton>
      </YkTooltip>
    </div>
  );
}
