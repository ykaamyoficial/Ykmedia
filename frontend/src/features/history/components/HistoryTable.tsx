import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type HistoryItem } from "@/features/history/types";
import { HistoryStatusBadge } from "@/features/history/components/HistoryStatusBadge";

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
        cell: ({ row }) => <span className="block max-w-80 truncate">{row.original.final_name}</span>,
      },
      {
        accessorKey: "kind",
        header: "Tipo",
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <HistoryStatusBadge status={row.original.status} />,
      },
    ],
    [],
  );

  return <YkDataTable data={items} columns={columns} loading={loading} />;
}
