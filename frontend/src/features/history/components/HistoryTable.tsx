import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type HistoryItem } from "@/features/history/types";
import { MediaName, MediaStatusBadge, MediaTypeIcon } from "@/shared/media";

type HistoryTableProps = {
  items: HistoryItem[];
  loading?: boolean;
};

export function HistoryTable({ items, loading = false }: HistoryTableProps) {
  const columns = useMemo<Array<ColumnDef<HistoryItem>>>(
    () => [
      {
        accessorKey: "date_display",
        header: "Data",
      },
      {
        accessorKey: "sender",
        header: "Remetente",
        cell: ({ row }) => <span className="font-medium">{row.original.sender}</span>,
      },
      {
        accessorKey: "origin",
        header: "Origem",
      },
      {
        accessorKey: "category",
        header: "Categoria",
      },
      {
        accessorKey: "final_name",
        header: "Nome final",
        cell: ({ row }) => (
          <div className="flex min-w-0 items-center gap-2.5">
            <MediaTypeIcon kind={row.original.kind} size="sm" />
            <MediaName name={row.original.final_name} className="max-w-80" />
          </div>
        ),
      },
      {
        accessorKey: "kind",
        header: "Tipo",
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <MediaStatusBadge status={row.original.status} />,
      },
    ],
    [],
  );

  return <YkDataTable data={items} columns={columns} loading={loading} />;
}
