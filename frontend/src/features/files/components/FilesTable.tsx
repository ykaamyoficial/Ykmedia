import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type FileLibraryItem } from "@/features/files/types";
import { fileDisplayName } from "@/features/files/utils";
import { MediaActions, MediaName, MediaStatusBadge, MediaTypeIcon } from "@/shared/media";

type FilesTableProps = {
  files: FileLibraryItem[];
  loading?: boolean;
};

export function FilesTable({ files, loading = false }: FilesTableProps) {
  const columns = useMemo<Array<ColumnDef<FileLibraryItem>>>(
    () => [
      {
        accessorKey: "final_name",
        header: "Nome",
        cell: ({ row }) => (
          <div className="flex min-w-0 items-center gap-2.5">
            <MediaTypeIcon kind={row.original.kind} size="sm" />
            <MediaName name={fileDisplayName(row.original)} className="max-w-72" />
          </div>
        ),
      },
      {
        accessorKey: "kind",
        header: "Tipo",
      },
      {
        accessorKey: "size",
        header: "Tamanho",
      },
      {
        accessorKey: "date_display",
        header: "Data",
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
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <MediaStatusBadge status={row.original.status} />,
      },
      {
        id: "actions",
        header: "Acoes",
        cell: ({ row }) => (
          <MediaActions
            path={row.original.absolute_path}
            canOpen={row.original.exists}
            fileName={fileDisplayName(row.original)}
          />
        ),
      },
    ],
    [],
  );

  return <YkDataTable data={files} columns={columns} loading={loading} />;
}
