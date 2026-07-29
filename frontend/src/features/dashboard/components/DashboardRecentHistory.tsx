import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type DashboardHistoryItem } from "@/features/dashboard/types";

const columns: Array<ColumnDef<DashboardHistoryItem>> = [
  {
    accessorKey: "date",
    header: "Data",
  },
  {
    accessorKey: "sender",
    header: "Remetente",
  },
  {
    accessorKey: "category",
    header: "Categoria",
    cell: ({ row }) => row.original.category ?? "Sem categoria",
  },
  {
    accessorKey: "final_name",
    header: "Arquivo",
    cell: ({ row }) => row.original.final_name ?? "Sem nome",
  },
  {
    accessorKey: "status",
    header: "Status",
  },
];

export function DashboardRecentHistory({
  history,
  loading = false,
}: {
  history: DashboardHistoryItem[];
  loading?: boolean;
}) {
  return <YkDataTable data={history} columns={columns} loading={loading} />;
}
