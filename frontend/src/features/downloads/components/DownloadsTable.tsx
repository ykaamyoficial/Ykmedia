import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type DownloadJobItem } from "@/features/downloads/types";
import { MediaName, MediaStatusBadge, MediaTypeIcon } from "@/shared/media";

type DownloadsTableProps = {
  jobs: DownloadJobItem[];
  loading?: boolean;
};

export function DownloadsTable({ jobs, loading = false }: DownloadsTableProps) {
  const columns = useMemo<Array<ColumnDef<DownloadJobItem>>>(
    () => [
      {
        accessorKey: "file",
        header: "Arquivo",
        cell: ({ row }) => (
          <div className="flex min-w-0 items-center gap-2.5">
            <MediaTypeIcon kind={row.original.kind} size="sm" />
            <MediaName name={row.original.file} className="max-w-80" />
          </div>
        ),
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
        accessorKey: "kind",
        header: "Tipo",
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <MediaStatusBadge status={row.original.status} />,
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
