import { YkButton } from "@/components/system/YkButton";
import { YkIcons } from "@/shared/icons";

type YkPaginationProps = {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
};

export function YkPagination({ page, pageCount, onPageChange }: YkPaginationProps) {
  return (
    <nav className="flex items-center justify-between gap-3" aria-label="Paginacao">
      <span className="text-xs text-secondary">
        Pagina {page} de {pageCount}
      </span>
      <div className="flex items-center gap-2">
        <YkButton
          type="button"
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <YkIcons.ChevronLeft className="h-4 w-4" />
          Anterior
        </YkButton>
        <YkButton
          type="button"
          variant="secondary"
          size="sm"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          Proxima
          <YkIcons.ChevronRight className="h-4 w-4" />
        </YkButton>
      </div>
    </nav>
  );
}
