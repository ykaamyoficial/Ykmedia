import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkButton } from "@/components/system/YkButton";
import { YkDataTable } from "@/shared/tables";
import { YkIcons } from "@/shared/icons";
import { type FileLibraryItem } from "@/features/files/types";
import { fileDisplayName, openContainingFolder, openFile } from "@/features/files/utils";
import { FileKindBadge, FileStatusBadge } from "@/features/files/components/FileKindBadge";

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
          <span className="block max-w-72 truncate font-medium">
            {fileDisplayName(row.original)}
          </span>
        ),
      },
      {
        accessorKey: "kind",
        header: "Tipo",
        cell: ({ row }) => <FileKindBadge kind={row.original.kind} />,
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
        cell: ({ row }) => <FileStatusBadge status={row.original.status} />,
      },
      {
        id: "actions",
        header: "Acoes",
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-2">
            <YkButton
              variant="secondary"
              size="sm"
              disabled={!row.original.exists}
              onClick={() => openFile(row.original.absolute_path)}
            >
              <YkIcons.Play className="h-3.5 w-3.5" aria-hidden="true" />
              Abrir
            </YkButton>
            <YkButton
              variant="secondary"
              size="sm"
              onClick={() => openContainingFolder(row.original.absolute_path)}
            >
              <YkIcons.FolderOpen className="h-3.5 w-3.5" aria-hidden="true" />
              Abrir pasta
            </YkButton>
          </div>
        ),
      },
    ],
    [],
  );

  return <YkDataTable data={files} columns={columns} loading={loading} />;
}
