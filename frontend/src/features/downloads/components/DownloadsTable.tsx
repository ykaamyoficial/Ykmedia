import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type DownloadJobItem } from "@/features/downloads/types";
import { DownloadStatusBadge } from "@/features/downloads/components/DownloadStatusBadge";

type DownloadsTableProps = {
  jobs: DownloadJobItem[];
  loading?: boolean;
};

export function DownloadsTable({ jobs, loading = false }: DownloadsTableProps) {
  const columns = useMemo<Array<ColumnDef<DownloadJobItem>>>(
    () => [
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
        accessorKey: "file",
        header: "Arquivo",
        cell: ({ row }) => <span className="block max-w-80 truncate">{row.original.file}</span>,
      },
      {
        accessorKey: "kind",
        header: "Tipo",
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <DownloadStatusBadge status={row.original.status} />,
      },
      {
        accessorKey: "created_at",
        header: "Recebido em",
      },
      {
        accessorKey: "short_id",
        header: "ID",
        cell: ({ row }) => <span className="font-mono text-xs text-secondary">{row.original.short_id}</span>,
      },
    ],
    [],
  );

  return <YkDataTable data={jobs} columns={columns} loading={loading} />;
}
